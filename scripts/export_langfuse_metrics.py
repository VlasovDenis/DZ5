from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv
import os
import sys

from dotenv import load_dotenv


# ============================================================
# Project
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "metrics"

sys.path.insert(0, str(SRC_DIR))

ARTIFACTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Environment
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"


from langfuse import get_client


# ============================================================
# Helpers
# ============================================================

AGENT_NAMES = {
    "strategist",
    "copywriter",
    "editor",
    "publisher",
}


def as_dict(value) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump()

    if isinstance(value, dict):
        return value

    return dict(value)


def get_value(data: dict, *names, default=None):
    for name in names:
        if name in data:
            return data[name]

    return default


def find_agent(
    observation: dict,
    observations_by_id: dict[str, dict],
) -> str:
    """
    Поднимаемся вверх по parentObservationId до LangGraph node.
    """

    parent_id = get_value(
        observation,
        "parent_observation_id",
        "parentObservationId",
    )

    while parent_id:
        parent = observations_by_id.get(parent_id)

        if parent is None:
            break

        name = get_value(
            parent,
            "name",
            default="",
        )

        if name in AGENT_NAMES:
            return name

        parent_id = get_value(
            parent,
            "parent_observation_id",
            "parentObservationId",
        )

    return "unknown"


def find_latest_root(
    langfuse,
    trace_name: str,
) -> dict:
    """
    Ищем последний root observation указанного типа.
    """

    now = datetime.now(timezone.utc)

    response = langfuse.api.observations.get_many(
        name=trace_name,
        is_root_observation=True,
        from_start_time=now - timedelta(days=2),
        to_start_time=now + timedelta(minutes=5),
        fields="core,basic,metrics,trace_context",
        limit=50,
    )

    if not response.data:
        raise RuntimeError(
            f"No Langfuse trace found: {trace_name}"
        )

    # API возвращает observations от новых к старым.
    return as_dict(response.data[0])


def load_trace_observations(
    langfuse,
    trace_id: str,
) -> list[dict]:
    now = datetime.now(timezone.utc)

    response = langfuse.api.observations.get_many(
        trace_id=trace_id,
        from_start_time=now - timedelta(days=2),
        to_start_time=now + timedelta(minutes=5),
        fields=(
            "core,basic,model,usage,"
            "metrics,trace_context"
        ),
        limit=1000,
    )

    return [
        as_dict(item)
        for item in response.data
    ]


def analyze_trace(
    langfuse,
    trace_name: str,
    label: str,
) -> dict:
    root = find_latest_root(
        langfuse,
        trace_name,
    )

    trace_id = get_value(
        root,
        "trace_id",
        "traceId",
    )

    observations = load_trace_observations(
        langfuse,
        trace_id,
    )

    observations_by_id = {
        get_value(item, "id"): item
        for item in observations
    }

    generations = [
        item
        for item in observations
        if str(
            get_value(
                item,
                "type",
                default="",
            )
        ).upper()
        == "GENERATION"
    ]

    generations.sort(
        key=lambda item: str(
            get_value(
                item,
                "start_time",
                "startTime",
                default="",
            )
        )
    )

    counters = defaultdict(int)

    rows = []

    for generation in generations:
        agent = find_agent(
            generation,
            observations_by_id,
        )

        counters[agent] += 1

        if counters[agent] > 1:
            step = (
                f"{agent} #{counters[agent]}"
            )
        else:
            step = agent

        input_tokens = (
            get_value(
                generation,
                "input_usage",
                "inputUsage",
                default=0,
            )
            or 0
        )

        output_tokens = (
            get_value(
                generation,
                "output_usage",
                "outputUsage",
                default=0,
            )
            or 0
        )

        total_tokens = (
            get_value(
                generation,
                "total_usage",
                "totalUsage",
                default=0,
            )
            or 0
        )

        latency = get_value(
            generation,
            "latency",
            default=None,
        )

        ttft = get_value(
            generation,
            "time_to_first_token",
            "timeToFirstToken",
            default=None,
        )

        model = get_value(
            generation,
            "model",
            default="",
        )

        total_cost = (
            get_value(
                generation,
                "total_cost",
                "totalCost",
                default=0,
            )
            or 0
        )

        rows.append(
            {
                "run": label,
                "step": step,
                "agent": agent,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "latency_seconds": latency,
                "ttft_seconds": ttft,
                "cost": total_cost,
            }
        )

    root_latency = get_value(
        root,
        "latency",
        default=None,
    )

    return {
        "label": label,
        "trace_name": trace_name,
        "trace_id": trace_id,
        "root_latency": root_latency,
        "rows": rows,
    }


