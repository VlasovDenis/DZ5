from pathlib import Path
from time import perf_counter
import os
import sys

from dotenv import load_dotenv
from pydantic import BaseModel, Field


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


# ============================================================
# Environment
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"


from langchain_core.messages import HumanMessage, SystemMessage

from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from ai_smm.llm import create_llm


# ============================================================
# Structured output for Single Prompt baseline
# ============================================================


class SinglePromptPlanItem(BaseModel):
    id: int
    day: str
    topic: str
    format: str
    content_goal: str
    key_message: str
    cta: str


class SinglePromptPost(BaseModel):
    post_id: int
    topic: str
    text: str
    hashtags: list[str] = Field(
        min_length=2,
        max_length=5,
    )


class SinglePromptResult(BaseModel):
    audience_analysis: str

    content_pillars: list[str]

    content_plan: list[SinglePromptPlanItem] = Field(
        min_length=7,
        max_length=7,
    )

    posts: list[SinglePromptPost] = Field(
        min_length=3,
        max_length=3,
    )

    self_review: str


# ============================================================
# Prompt
# ============================================================

SYSTEM_PROMPT = """
Ты — единый AI SMM-специалист.

За ОДИН вызов ты должен выполнить работу,
которую в multi-agent варианте выполняют:

1. Strategist
2. Copywriter
3. Editor
4. Publisher

Твоя задача:

- проанализировать целевую аудиторию;
- определить контент-направления;
- составить контент-план на 7 дней;
- написать 3 готовых поста;
- самостоятельно проверить их перед финальным ответом;
- адаптировать оформление для VK;
- добавить уместные хештеги.

КРИТИЧЕСКИЕ ПРАВИЛА:

Используй только подтверждённые факты о продукте.

Не придумывай:
- интеграции;
- уведомления;
- автоматическое отслеживание сроков;
- отчёты;
- конкретные проценты экономии;
- конкретные показатели эффективности;
- клиентов;
- кейсы;
- сроки обработки;
- функции, которых нет во входных данных.

Если конкретная функция продукта не подтверждена,
описывай бизнес-проблему или общий эффект автоматизации,
но не представляй неподтверждённую возможность как факт.

Перед выдачей результата самостоятельно проверь:

1. Нет ли неподтверждённых фактов.
2. Нет ли неподтверждённых цифр.
3. Соответствуют ли посты контент-плану.
4. Подходят ли они целевой аудитории.
5. Подходят ли они для VK.
6. Есть ли CTA.
7. Не добавлены ли функции продукта,
   которых нет во входных данных.

Верни только результат согласно JSON-схеме.
"""


