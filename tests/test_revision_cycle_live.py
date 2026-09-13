from ai_smm.graph import (
    prepare_revision_node,
    route_after_editor,
)
from ai_smm.schemas import EditorResult


def test_revision_cycle_live():
    """
    Детерминированно проверяет один полный revision-cycle:

    Editor(REVISE)
        -> prepare_revision
        -> revision_count = 1
        -> Editor(APPROVED)
        -> approved

    Реальная LLM здесь намеренно не используется:
    stochastic поведение модели не должно делать
    regression-тест flaky.
    """

    state = {
        "editor_result": EditorResult(
            decision="REVISE",
            summary="Требуется доработка.",
            issues=[],
        ),
        "revision_count": 0,
        "max_revisions": 3,
        "editor_approved": False,
        "forced_publish": False,
    }

    print()
    print("===== REVISION CYCLE TEST =====")

    # ---------------------------------------------------------
    # Первый Editor требует доработку
    # ---------------------------------------------------------

    route = route_after_editor(state)

    print(
        "before revision:",
        "revision_count=",
        state["revision_count"],
        "route=",
        route,
    )

    assert route == "revise"
    assert state["revision_count"] == 0

    # ---------------------------------------------------------
    # prepare_revision увеличивает счётчик
    # ---------------------------------------------------------

    state.update(
        prepare_revision_node(state)
    )

    print(
        "after prepare_revision:",
        "revision_count=",
        state["revision_count"],
    )

    assert state["revision_count"] == 1

    # ---------------------------------------------------------
    # Повторный Editor одобряет доработанную версию
    # ---------------------------------------------------------

    state["editor_result"] = EditorResult(
        decision="APPROVED",
        summary="Материал исправлен и готов к публикации.",
        issues=[],
    )

    state["editor_approved"] = True

    route = route_after_editor(state)

    print(
        "after second editor:",
        "revision_count=",
        state["revision_count"],
        "route=",
        route,
    )

    assert route == "approved"

    # ---------------------------------------------------------
    # Итог
    # ---------------------------------------------------------

    assert state["revision_count"] == 1
    assert state["revision_count"] <= state["max_revisions"]

    assert state["editor_approved"] is True
    assert state["forced_publish"] is False

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