from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from ai_smm.agents.copywriter import copywriter_node
from ai_smm.agents.editor import editor_node
from ai_smm.agents.publisher import publisher_node
from ai_smm.agents.strategist import strategist_node
from ai_smm.graph import (
    force_publish_node,
    prepare_revision_node,
    route_after_editor,
)
from ai_smm.schemas import EditorIssue, EditorResult
from ai_smm.state import SMMState


def controlled_editor_node(
    state: SMMState,
    config: RunnableConfig | None = None,
) -> dict:
    """
    Контрольный Editor для демонстрации revision edge.

    1. Всегда вызывает настоящий editor_node.
    2. Если настоящий Editor сам вернул REVISE,
       используем его результат без изменений.
    3. Только на первой проверке, если Editor вернул
       APPROVED, создаём одно контролируемое замечание.
    4. После первой revision никакого вмешательства нет.
    """

    real_update = editor_node(
        state,
        config,
    )

    real_result: EditorResult = real_update[
        "editor_result"
    ]

    # -----------------------------------------------------
    # Если настоящий Editor сам нашёл проблему —
    # вообще ничего не меняем.
    # -----------------------------------------------------

    if real_result.decision == "REVISE":
        return real_update

    # -----------------------------------------------------
    # После первой доработки используем только
    # настоящий результат Editor.
    # -----------------------------------------------------

    if state["revision_count"] > 0:
        return real_update

    # -----------------------------------------------------
    # Первый Editor сказал APPROVED.
    #
    # Для контролируемого эксперимента создаём одно
    # гарантированное revision замечание.
    # Quote берём прямо из текущего draft.
    # -----------------------------------------------------

    copywriter_result = state.get(
        "copywriter_result"
    )

    if copywriter_result is None:
        raise ValueError(
            "Controlled Editor requires "
            "copywriter_result"
        )

    first_post = copywriter_result.posts[0]

    controlled_result = EditorResult(
        decision="REVISE",
        summary=(
            "Контрольная revision-итерация для проверки "
            "условного перехода Editor → Copywriter "
            "в LangGraph."
        ),
        issues=[
            EditorIssue(
                post_id=first_post.post_id,
                category="style",
                quote=first_post.hook,
                problem=(
                    "Для контрольного сценария необходимо "
                    "выполнить хотя бы одну редакторскую "
                    "итерацию и повторно проверить текст."
                ),
                recommendation=(
                    "Сделать hook короче и яснее, "
                    "сохранив тему, факты и смысл поста."
                ),
            )
        ],
    )

    return {
        "editor_result": controlled_result,
        "editor_approved": False,
        "messages": [
            AIMessage(
                content=(
                    "[Editor - controlled revision]\n"
                    + controlled_result.model_dump_json(
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            )
        ],
    }


def build_forced_revision_graph():
    builder = StateGraph(SMMState)

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
        controlled_editor_node,
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

    builder.add_conditional_edges(
        "editor",
        route_after_editor,
        {
            "approved": "publisher",
            "revise": "prepare_revision",
            "force_publish": "force_publish",
        },
    )

    builder.add_edge(
        "prepare_revision",
        "copywriter",
    )

    builder.add_edge(
        "force_publish",
        "publisher",
    )

    builder.add_edge(
        "publisher",
        END,
    )

    return builder.compile()


forced_revision_graph = (
    build_forced_revision_graph()
)