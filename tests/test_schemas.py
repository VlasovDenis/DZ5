from ai_smm.schemas import (
    ContentPlanItem,
    EditorIssue,
    EditorResult,
    StrategistResult,
)


def test_strategist_schema():
    result = StrategistResult(
        audience_analysis="B2B-аудитория",
        audience_pains=[
            "Ручная работа с договорами",
            "Риск пропуска важных условий",
        ],
        content_pillars=[
            "Экспертный контент",
            "Автоматизация",
        ],
        plan=[
            ContentPlanItem(
                id=1,
                day="Понедельник",
                topic="Ошибки при ручной проверке договоров",
                format="Экспертный пост",
                content_goal="Повысить осведомлённость",
                target_audience="Юристы",
                key_message="Рутинную проверку можно автоматизировать",
                cta="Узнать больше",
                priority="high",
            )
        ],
    )

    assert result.plan[0].id == 1
    assert result.plan[0].priority == "high"


def test_editor_schema():
    result = EditorResult(
        decision="REVISE",
        summary="Требуется исправление",
        issues=[
            EditorIssue(
                post_id=1,
                category="fact",
                quote="Экономия составляет 60%",
                problem="Используется неподтверждённая цифра",
                recommendation="Убрать конкретный процент",
            )            
        ],
    )

    assert result.decision == "REVISE"
    assert len(result.issues) == 1
    assert result.issues[0].quote == "Экономия составляет 60%"