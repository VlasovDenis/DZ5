from ai_smm.graph import route_after_editor
from ai_smm.schemas import EditorResult


def make_state(
    decision: str,
    revision_count: int,
    max_revisions: int = 3,
):
    return {
        "editor_result": EditorResult(
            decision=decision,
            summary="test",
            issues=[],
        ),
        "revision_count": revision_count,
        "max_revisions": max_revisions,
    }


def test_route_approved():
    state = make_state(
        decision="APPROVED",
        revision_count=0,
    )

    assert (
        route_after_editor(state)
        == "approved"
    )


def test_route_first_revision():
    state = make_state(
        decision="REVISE",
        revision_count=0,
    )

    assert (
        route_after_editor(state)
        == "revise"
    )


def test_route_second_revision():
    state = make_state(
        decision="REVISE",
        revision_count=2,
    )

    assert (
        route_after_editor(state)
        == "revise"
    )


def test_route_revision_limit():
    state = make_state(
        decision="REVISE",
        revision_count=3,
    )

    assert (
        route_after_editor(state)
        == "force_publish"
    )