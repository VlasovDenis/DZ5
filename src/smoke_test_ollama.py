from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama


MODEL_NAME = "qwen3:4b-instruct"
OLLAMA_URL = "http://localhost:11434"


llm = ChatOllama(
    model=MODEL_NAME,
    base_url=OLLAMA_URL,
    temperature=0.2,
    num_predict=128,
    keep_alive="10m",
)


messages = [
    SystemMessage(
        content=(
            "Ты полезный русскоязычный помощник. "
            "Отвечай кратко, точно и только по существу."
        )
    ),
    HumanMessage(
        content=(
            "Что такое мультиагентная система? "
            "Ответь одним коротким предложением."
        )
    ),
]


response = llm.invoke(messages)


print("===== CONTENT =====")
print(response.content)

print("\n===== USAGE METADATA =====")
print(response.usage_metadata)

print("\n===== RESPONSE METADATA =====")
print(response.response_metadata)