def fmt_number(value) -> str:
    if value is None:
        return "-"

    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


def write_report(runs: list[dict]) -> None:
    csv_path = (
        ARTIFACTS_DIR
        / "langfuse-agent-metrics.csv"
    )

    md_path = (
        ARTIFACTS_DIR
        / "langfuse-agent-metrics.md"
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    fieldnames = [
        "run",
        "step",
        "agent",
        "model",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "latency_seconds",
        "ttft_seconds",
        "cost",
    ]

    with csv_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for run in runs:
            writer.writerows(
                run["rows"]
            )

    # --------------------------------------------------------
    # Markdown
    # --------------------------------------------------------

    lines = [
        "# Langfuse agent metrics",
        "",
    ]

    for run in runs:
        rows = run["rows"]

        input_total = sum(
            row["input_tokens"]
            for row in rows
        )

        output_total = sum(
            row["output_tokens"]
            for row in rows
        )

        token_total = sum(
            row["total_tokens"]
            for row in rows
        )

        llm_latency_total = sum(
            row["latency_seconds"] or 0
            for row in rows
        )

        cost_total = sum(
            float(row["cost"] or 0)
            for row in rows
        )

        lines.extend(
            [
                f"## {run['label']}",
                "",
                f"- Trace name: `{run['trace_name']}`",
                f"- Trace ID: `{run['trace_id']}`",
                (
                    "- End-to-end latency: "
                    f"{fmt_number(run['root_latency'])} s"
                ),
                f"- LLM calls: {len(rows)}",
                f"- Input tokens: {input_total}",
                f"- Output tokens: {output_total}",
                f"- Total tokens: {token_total}",
                (
                    "- Sum of LLM generation latency: "
                    f"{llm_latency_total:.2f} s"
                ),
                f"- External API cost: {cost_total:.6f}",
                "",
                "| Step | Model | Input | Output | Total | "
                "Latency, s | TTFT, s |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )

        for row in rows:
            lines.append(
                "| "
                f"{row['step']} | "
                f"{row['model']} | "
                f"{row['input_tokens']} | "
                f"{row['output_tokens']} | "
                f"{row['total_tokens']} | "
                f"{fmt_number(row['latency_seconds'])} | "
                f"{fmt_number(row['ttft_seconds'])} |"
            )

        lines.append("")

    md_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()
    print("===== SAVED =====")
    print(csv_path)
    print(md_path)


def main():
    langfuse = get_client()

    print("===== LANGFUSE AUTH =====")

    if not langfuse.auth_check():
        raise RuntimeError(
            "Langfuse authentication failed"
        )

    print("authenticated: True")

    runs = [
        analyze_trace(
            langfuse,
            trace_name=(
                "ai-smm-multi-agent-run"
            ),
            label="Normal run",
        ),
        analyze_trace(
            langfuse,
            trace_name=(
                "ai-smm-forced-revision-run"
            ),
            label="Controlled revision run",
        ),
    ]

    for run in runs:
        print()
        print(
            f"===== {run['label'].upper()} ====="
        )

        print(
            "trace_id:",
            run["trace_id"],
        )

        print(
            "end_to_end_latency:",
            run["root_latency"],
        )

        print(
            "llm_calls:",
            len(run["rows"]),
        )

        for row in run["rows"]:
            print(
                f"{row['step']:<15} "
                f"in={row['input_tokens']:<6} "
                f"out={row['output_tokens']:<6} "
                f"total={row['total_tokens']:<6} "
                f"latency={fmt_number(row['latency_seconds'])}s"
            )

    write_report(runs)


if __name__ == "__main__":
    main()