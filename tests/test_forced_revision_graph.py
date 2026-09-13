from ai_smm.forced_revision_graph import (
    build_forced_revision_graph,
)


def test_forced_revision_graph_compiles():
    graph = build_forced_revision_graph()

    assert graph is not None


def test_forced_revision_graph_has_nodes():
    graph = build_forced_revision_graph()

    node_names = set(
        graph.get_graph().nodes.keys()
    )

    expected = {
        "__start__",
        "strategist",
        "copywriter",
        "editor",
        "prepare_revision",
        "force_publish",
        "publisher",
        "__end__",
    }

    assert expected.issubset(
        node_names
    )