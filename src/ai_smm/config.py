from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "qwen3:4b-instruct"

    max_revisions: int = 3

    strategist_temperature: float = 0.3
    copywriter_temperature: float = 0.7
    editor_temperature: float = 0.1
    publisher_temperature: float = 0.3


settings = Settings()