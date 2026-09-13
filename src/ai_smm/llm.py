import os


# ============================================================
# IMPORTANT:
#
# На корпоративной Windows-машине HTTPS_PROXY может приводить
# к падению ollama/httpx во время импорта:
#
# Windows fatal exception: access violation
# ssl.create_default_context
#
# Удаляем HTTPS proxy ТОЛЬКО внутри данного Python-процесса
# и только до импорта langchain_ollama.
#
# Глобальные настройки Windows / PowerShell не изменяются.
# ============================================================

os.environ.pop(
    "HTTPS_PROXY",
    None,
)

os.environ.pop(
    "https_proxy",
    None,
)

os.environ["NO_PROXY"] = (
    "localhost,127.0.0.1"
)

os.environ["no_proxy"] = (
    "localhost,127.0.0.1"
)


from langchain_ollama import ChatOllama

from ai_smm.config import settings


def create_llm(
    temperature: float,
    num_predict: int = 2048,
) -> ChatOllama:
    return ChatOllama(
        model=settings.model_name,
        base_url=settings.ollama_base_url,
        temperature=temperature,
        num_ctx=8192,
        num_predict=num_predict,
        keep_alive="10m",
        validate_model_on_init=True,

        # Не позволяем httpx использовать proxy settings
        # окружения для локального Ollama.
        client_kwargs={
            "trust_env": False,
        },
    )