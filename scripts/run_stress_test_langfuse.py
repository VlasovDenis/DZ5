from pathlib import Path
import os
import sys

from dotenv import load_dotenv


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


from langchain_core.messages import HumanMessage

from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from ai_smm.graph import smm_graph


def main():
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
    # Stress-test input
    # ========================================================

    task = (
        "STRESS-TEST: сформировать контент-план на неделю "
        "и написать три готовых поста для TikTok для компании, "
        "которая предлагает промышленное оборудование "
        "для проектов атомной энергетики. "
        "Контент должен оставаться профессиональным и корректным "
        "для B2B-аудитории, несмотря на развлекательный формат TikTok. "
        "Не использовать сенсационность и дешёвый clickbait. "
        "Не придумывать технические характеристики, клиентов, "
        "сертификации, разрешения, показатели безопасности, "
        "срок службы, эффективность, экономические показатели "
        "или соответствие конкретным нормативам, если этого нет "
        "в подтверждённых фактах."
    )

    initial_state = {
        "messages": [
            HumanMessage(content=task)
        ],

        "task": task,

        "niche": (
            "Промышленное B2B-оборудование "
            "для проектов атомной энергетики"
        ),

        "target_audience": (
            "Инженеры, технические специалисты, "
            "руководители инженерных подразделений, "
            "специалисты по закупкам и руководители проектов "
            "в энергетических и промышленных организациях."
        ),

        "social_network": "TikTok",

        # Намеренно очень ограниченный набор фактов.
        # Всё остальное модель должна считать неподтверждённым.
        "verified_product_facts": [
            (
                "Компания предлагает промышленное оборудование "
                "для проектов атомной энергетики."
            ),
            (
                "Контент предназначен для профессиональной "
                "B2B-аудитории."
            ),
        ],

        "selected_post_ids": [
            1,
            3,
            4,
        ],

        "revision_count": 0,
        "max_revisions": 3,

        "editor_approved": False,
        "forced_publish": False,
    }

    # ========================================================
    # Langfuse
    # ========================================================

    langfuse_handler = CallbackHandler()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="ai-smm-stress-test-run",
        input={
            "task": task,
            "niche": initial_state["niche"],
            "social_network": initial_state[
                "social_network"
            ],
        },
    ) as root_span:

        with propagate_attributes(
            session_id="dz5-ai-smm-stress-test",
            tags=[
                "otus",
                "dz5",
                "stress-test",
                "langgraph",
                "ollama",
                "qwen3-4b-instruct",
            ],
        ):

            result = smm_graph.invoke(
                initial_state,
                config={
                    "callbacks": [
                        langfuse_handler
                    ],
                    "run_name": (
                        "ai-smm-stress-test-langgraph"
                    ),
                    "recursion_limit": 25,
                },
            )

        root_span.update(
            output={
                "revision_count": (
                    result["revision_count"]
                ),
                "editor_approved": (
                    result["editor_approved"]
                ),
                "forced_publish": (
                    result["forced_publish"]
                ),
                "editor_decision": (
                    result[
                        "editor_result"
                    ].decision
                ),
                "published_posts": len(
                    result[
                        "publisher_result"
                    ].posts
                ),
            }
        )

    # ========================================================
    # Console result
    # ========================================================

    print()
    print("===== STRESS TEST RESULT =====")

    print(
        "revision_count:",
        result["revision_count"],
    )

    print(
        "editor_approved:",
        result["editor_approved"],
    )

    print(
        "forced_publish:",
        result["forced_publish"],
    )

    print(
        "editor_decision:",
        result["editor_result"].decision,
    )

    print()
    print("===== STRATEGIST RESULT =====")

    print()
    print("AUDIENCE ANALYSIS:")
    print(
        result[
            "strategist_result"
        ].audience_analysis
    )

    print()
    print("CONTENT PILLARS:")

    for pillar in (
        result[
            "strategist_result"
        ].content_pillars
    ):
        print(
            "-",
            pillar,
        )

    print()
    print("===== WEEKLY PLAN =====")

    for item in (
        result[
            "strategist_result"
        ].plan
    ):
        print()
        print(
            f"{item.id}. "
            f"{item.day}: "
            f"{item.topic}"
        )
        print(
            "FORMAT:",
            item.format,
        )
        print(
            "GOAL:",
            item.content_goal,
        )
        print(
            "MESSAGE:",
            item.key_message,
        )
        print(
            "CTA:",
            item.cta,
        )

    print()
    print("===== FINAL EDITOR RESULT =====")

    print(
        "DECISION:",
        result[
            "editor_result"
        ].decision,
    )

    print(
        "SUMMARY:",
        result[
            "editor_result"
        ].summary,
    )

    if result[
        "editor_result"
    ].issues:

        print()
        print("ISSUES:")

        for issue in (
            result[
                "editor_result"
            ].issues
        ):
            print()
            print(
                f"POST {issue.post_id} "
                f"[{issue.category}]"
            )
            print(
                "QUOTE:",
                issue.quote,
            )
            print(
                "PROBLEM:",
                issue.problem,
            )
            print(
                "RECOMMENDATION:",
                issue.recommendation,
            )

    print()
    print("===== FINAL POSTS =====")

    for post in (
        result[
            "publisher_result"
        ].posts
    ):
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

    # ========================================================
    # Force telemetry delivery
    # ========================================================

    langfuse.flush()

    print()
    print("===== LANGFUSE =====")
    print(
        "Stress-test trace sent successfully."
    )


if __name__ == "__main__":
    main()