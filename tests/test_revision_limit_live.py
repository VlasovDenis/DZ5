from ai_smm.graph import (
    force_publish_node,
    prepare_revision_node,
    route_after_editor,
)
from ai_smm.schemas import EditorResult


def make_revise_state(
    revision_count: int = 0,
    max_revisions: int = 3,
) -> dict:
    """
    Создаёт минимальное состояние,
    в котором Editor требует доработку.
    """

    return {
        "editor_result": EditorResult(
            decision="REVISE",
            summary="Требуется доработка.",
            issues=[],
        ),
        "revision_count": revision_count,
        "max_revisions": max_revisions,
        "editor_approved": False,
        "forced_publish": False,
    }


def test_revision_limit_live():
    """
    Проверяет полный deterministic lifecycle
    достижения max_revisions без вызовов LLM.

    Ожидаемый путь:

    revision_count=0
        -> revise
        -> prepare_revision -> 1

    revision_count=1
        -> revise
        -> prepare_revision -> 2

    revision_count=2
        -> revise
        -> prepare_revision -> 3

    revision_count=3
        -> force_publish
    """

    state = make_revise_state(
        revision_count=0,
        max_revisions=3,
    )

    print()
    print("===== REVISION LIMIT TEST =====")

    # ---------------------------------------------------------
    # Revision #1
    # ---------------------------------------------------------

    route = route_after_editor(state)

    print()
    print(
        "revision_count:",
        state["revision_count"],
        "route:",
        route,
    )

    assert route == "revise"

    state.update(
        prepare_revision_node(state)
    )

    assert state["revision_count"] == 1

    # ---------------------------------------------------------
    # Revision #2
    # ---------------------------------------------------------

    route = route_after_editor(state)

    print(
        "revision_count:",
        state["revision_count"],
        "route:",
        route,
    )

    assert route == "revise"

    state.update(
        prepare_revision_node(state)
    )

    assert state["revision_count"] == 2

    # ---------------------------------------------------------
    # Revision #3
    # ---------------------------------------------------------

    route = route_after_editor(state)

    print(
        "revision_count:",
        state["revision_count"],
        "route:",
        route,
    )

    assert route == "revise"

    state.update(
        prepare_revision_node(state)
    )

    assert state["revision_count"] == 3

    # ---------------------------------------------------------
    # Limit reached
    # ---------------------------------------------------------

    route = route_after_editor(state)

    print(
        "revision_count:",
        state["revision_count"],
        "route:",
        route,
    )

    assert route == "force_publish"

    # ---------------------------------------------------------
    # force_publish node
    # ---------------------------------------------------------

    state.update(
        force_publish_node(state)
    )

    print()
    print("===== FINAL STATE =====")
    print(
        "revision_count:",
        state["revision_count"],
    )
    print(
        "editor_approved:",
        state["editor_approved"],
    )
    print(
        "forced_publish:",
        state["forced_publish"],
    )

    assert state["revision_count"] == 3
    assert state["max_revisions"] == 3

    assert state["editor_approved"] is False
    assert state["forced_publish"] is True

    # Счётчик не должен превысить лимит.
    assert (
        state["revision_count"]
        <= state["max_revisions"]
    )