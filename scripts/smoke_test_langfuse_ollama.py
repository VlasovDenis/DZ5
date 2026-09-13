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
# Environment
# ---------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"


# ВАЖНО:
# ai_smm.llm должен импортироваться после настройки env.
from langchain_core.messages import HumanMessage, SystemMessage

from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from ai_smm.llm import create_llm


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

    # -----------------------------------------------------
    # Real local model
    # -----------------------------------------------------

    llm = create_llm(
        temperature=0.2,
        num_predict=128,
    )

    langfuse_handler = CallbackHandler()

    messages = [
        SystemMessage(
            content=(
                "Ты полезный русскоязычный помощник. "
                "Отвечай кратко и точно."
            )
        ),
        HumanMessage(
            content=(
                "Что такое мультиагентная система? "
                "Ответь одним коротким предложением."
            )
        ),
    ]

    # -----------------------------------------------------
    # Parent trace/span for the whole test
    # -----------------------------------------------------

    with langfuse.start_as_current_observation(
        as_type="span",
        name="dz5-real-ollama-smoke",
        input={
            "task": (
                "Проверка реального вызова "
                "ChatOllama через Langfuse"
            ),
            "model": "qwen3:4b-instruct",
        },
    ) as root_span:

        # Эти атрибуты будут у дочерних observations.
        with propagate_attributes(
            session_id="dz5-smoke-session",
            tags=[
                "dz5",
                "ollama",
                "langchain",
                "smoke-test",
            ],
        ):
            response = llm.invoke(
                messages,
                config={
                    "callbacks": [
                        langfuse_handler
                    ],
                    "run_name": (
                        "qwen3-4b-instruct-smoke"
                    ),
                },
            )

        root_span.update(
            output={
                "content": response.content,
            }
        )

    # -----------------------------------------------------
    # Local diagnostics
    # -----------------------------------------------------

    print()
    print("===== CONTENT =====")
    print(response.content)

    print()
    print("===== USAGE METADATA =====")
    print(response.usage_metadata)

    print()
    print("===== RESPONSE METADATA =====")
    print(response.response_metadata)

    # Short-lived script -> ensure telemetry is sent.
    langfuse.flush()

    print()
    print("===== RESULT =====")
    print(
        "Real Ollama Langfuse trace "
        "sent successfully."
    )


if __name__ == "__main__":
    main()