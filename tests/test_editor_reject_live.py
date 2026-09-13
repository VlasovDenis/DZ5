from langchain_core.messages import HumanMessage

from ai_smm.agents.editor import editor_node
from ai_smm.schemas import (
    ContentPlanItem,
    CopywriterResult,
    PostDraft,
    StrategistResult,
)


def test_editor_rejects_unsupported_product_claims():
    task = (
        "Подготовить SMM-контент для B2B SaaS-платформы "
        "автоматизации обработки и анализа договоров."
    )

    strategist_result = StrategistResult(
        audience_analysis=(
            "Корпоративные специалисты, работающие "
            "с договорами."
        ),
        audience_pains=[
            "Большой объём ручной работы",
            "Риски ошибок при работе с договорами",
        ],
        content_pillars=[
            "Экспертный контент",
            "Автоматизация",
        ],
        plan=[
            ContentPlanItem(
                id=1,
                day="Понедельник",
                topic="Автоматизация работы с договорами",
                format="expert",
                content_goal="Показать ценность автоматизации",
                target_audience="Юристы",
                key_message=(
                    "Автоматизация может упростить "
                    "работу с договорами"
                ),
                cta="Обсудить текущий процесс",
                priority="high",
            )
        ],
    )

    # Специально плохой текст.
    copywriter_result = CopywriterResult(
        posts=[
            PostDraft(
                post_id=1,
                topic="Автоматизация работы с договорами",
                hook=(
                    "Платформа автоматически отслеживает "
                    "все сроки исполнения договоров."
                ),
                body=(
                    "Система отправляет уведомления "
                    "за три дня до наступления срока, "
                    "интегрируется с ERP и снижает "
                    "количество ошибок на 60%."
                ),
                cta=(
                    "Узнайте, как подключить систему "
                    "к вашей ERP."
                ),
            )
        ]
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
            "Юристы и руководители юридических отделов"
        ),

        "social_network": "VK",

        "verified_product_facts": [
            (
                "Продукт является B2B SaaS-платформой "
                "для автоматизации обработки и анализа договоров."
            )
        ],

        "selected_post_ids": [1],

        "strategist_result": strategist_result,
        "copywriter_result": copywriter_result,

        "revision_count": 0,
        "max_revisions": 3,

        "editor_approved": False,
        "forced_publish": False,
    }

    update = editor_node(state)
    state.update(update)

    result = state["editor_result"]

    print()
    print("===== EDITOR FORCED REJECT TEST =====")
    print("DECISION:", result.decision)
    print("SUMMARY:", result.summary)

    for issue in result.issues:
        print()
        print(
            f"POST {issue.post_id} "
            f"[{issue.category}]"
        )
        print("QUOTE:", issue.quote)
        print("PROBLEM:", issue.problem)
        print(
            "RECOMMENDATION:",
            issue.recommendation,
        )

    assert result.decision == "REVISE"
    assert state["editor_approved"] is False
    assert len(result.issues) > 0

    quoted_text = " ".join(
        issue.quote
        for issue in result.issues
    )

    assert (
        "60%" in quoted_text
        or "ERP" in quoted_text
        or "уведом" in quoted_text.lower()
        or "отслеж" in quoted_text.lower()
    )