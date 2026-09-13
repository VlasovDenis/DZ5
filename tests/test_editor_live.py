from langchain_core.messages import HumanMessage

from ai_smm.agents.copywriter import copywriter_node
from ai_smm.agents.editor import editor_node
from ai_smm.agents.strategist import strategist_node


def test_editor_live():
    task = (
        "Сформировать контент-план на неделю для "
        "B2B SaaS-платформы автоматизации обработки "
        "и анализа договоров и написать готовые "
        "тексты для трёх постов."
    )

    state = {
        "messages": [
            HumanMessage(content=task)
        ],
        "task": task,
        "niche": (
            "B2B SaaS-платформа для автоматизации "
            "обработки и анализа договоров"
        ),
        "target_audience": (
            "Юристы, руководители юридических отделов, "
            "специалисты по закупкам, финансовые директора "
            "и операционные руководители."
        ),
        "social_network": "VK",
        "verified_product_facts": [
            (
                "Продукт является B2B SaaS-платформой "
                "для автоматизации обработки и анализа договоров."
            ),
        ],
        "selected_post_ids": [1, 3, 4],
        "revision_count": 0,
        "max_revisions": 3,
        "editor_approved": False,
        "forced_publish": False,
    }

    strategist_update = strategist_node(state)
    state.update(strategist_update)

    copywriter_update = copywriter_node(state)
    state.update(copywriter_update)

    editor_update = editor_node(state)
    state.update(editor_update)

    editor_result = state["editor_result"]

    print()
    print("===== EDITOR RESULT =====")
    print("DECISION:", editor_result.decision)

    print()
    print("SUMMARY:")
    print(editor_result.summary)

    print()
    print("ISSUES:")

    for issue in editor_result.issues:
        print()
        print(
            f"Post {issue.post_id} "
            f"[{issue.category}]"
        )
        print("Problem:", issue.problem)
        print(
            "Recommendation:",
            issue.recommendation,
        )

    assert editor_result.decision in {
        "APPROVED",
        "REVISE",
    }

    assert (
        state["editor_approved"]
        == (editor_result.decision == "APPROVED")
    )