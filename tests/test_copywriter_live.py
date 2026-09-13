from langchain_core.messages import HumanMessage

from ai_smm.agents.copywriter import copywriter_node
from ai_smm.agents.strategist import strategist_node


def test_copywriter_live():
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

    result = state["copywriter_result"]

    assert len(result.posts) == 3

    assert sorted(
        post.post_id for post in result.posts
    ) == [1, 3, 4]

    print()
    print("===== COPYWRITER RESULT =====")

    for post in result.posts:
        print()
        print(
            f"----- POST {post.post_id}: "
            f"{post.topic} -----"
        )
        print()
        print("HOOK:")
        print(post.hook)

        print()
        print("BODY:")
        print(post.body)

        print()
        print("CTA:")
        print(post.cta)