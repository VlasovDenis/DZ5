import re
import unicodedata

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.runnables import RunnableConfig

from ai_smm.config import settings
from ai_smm.llm import create_llm
from ai_smm.prompts.editor import EDITOR_SYSTEM_PROMPT
from ai_smm.schemas import EditorResult
from ai_smm.state import SMMState


def normalize_text_for_validation(
    text: str,
) -> str:
    """
    Нормализует текст только для deterministic quote validation.

    Смысл текста не меняется:
    - Unicode приводится к единой форме;
    - несколько пробелов / переносов строк
      превращаются в один пробел.
    """

    normalized = unicodedata.normalize(
        "NFKC",
        text,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


def editor_node(
    state: SMMState,
    config: RunnableConfig | None = None,
) -> dict:
    strategist_result = state.get(
        "strategist_result"
    )

    copywriter_result = state.get(
        "copywriter_result"
    )

    if strategist_result is None:
        raise ValueError(
            "Editor requires strategist_result"
        )

    if copywriter_result is None:
        raise ValueError(
            "Editor requires copywriter_result"
        )

    # ---------------------------------------------------------
    # LLM
    # ---------------------------------------------------------

    llm = create_llm(
        temperature=settings.editor_temperature,
        num_predict=2000,
    )

    structured_llm = llm.with_structured_output(
        EditorResult,
        method="json_schema",
        include_raw=True,
    )

    # ---------------------------------------------------------
    # Только актуальные данные
    # ---------------------------------------------------------

    strategist_json = (
        strategist_result.model_dump_json(
            indent=2,
            ensure_ascii=False,
        )
    )

    copywriter_json = (
        copywriter_result.model_dump_json(
            indent=2,
            ensure_ascii=False,
        )
    )

    verified_facts = "\n".join(
        f"- {fact}"
        for fact in state[
            "verified_product_facts"
        ]
    )

    user_prompt = f"""
Исходная задача пользователя:

{state["task"]}

Бизнес-ниша:
{state["niche"]}

Целевая аудитория:
{state["target_audience"]}

Социальная сеть:
{state["social_network"]}

ПОДТВЕРЖДЁННЫЕ ФАКТЫ О ПРОДУКТЕ:

{verified_facts}

Конкретную функцию продукта можно считать
подтверждённой только если она явно следует
из списка выше.

Проверь ТОЛЬКО текущую версию Copywriter.

Не учитывай предыдущие версии постов.

Особенно внимательно проверь:
- неподтверждённые функции продукта;
- неподтверждённые цифры;
- гарантии;
- вымышленные кейсы;
- несоответствие контент-плану;
- проблемы CTA;
- стиль;
- ясность.
"""

    # ---------------------------------------------------------
    # ВАЖНО:
    # state["messages"] сюда не передаём.
    #
    # Editor получает только актуальный рабочий контекст.
    # ---------------------------------------------------------

    messages = [
        SystemMessage(
            content=EDITOR_SYSTEM_PROMPT
        ),
        HumanMessage(
            content=(
                "[Исходный запрос пользователя]\n"
                + state["task"]
            )
        ),
        AIMessage(
            content=(
                "[Актуальный Strategist]\n"
                + strategist_json
            )
        ),
        AIMessage(
            content=(
                "[ТЕКУЩАЯ версия Copywriter]\n"
                + copywriter_json
            )
        ),
        HumanMessage(
            content=user_prompt
        ),
    ]

    # ---------------------------------------------------------
    # Deterministic validation context
    # ---------------------------------------------------------

    posts_by_id = {
        post.post_id: post
        for post in copywriter_result.posts
    }

    allowed_post_ids = sorted(
        posts_by_id.keys()
    )

    def validate_editor_result(
        candidate: EditorResult,
    ) -> str | None:
        """
        Проверяет deterministic-контракт Editor.

        Возвращает:
        - None, если результат валиден;
        - описание ошибки, если требуется
          corrective retry.
        """

        # -----------------------------------------------------
        # Decision / issues consistency
        # -----------------------------------------------------

        if (
            candidate.decision == "APPROVED"
            and candidate.issues
        ):
            return (
                "Editor returned decision=APPROVED "
                "but issues list is not empty"
            )

        if (
            candidate.decision == "REVISE"
            and not candidate.issues
        ):
            return (
                "Editor returned decision=REVISE "
                "but issues list is empty"
            )

        # -----------------------------------------------------
        # Проверка каждого issue
        # -----------------------------------------------------

        for issue in candidate.issues:
            post = posts_by_id.get(
                issue.post_id
            )

            if post is None:
                return (
                    "Editor referenced unknown "
                    f"post_id={issue.post_id}. "
                    f"Allowed post IDs: "
                    f"{allowed_post_ids}"
                )

            current_text = "\n".join(
                [
                    post.topic,
                    post.hook,
                    post.body,
                    post.cta,
                ]
            )

            quote = issue.quote.strip()

            normalized_quote = (
                normalize_text_for_validation(
                    quote
                )
            )

            if not normalized_quote:
                return (
                    "Editor returned empty quote "
                    f"for post_id={issue.post_id}"
                )

            normalized_current_text = (
                normalize_text_for_validation(
                    current_text
                )
            )

            if (
                normalized_quote
                not in normalized_current_text
            ):
                return (
                    "Editor referenced text that is "
                    "not present in current post "
                    f"{issue.post_id}: "
                    f"{quote!r}"
                )

        return None

    # ---------------------------------------------------------
    # LLM + one corrective retry
    #
    # Маленькая локальная модель иногда возвращает
    # правдоподобное замечание, но:
    #
    # - issue.quote является пересказом;
    # - post_id неправильный;
    # - decision и issues противоречат друг другу;
    # - structured output повреждён.
    #
    # Deterministic validation не ослабляем.
    # Даём модели только одну попытку исправить ответ.
    # ---------------------------------------------------------

    parsed: EditorResult | None = None
    last_error: str | None = None

    for attempt in range(2):
        call_messages = list(
            messages
        )

        if attempt == 1:
            call_messages.append(
                HumanMessage(
                    content=f"""
ПРЕДЫДУЩИЙ ОТВЕТ EDITOR НАРУШИЛ
СТРУКТУРНЫЙ КОНТРАКТ.

Причина:

{last_error}

Исправь ТОЛЬКО результат проверки.

КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:

1. Проверяй только ТЕКУЩУЮ версию Copywriter.

2. Разрешённые post_id:

{allowed_post_ids}

3. Для каждого issue поле quote должно быть
ТОЧНОЙ цитатой из текущего поста.

4. quote должен дословно присутствовать
в одном из следующих полей соответствующего поста:
- topic;
- hook;
- body;
- cta.

5. Не пересказывай текст своими словами.

6. Не объединяй несколько разных фрагментов
в одну искусственную цитату.

7. Не изменяй слова внутри quote.

8. Если проблема относится к нескольким фрагментам,
создай отдельный issue для каждой точной цитаты.

9. Если реальных проблем нет, верни:

decision = "APPROVED"

и пустой список issues.

10. Если проблемы есть, верни:

decision = "REVISE"

и только валидные issues
с точными цитатами.

11. Если decision = "APPROVED",
issues ОБЯЗАТЕЛЬНО должен быть пустым.

12. Если decision = "REVISE",
issues ОБЯЗАТЕЛЬНО должен содержать
хотя бы одно замечание.

13. quote не может быть пустой строкой.

Верни результат строго согласно JSON-схеме.
"""
                )
            )

        # -----------------------------------------------------
        # Langfuse / LangChain run name
        # -----------------------------------------------------

        llm_config = dict(
            config or {}
        )

        llm_config["run_name"] = (
            "editor-llm"
            if attempt == 0
            else "editor-llm-retry"
        )

        # -----------------------------------------------------
        # LLM invocation
        # -----------------------------------------------------

        result = structured_llm.invoke(
            call_messages,
            config=llm_config,
        )

        # -----------------------------------------------------
        # Structured output parsing
        # -----------------------------------------------------

        if (
            result["parsing_error"]
            is not None
        ):
            last_error = (
                "structured output error: "
                f"{result['parsing_error']}"
            )
            continue

        candidate: EditorResult | None = (
            result["parsed"]
        )

        if candidate is None:
            last_error = (
                "Editor returned empty parsed result"
            )
            continue

        # -----------------------------------------------------
        # Deterministic validation
        # -----------------------------------------------------

        validation_error = (
            validate_editor_result(
                candidate
            )
        )

        if validation_error is not None:
            last_error = (
                validation_error
            )
            continue

        # -----------------------------------------------------
        # Результат полностью валиден
        # -----------------------------------------------------

        parsed = candidate
        break

    # ---------------------------------------------------------
    # Обе попытки нарушили контракт
    # ---------------------------------------------------------

    if parsed is None:
        raise ValueError(
            "Editor failed deterministic validation "
            "after corrective retry: "
            f"{last_error}"
        )

    # ---------------------------------------------------------
    # Result
    # ---------------------------------------------------------

    approved = (
        parsed.decision
        == "APPROVED"
    )

    return {
        "editor_result": parsed,

        "editor_approved": approved,

        "messages": [
            AIMessage(
                content=(
                    "[Editor]\n"
                    + parsed.model_dump_json(
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            )
        ],
    }