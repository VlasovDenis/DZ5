from ai_smm.agents.strategist import strategist_node


def test_strategist_live():
    state = {
        "messages": [],
        "task": (
            "Сформировать контент-план на неделю для "
            "B2B SaaS-платформы автоматизации обработки "
            "и анализа договоров и подготовить основу "
            "для написания трёх постов."
        ),
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
        "revision_count": 0,
        "max_revisions": 3,
        "editor_approved": False,
        "forced_publish": False,
    }
    result = strategist_node(state)

    strategist_result = result["strategist_result"]

    assert len(strategist_result.plan) == 7
    assert [item.id for item in strategist_result.plan] == list(range(1, 8))
    assert len(strategist_result.audience_pains) > 0
    assert len(strategist_result.content_pillars) > 0
    assert len(result["messages"]) == 1

    print()
    print("===== AUDIENCE =====")
    print(strategist_result.audience_analysis)

    print()
    print("===== CONTENT PILLARS =====")
    for pillar in strategist_result.content_pillars:
        print("-", pillar)

    print()
    print("===== PLAN =====")
    for item in strategist_result.plan:
        print(
            f"{item.id}. {item.day}: "
            f"{item.topic} [{item.format}]"
        )