def main():
    # ========================================================
    # Langfuse
    # ========================================================

    langfuse = get_client()

    print("===== LANGFUSE AUTH =====")

    authenticated = langfuse.auth_check()

    print(
        "authenticated:",
        authenticated,
    )

    if not authenticated:
        raise RuntimeError(
            "Langfuse authentication failed"
        )

    # ========================================================
    # Same business task as Multi-Agent run
    # ========================================================

    task = (
        "Сформировать контент-план на неделю для "
        "B2B SaaS-платформы автоматизации обработки "
        "и анализа договоров и написать готовые "
        "тексты для трёх постов."
    )

    niche = (
        "B2B SaaS-платформа для автоматизации "
        "обработки и анализа договоров"
    )

    target_audience = (
        "Юристы, руководители юридических отделов, "
        "специалисты по закупкам, финансовые директора "
        "и операционные руководители."
    )

    social_network = "VK"

    verified_product_facts = [
        (
            "Продукт является B2B SaaS-платформой "
            "для автоматизации обработки и анализа договоров."
        ),
    ]

    verified_facts_text = "\n".join(
        f"- {fact}"
        for fact in verified_product_facts
    )

    user_prompt = f"""
ИСХОДНАЯ ЗАДАЧА:

{task}

БИЗНЕС-НИША:

{niche}

ЦЕЛЕВАЯ АУДИТОРИЯ:

{target_audience}

СОЦИАЛЬНАЯ СЕТЬ:

{social_network}

ПОДТВЕРЖДЁННЫЕ ФАКТЫ О ПРОДУКТЕ:

{verified_facts_text}

ТРЕБУЕТСЯ:

1. Анализ аудитории.
2. Контент-направления.
3. Контент-план ровно на 7 дней.
4. Ровно 3 готовых поста из этого плана.
5. Каждый пост должен содержать:
   - понятный hook;
   - основной текст;
   - CTA;
   - 2–5 hashtags.
6. Выполни внутреннюю самопроверку перед финальным ответом.
7. В self_review кратко укажи,
   что именно было проверено.

Не добавляй неподтверждённые функции продукта.
"""

    # ========================================================
    # Model
    # ========================================================

    llm = create_llm(
        temperature=0.4,
        num_predict=5000,
    )

    structured_llm = llm.with_structured_output(
        SinglePromptResult,
        method="json_schema",
        include_raw=True,
    )

    handler = CallbackHandler()

    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        ),
        HumanMessage(
            content=user_prompt
        ),
    ]

    # ========================================================
    # Single Prompt trace
    # ========================================================

    started = perf_counter()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="ai-smm-single-prompt-run",
        input={
            "task": task,
            "niche": niche,
            "social_network": social_network,
        },
    ) as root_span:

        with propagate_attributes(
            session_id="dz5-ai-smm-single-prompt",
            tags=[
                "otus",
                "dz5",
                "single-prompt",
                "ollama",
                "qwen3-4b-instruct",
            ],
        ):

            response = structured_llm.invoke(
                messages,
                config={
                    "callbacks": [
                        handler
                    ],
                    "run_name": (
                        "single-prompt-llm"
                    ),
                },
            )

        elapsed = perf_counter() - started

        if response["parsing_error"] is not None:
            raise RuntimeError(
                "Single Prompt structured output error: "
                f"{response['parsing_error']}"
            )

        parsed: SinglePromptResult = response["parsed"]
        raw = response["raw"]

        if parsed is None:
            raise RuntimeError(
                "Single Prompt returned empty parsed result"
            )

        root_span.update(
            output={
                "posts": len(parsed.posts),
                "plan_items": len(
                    parsed.content_plan
                ),
                "llm_calls": 1,
                "elapsed_seconds": elapsed,
            }
        )

    # ========================================================
    # Console output
    # ========================================================

    print()
    print("===== SINGLE PROMPT RESULT =====")

    print()
    print("AUDIENCE ANALYSIS:")
    print(parsed.audience_analysis)

    print()
    print("CONTENT PILLARS:")

    for pillar in parsed.content_pillars:
        print(
            "-",
            pillar,
        )

    print()
    print("===== WEEKLY PLAN =====")

    for item in parsed.content_plan:
        print(
            f"{item.id}. "
            f"{item.day}: "
            f"{item.topic} "
            f"[{item.format}]"
        )

    print()
    print("===== FINAL POSTS =====")

    for post in parsed.posts:
        print()
        print(
            f"----- POST {post.post_id}: "
            f"{post.topic} -----"
        )
        print()
        print(post.text)
        print()
        print(
            "HASHTAGS:",
            " ".join(post.hashtags),
        )

    print()
    print("===== SELF REVIEW =====")
    print(parsed.self_review)

    print()
    print("===== USAGE METADATA =====")
    print(raw.usage_metadata)

    print()
    print("===== RESPONSE METADATA =====")
    print(raw.response_metadata)

    print()
    print("===== PERFORMANCE =====")
    print(
        f"end_to_end_latency: "
        f"{elapsed:.2f}s"
    )
    print("llm_calls: 1")

    # ========================================================
    # Telemetry
    # ========================================================

    langfuse.flush()

    print()
    print("===== LANGFUSE =====")
    print(
        "Single Prompt trace sent successfully."
    )


if __name__ == "__main__":
    main()