from langchain_core.messages import HumanMessage

from ai_smm.agents.publisher import publisher_node
from ai_smm.schemas import (
    CopywriterResult,
    EditorResult,
    PostDraft,
)


def test_publisher_live():
    task = (
        "Подготовить три финальных поста "
        "для B2B SaaS-платформы."
    )

    # ---------------------------------------------------------
    # Заранее подготовленный валидный результат Copywriter.
    #
    # Publisher-тест не должен зависеть от случайного
    # поведения Strategist / Copywriter / Editor.
    # ---------------------------------------------------------

    copywriter_result = CopywriterResult(
        posts=[
            PostDraft(
                post_id=1,
                topic="Ручная работа с договорами",
                hook=(
                    "Почему работа с договорами "
                    "занимает так много времени?"
                ),
                body=(
                    "Автоматизация обработки и анализа "
                    "договоров может упростить работу "
                    "с большим количеством документов."
                ),
                cta=(
                    "Расскажите, какие задачи при работе "
                    "с договорами занимают у вас больше "
                    "всего времени."
                ),
            ),
            PostDraft(
                post_id=3,
                topic="Анализ договоров",
                hook=(
                    "Что усложняет анализ большого "
                    "количества договоров?"
                ),
                body=(
                    "При большом объёме документов "
                    "ручная обработка требует значительных "
                    "усилий. Автоматизация помогает "
                    "организовать процесс обработки "
                    "и анализа договоров."
                ),
                cta=(
                    "Поделитесь, как в вашей компании "
                    "организован анализ договоров."
                ),
            ),
            PostDraft(
                post_id=4,
                topic="Автоматизация договорной работы",
                hook=(
                    "Какие процессы при работе с договорами "
                    "можно сделать удобнее?"
                ),
                body=(
                    "B2B SaaS-платформа может использоваться "
                    "для автоматизации обработки и анализа "
                    "договоров."
                ),
                cta=(
                    "Напишите, какие этапы договорной работы "
                    "вы хотели бы автоматизировать."
                ),
            ),
        ]
    )

    # ---------------------------------------------------------
    # Publisher разрешён только после APPROVED
    # либо forced_publish.
    #
    # Здесь явно создаём approved-flow.
    # ---------------------------------------------------------

    editor_result = EditorResult(
        decision="APPROVED",
        summary=(
            "Тексты готовы к публикации."
        ),
        issues=[],
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
                "для автоматизации обработки и анализа "
                "договоров."
            ),
        ],

        "selected_post_ids": [
            1,
            3,
            4,
        ],

        "copywriter_result": copywriter_result,
        "editor_result": editor_result,

        "revision_count": 0,
        "max_revisions": 3,

        "editor_approved": True,
        "forced_publish": False,
    }

    # ---------------------------------------------------------
    # Publisher
    # ---------------------------------------------------------

    update = publisher_node(state)

    publisher_result = update[
        "publisher_result"
    ]

    source_posts = {
        post.post_id: post
        for post in copywriter_result.posts
    }

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    assert len(
        publisher_result.posts
    ) == 3

    assert sorted(
        post.post_id
        for post in publisher_result.posts
    ) == [
        1,
        3,
        4,
    ]

    print()
    print(
        "===== PUBLISHER RESULT ====="
    )

    for post in publisher_result.posts:
        source = source_posts[
            post.post_id
        ]

        # Publisher не должен переписывать
        # проверенный Copywriter content.
        assert source.hook in post.text
        assert source.body in post.text
        assert source.cta in post.text

        assert (
            post.topic
            == source.topic
        )

        # LLM Publisher отвечает только
        # за оформление.
        assert (
            2
            <= len(post.hashtags)
            <= 5
        )

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
            " ".join(
                post.hashtags
            ),
        )