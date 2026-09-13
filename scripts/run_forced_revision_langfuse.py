from pathlib import Path
import os
import sys

from dotenv import load_dotenv


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_DIR),
)


# ============================================================
# Environment
# ============================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)

os.environ["NO_PROXY"] = (
    "localhost,127.0.0.1"
)

os.environ["no_proxy"] = (
    "localhost,127.0.0.1"
)


from langchain_core.messages import HumanMessage

from langfuse import (
    get_client,
    propagate_attributes,
)
from langfuse.langchain import CallbackHandler

from ai_smm.forced_revision_graph import (
    forced_revision_graph,
)


def main():
    langfuse = get_client()

    print(
        "===== LANGFUSE AUTH ====="
    )

    authenticated = (
        langfuse.auth_check()
    )

    print(
        "authenticated:",
        authenticated,
    )

    if not authenticated:
        raise RuntimeError(
            "Langfuse authentication failed"
        )

    # ========================================================
    # Task
    # ========================================================

    task = (
        "Сформировать контент-план на неделю для "
        "B2B SaaS-платформы автоматизации обработки "
        "и анализа договоров и написать готовые "
        "тексты для трёх постов."
    )

    initial_state = {
        "messages": [
            HumanMessage(
                content=task
            )
        ],

        "task": task,

        "niche": (
            "B2B SaaS-платформа для автоматизации "
            "обработки и анализа договоров"
        ),

        "target_audience": (
            "Юристы, руководители юридических отделов, "
            "специалисты по закупкам, финансовые директора "
            "и операционные руководители."
        ),

        "social_network": "VK",

        "verified_product_facts": [
            (
                "Продукт является B2B SaaS-платформой "
                "для автоматизации обработки "
                "и анализа договоров."
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

    handler = CallbackHandler()

    # ========================================================
    # Trace
    # ========================================================

    with langfuse.start_as_current_observation(
        as_type="span",
        name="ai-smm-forced-revision-run",
        input={
            "experiment": (
                "controlled-revision"
            ),
            "task": task,
        },
    ) as root_span:

        with propagate_attributes(
            session_id=(
                "dz5-ai-smm-forced-revision"
            ),
            tags=[
                "otus",
                "dz5",
                "langgraph",
                "multi-agent",
                "forced-revision",
                "ollama",
                "qwen3-4b-instruct",
            ],
        ):

            result = (
                forced_revision_graph.invoke(
                    initial_state,
                    config={
                        "callbacks": [
                            handler
                        ],
                        "run_name": (
                            "ai-smm-forced-"
                            "revision-langgraph"
                        ),
                        "recursion_limit": 25,
                    },
                )
            )

        root_span.update(
            output={
                "revision_count": (
                    result[
                        "revision_count"
                    ]
                ),
                "editor_approved": (
                    result[
                        "editor_approved"
                    ]
                ),
                "forced_publish": (
                    result[
                        "forced_publish"
                    ]
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
    # Console
    # ========================================================

    print()
    print(
        "===== FORCED REVISION RESULT ====="
    )

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
        result[
            "editor_result"
        ].decision,
    )

    print()
    print(
        "===== MESSAGE HISTORY ====="
    )

    for index, message in enumerate(
        result["messages"],
        start=1,
    ):
        preview = str(
            message.content
        ).replace(
            "\n",
            " ",
        )

        print(
            f"{index}. "
            f"{message.__class__.__name__}: "
            f"{preview[:90]}"
        )

    print()
    print(
        "===== FINAL POSTS ====="
    )

    for post in (
        result[
            "publisher_result"
        ].posts
    ):
        print()
        print(
            f"POST {post.post_id}: "
            f"{post.topic}"
        )

        print(
            post.text
        )

        print(
            "HASHTAGS:",
            " ".join(
                post.hashtags
            ),
        )

    # ========================================================
    # Validation
    # ========================================================

    if result["revision_count"] < 1:
        raise RuntimeError(
            "Controlled experiment failed: "
            "revision path was not executed"
        )

    # ========================================================
    # Flush telemetry
    # ========================================================

    langfuse.flush()

    print()
    print(
        "===== LANGFUSE ====="
    )

    print(
        "Forced revision trace sent successfully."
    )


if __name__ == "__main__":
    main()