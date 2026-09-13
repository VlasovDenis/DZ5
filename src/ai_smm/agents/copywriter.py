from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai_smm.config import settings
from ai_smm.llm import create_llm
from ai_smm.prompts.copywriter import COPYWRITER_SYSTEM_PROMPT
from ai_smm.schemas import CopywriterResult
from ai_smm.state import SMMState
from langchain_core.runnables import RunnableConfig

def copywriter_node(
    state: SMMState,
    config: RunnableConfig | None = None,
) -> dict:
    strategist_result = state.get("strategist_result")

    if strategist_result is None:
        raise ValueError(
            "Copywriter requires strategist_result"
        )

    selected_post_ids = state["selected_post_ids"]

    selected_items = [
        item
        for item in strategist_result.plan
        if item.id in selected_post_ids
    ]

    if len(selected_items) != len(selected_post_ids):
        raise ValueError(
            "Some selected_post_ids are missing "
            "from strategist content plan"
        )

    llm = create_llm(
        temperature=settings.copywriter_temperature,
        num_predict=3000,
    )

    structured_llm = llm.with_structured_output(
        CopywriterResult,
        method="json_schema",
        include_raw=True,
    )

    # ---------------------------------------------------------
    # Подтверждённые факты о продукте
    # ---------------------------------------------------------

    verified_facts = "\n".join(
        f"- {fact}"
        for fact in state["verified_product_facts"]
    )

    # ---------------------------------------------------------
    # Актуальный результат Strategist
    # ---------------------------------------------------------

    strategist_json = strategist_result.model_dump_json(
        indent=2,
        ensure_ascii=False,
    )

    selected_json = "\n\n".join(
        item.model_dump_json(
            indent=2,
            ensure_ascii=False,
        )
        for item in selected_items
    )

    # ---------------------------------------------------------
    # Проверяем, является ли вызов повторной доработкой
    # ---------------------------------------------------------

    editor_result = state.get("editor_result")
    previous_draft = state.get("copywriter_result")

    is_revision = (
        editor_result is not None
        and editor_result.decision == "REVISE"
        and previous_draft is not None
    )

    previous_json = None
    editor_json = None

    if is_revision:
        previous_json = previous_draft.model_dump_json(
            indent=2,
            ensure_ascii=False,
        )

        editor_json = editor_result.model_dump_json(
            indent=2,
            ensure_ascii=False,
        )

    # ---------------------------------------------------------
    # Основное задание
    # ---------------------------------------------------------

    user_prompt = f"""
Бизнес-ниша:
{state["niche"]}

Целевая аудитория:
{state["target_audience"]}

Социальная сеть:
{state["social_network"]}

ПОДТВЕРЖДЁННЫЕ ФАКТЫ О ПРОДУКТЕ:

{verified_facts}

ВАЖНО:
любое конкретное свойство продукта, которого нет
в списке подтверждённых фактов, нельзя представлять
как существующую функцию продукта.

Выбранные ID постов:
{selected_post_ids}

Напиши тексты ТОЛЬКО для следующих элементов
контент-плана:

{selected_json}

Верни ровно {len(selected_post_ids)} поста.
"""

    # ---------------------------------------------------------
    # ВАЖНО:
    # НЕ передаём state["messages"] целиком.
    #
    # Формируем только актуальный рабочий контекст.
    # ---------------------------------------------------------

    messages = [
        SystemMessage(
            content=COPYWRITER_SYSTEM_PROMPT
        ),
        HumanMessage(
            content=(
                "[Исходный запрос пользователя]\n"
                + state["task"]
            )
        ),
        AIMessage(
            content=(
                "[Актуальный результат Strategist]\n"
                + strategist_json
            )
        ),
    ]

    # ---------------------------------------------------------
    # Если это revision — передаём ТОЛЬКО:
    # текущий draft + последнее ревью Editor
    # ---------------------------------------------------------

    if is_revision:
        messages.extend(
            [
                AIMessage(
                    content=(
                        "[Текущий черновик Copywriter]\n"
                        + previous_json
                    )
                ),
                AIMessage(
                    content=(
                        "[Последнее ревью Editor]\n"
                        + editor_json
                    )
                ),
                HumanMessage(
                    content=f"""
Это повторная доработка.

Номер доработки:
{state["revision_count"]}

Исправь замечания Editor в ТЕКУЩЕМ черновике.

Проверь при этом весь пост:
- topic;
- hook;
- body;
- cta.

Если неподтверждённая функция встречается
в нескольких местах поста, исправь все её появления.

Не возвращай удалённые ранее утверждения.
"""
                ),
            ]
        )

    messages.append(
        HumanMessage(content=user_prompt)
    )

    # ---------------------------------------------------------
    # LLM + controlled corrective retry
    #
    # Небольшая локальная модель иногда возвращает
    # структурно валидный JSON, но нарушает контракт:
    # например post_id=-1 вместо одного из выбранных ID.
    #
    # В таком случае не ослабляем deterministic validation,
    # а даём модели ОДНУ попытку исправить структуру.
    # ---------------------------------------------------------

    expected_ids = sorted(
        selected_post_ids
    )

    parsed: CopywriterResult | None = None
    last_error: str | None = None

    for attempt in range(2):
        call_messages = list(messages)

        if attempt == 1:
            call_messages.append(
                HumanMessage(
                    content=f"""
ПРЕДЫДУЩИЙ ОТВЕТ НАРУШИЛ СТРУКТУРНЫЙ КОНТРАКТ.

Исправь ответ.

Обязательные требования:

- верни РОВНО {len(selected_post_ids)} поста;
- используй ТОЛЬКО следующие post_id:
  {expected_ids}
- каждый post_id должен встретиться ровно один раз;
- запрещены любые другие значения post_id;
- не используй -1, 0 или новые ID;
- сохрани содержание задания;
- верни результат строго согласно JSON-схеме.

Ожидаемый набор post_id:
{expected_ids}
"""
                )
            )

        llm_config = dict(
            config or {}
        )

        llm_config["run_name"] = (
            "copywriter-llm"
            if attempt == 0
            else "copywriter-llm-retry"
        )

        result = structured_llm.invoke(
            call_messages,
            config=llm_config,
        )

        # -----------------------------------------------------
        # Structured output parsing
        # -----------------------------------------------------

        if result["parsing_error"] is not None:
            last_error = (
                "structured output error: "
                f"{result['parsing_error']}"
            )
            continue

        candidate: CopywriterResult | None = (
            result["parsed"]
        )

        if candidate is None:
            last_error = (
                "empty parsed result"
            )
            continue

        # -----------------------------------------------------
        # Deterministic validation
        # -----------------------------------------------------

        if (
            len(candidate.posts)
            != len(selected_post_ids)
        ):
            last_error = (
                "wrong number of posts: "
                f"{len(candidate.posts)}, "
                f"expected "
                f"{len(selected_post_ids)}"
            )
            continue

        returned_ids = sorted(
            post.post_id
            for post in candidate.posts
        )

        if returned_ids != expected_ids:
            last_error = (
                "wrong post IDs: "
                f"{returned_ids}, "
                f"expected {expected_ids}"
            )
            continue

        # Всё валидно.
        parsed = candidate
        break

    # ---------------------------------------------------------
    # Обе попытки нарушили контракт
    # ---------------------------------------------------------

    if parsed is None:
        raise ValueError(
            "Copywriter failed deterministic validation "
            "after corrective retry: "
            f"{last_error}"
        )
    
    # ---------------------------------------------------------
    # State update
    # ---------------------------------------------------------

    return {
        "copywriter_result": parsed,
        "messages": [
            AIMessage(
                content=(
                    "[Copywriter]\n"
                    + parsed.model_dump_json(
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            )
        ],
    }