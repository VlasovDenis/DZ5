from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai_smm.config import settings
from ai_smm.llm import create_llm
from ai_smm.prompts.strategist import STRATEGIST_SYSTEM_PROMPT
from ai_smm.schemas import StrategistResult
from ai_smm.state import SMMState
from langchain_core.runnables import RunnableConfig

def strategist_node(
    state: SMMState,
    config: RunnableConfig | None = None,
) -> dict:
    llm = create_llm(
        temperature=settings.strategist_temperature,
        num_predict=2500,
    )

    structured_llm = llm.with_structured_output(
        StrategistResult,
        method="json_schema",
        include_raw=True,
    )

    user_prompt = f"""
Исходная задача пользователя:

{state["task"]}

Бизнес-ниша:
{state["niche"]}

Целевая аудитория:
{state["target_audience"]}

Целевая социальная сеть:
{state["social_network"]}

Сформируй стратегию и контент-план ровно на 7 дней.

Используй только предоставленный бизнес-контекст.
Если информации для конкретного факта нет, не придумывай её.
"""
    llm_config = dict(config or {})
    llm_config["run_name"] = "strategist-llm"

    result = structured_llm.invoke(
        [
            SystemMessage(content=STRATEGIST_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ],
        config=llm_config,
    )

    if result["parsing_error"] is not None:
        raise RuntimeError(
            f"Strategist structured output error: "
            f"{result['parsing_error']}"
        )

    parsed: StrategistResult = result["parsed"]
    raw = result["raw"]

    if parsed is None:
        raise RuntimeError("Strategist returned empty parsed result")

    if len(parsed.plan) != 7:
        raise ValueError(
            f"Strategist must return exactly 7 plan items, "
            f"got {len(parsed.plan)}"
        )

    return {
        "strategist_result": parsed,
        "messages": [
            AIMessage(
                content=(
                    "[Strategist]\n"
                    + parsed.model_dump_json(
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            )
        ],
    }