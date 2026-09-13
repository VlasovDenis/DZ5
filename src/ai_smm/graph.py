from typing import Literal

from langgraph.graph import END, START, StateGraph

from ai_smm.agents.copywriter import copywriter_node
from ai_smm.agents.editor import editor_node
from ai_smm.agents.publisher import publisher_node
from ai_smm.agents.strategist import strategist_node
from ai_smm.state import SMMState


def prepare_revision_node(state: SMMState) -> dict:
    """
    Увеличивает счётчик доработок перед повторным
    вызовом Copywriter.
    """

    next_revision = state["revision_count"] + 1

    return {
        "revision_count": next_revision,
    }


def force_publish_node(state: SMMState) -> dict:
    """
    Активирует forced_publish после достижения
    максимального количества доработок.
    """

    return {
        "forced_publish": True,
        "editor_approved": False,
    }


def route_after_editor(
    state: SMMState,
) -> Literal[
    "approved",
    "revise",
    "force_publish",
]:
    """
    Определяет следующий узел после Editor.
    """

    editor_result = state.get("editor_result")

    if editor_result is None:
        raise ValueError(
            "Routing after Editor requires editor_result"
        )

    # Editor одобрил материал.
    if editor_result.decision == "APPROVED":
        return "approved"

    # Лимит доработок уже достигнут.
    if (
        state["revision_count"]
        >= state["max_revisions"]
    ):
        return "force_publish"

    # Есть возможность отправить текст
    # Copywriter на очередную доработку.
    return "revise"


def build_smm_graph():
    """
    Создаёт и компилирует LangGraph
    для AI SMM-отдела.
    """

    builder = StateGraph(SMMState)

    # ---------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------

    builder.add_node(
        "strategist",
        strategist_node,
    )

    builder.add_node(
        "copywriter",
        copywriter_node,
    )

    builder.add_node(
        "editor",
        editor_node,
    )

    builder.add_node(
        "prepare_revision",
        prepare_revision_node,
    )

    builder.add_node(
        "force_publish",
        force_publish_node,
    )

    builder.add_node(
        "publisher",
        publisher_node,
    )

    # ---------------------------------------------------------
    # Main flow
    # ---------------------------------------------------------

    builder.add_edge(
        START,
        "strategist",
    )

    builder.add_edge(
        "strategist",
        "copywriter",
    )

    builder.add_edge(
        "copywriter",
        "editor",
    )

    # ---------------------------------------------------------
    # Conditional routing after Editor
    # ---------------------------------------------------------

    builder.add_conditional_edges(
        "editor",
        route_after_editor,
        {
            "approved": "publisher",
            "revise": "prepare_revision",
            "force_publish": "force_publish",
        },
    )

    # ---------------------------------------------------------
    # Revision loop
    # ---------------------------------------------------------

    builder.add_edge(
        "prepare_revision",
        "copywriter",
    )

    # ---------------------------------------------------------
    # Revision limit reached
    # ---------------------------------------------------------

    builder.add_edge(
        "force_publish",
        "publisher",
    )

    # ---------------------------------------------------------
    # Finish
    # ---------------------------------------------------------

    builder.add_edge(
        "publisher",
        END,
    )

    return builder.compile()


smm_graph = build_smm_graph()