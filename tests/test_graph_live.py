from langchain_core.messages import HumanMessage

from ai_smm.graph import smm_graph


def test_smm_graph_live():
    task = (
        "Сформировать контент-план на неделю для "
        "B2B SaaS-платформы автоматизации обработки "
        "и анализа договоров и написать готовые "
        "тексты для трёх постов."
    )

    initial_state = {
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

    result = smm_graph.invoke(
        initial_state
    )

    print()
    print("===== GRAPH FINAL STATE =====")

    print(
        "revision_count:",
        result["revision_count"],
    )

    print(
        "editor_approved:",
        result["editor_approved"],
    )

    print(
        "forced_publish:",
        result["forced_publish"],
    )

    print(
        "editor_decision:",
        result["editor_result"].decision,
    )

    print()
    print("===== MESSAGE HISTORY =====")

    for index, message in enumerate(
        result["messages"],
        start=1,
    ):
        print(
            f"{index}. "
            f"{message.__class__.__name__}"
        )

    print()
    print("===== FINAL POSTS =====")

    for post in result["publisher_result"].posts:
        print()
        print(
            f"----- POST {post.post_id}: "
            f"{post.topic} -----"
        )

        print()
        print(post.text)

        print()
        print(
            "HASHTAGS:",
            " ".join(post.hashtags),
        )

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert result["publisher_result"] is not None

    assert (
        len(result["publisher_result"].posts)
        == 3
    )

    assert (
        result["revision_count"]
        <= result["max_revisions"]
    )

    assert (
        result["editor_approved"]
        or result["forced_publish"]
    )

    final_ids = sorted(
        post.post_id
        for post in result["publisher_result"].posts
    )

    assert final_ids == [1, 3, 4]

    # User + Strategist + Copywriter + Editor + Publisher
    assert len(result["messages"]) >= 5