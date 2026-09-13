from pathlib import Path
import os
import sys

from dotenv import load_dotenv


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------
# Load environment BEFORE Langfuse client initialization
# ---------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

# Local services must bypass corporate proxy.
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"


from langfuse import get_client


def main():
    langfuse = get_client()

    print("===== LANGFUSE CONFIG =====")
    print(
        "base_url:",
        os.environ.get("LANGFUSE_BASE_URL"),
    )

    print(
        "public_key configured:",
        bool(os.environ.get("LANGFUSE_PUBLIC_KEY")),
    )

    print(
        "secret_key configured:",
        bool(os.environ.get("LANGFUSE_SECRET_KEY")),
    )

    print()
    print("===== AUTH CHECK =====")

    authenticated = langfuse.auth_check()

    print(
        "authenticated:",
        authenticated,
    )

    if not authenticated:
        raise RuntimeError(
            "Langfuse authentication failed"
        )

    # -----------------------------------------------------
    # Test Trace
    # -----------------------------------------------------

    with langfuse.start_as_current_observation(
        as_type="span",
        name="dz5-smoke-test",
        input={
            "task": "Проверка подключения DZ5 к Langfuse",
        },
    ) as root_span:

        with langfuse.start_as_current_observation(
            as_type="generation",
            name="test-local-llm-generation",
            model="qwen3:4b-instruct",
            input={
                "prompt": (
                    "Что такое мультиагентная система?"
                )
            },
        ) as generation:

            generation.update(
                output=(
                    "Тестовая генерация для проверки "
                    "интеграции Langfuse."
                ),
                usage_details={
                    "input_tokens": 10,
                    "output_tokens": 12,
                },
            )

        root_span.update(
            output={
                "status": "success",
            }
        )

    # Short-lived script:
    # force all buffered telemetry to Langfuse.
    langfuse.flush()

    print()
    print("===== RESULT =====")
    print("Langfuse smoke trace sent successfully.")


if __name__ == "__main__":
    main()