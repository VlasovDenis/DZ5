from pathlib import Path
import sys


# Корень проекта:
# C:\PROJECTS\OTUS\DZ5
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# src-layout проекта:
# C:\PROJECTS\OTUS\DZ5\src
SRC_DIR = PROJECT_ROOT / "src"

# Позволяет запускать скрипт напрямую:
# python .\scripts\export_graph.py
sys.path.insert(0, str(SRC_DIR))


from ai_smm.graph import smm_graph


def main():
    artifacts_dir = PROJECT_ROOT / "artifacts"

    artifacts_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    mermaid = (
        smm_graph
        .get_graph()
        .draw_mermaid()
    )

    mmd_path = (
        artifacts_dir
        / "smm_graph.mmd"
    )

    mmd_path.write_text(
        mermaid,
        encoding="utf-8",
    )

    markdown_path = (
        artifacts_dir
        / "smm_graph.md"
    )

    markdown_path.write_text(
        (
            "# AI SMM Multi-Agent Graph\n\n"
            "```mermaid\n"
            f"{mermaid}\n"
            "```\n"
        ),
        encoding="utf-8",
    )

    print("===== LANGGRAPH MERMAID =====")
    print()
    print(mermaid)

    print()
    print(f"Saved: {mmd_path}")
    print(f"Saved: {markdown_path}")


if __name__ == "__main__":
    main()