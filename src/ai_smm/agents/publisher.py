from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai_smm.config import settings
from ai_smm.llm import create_llm
from ai_smm.prompts.publisher import PUBLISHER_SYSTEM_PROMPT
from ai_smm.schemas import (
    PublishedPost,
    PublisherFormattingResult,
    PublisherResult,
)
from ai_smm.state import SMMState
from langchain_core.runnables import RunnableConfig

def publisher_node(
    state: SMMState,
    config: RunnableConfig | None = None,
) -> dict:
    copywriter_result = state.get("copywriter_result")
    editor_result = state.get("editor_result")

    if copywriter_result is None:
        raise ValueError(
            "Publisher requires copywriter_result"
        )

    if editor_result is None:
        raise ValueError(
            "Publisher requires editor_result"
        )

    if (
        editor_result.decision != "APPROVED"
        and not state["forced_publish"]
    ):
        raise ValueError(
            "Publisher requires APPROVED content "
            "or forced_publish=True"
        )

    # ---------------------------------------------------------
    # Publisher LLM занимается ТОЛЬКО оформлением.
    # ---------------------------------------------------------

    llm = create_llm(
        temperature=settings.publisher_temperature,
        num_predict=1000,
    )

    structured_llm = llm.with_structured_output(
        PublisherFormattingResult,
        method="json_schema",
        include_raw=True,
    )

    copywriter_json = copywriter_result.model_dump_json(
        indent=2,
        ensure_ascii=False,
    )

    user_prompt = f"""
Социальная сеть:
{state["social_network"]}

Подготовь оформление для следующих публикаций:

{copywriter_json}

Для каждого post_id верни только:
- emoji;
- hashtags.

Не переписывай и не генерируй текст публикации.
"""

    llm_config = dict(config or {})
    llm_config["run_name"] = "publisher-llm"

    result = structured_llm.invoke(
        [
            SystemMessage(
                content=PUBLISHER_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=user_prompt
            ),
        ],
        config=llm_config,
    )

    if result["parsing_error"] is not None:
        raise RuntimeError(
            f"Publisher structured output error: "
            f"{result['parsing_error']}"
        )

    formatting: PublisherFormattingResult = result["parsed"]

    if formatting is None:
        raise RuntimeError(
            "Publisher returned empty parsed result"
        )

    # ---------------------------------------------------------
    # Проверяем post_id.
    # ---------------------------------------------------------

    source_ids = sorted(
        post.post_id
        for post in copywriter_result.posts
    )

    formatting_ids = sorted(
        item.post_id
        for item in formatting.posts
    )

    if source_ids != formatting_ids:
        raise ValueError(
            f"Publisher returned IDs {formatting_ids}, "
            f"expected {source_ids}"
        )

    formatting_by_id = {
        item.post_id: item
        for item in formatting.posts
    }

    # ---------------------------------------------------------
    # Финальный текст собираем ДЕТЕРМИНИРОВАННО.
    #
    # LLM не имеет возможности изменить содержание.
    # ---------------------------------------------------------

    published_posts = []

    for source_post in copywriter_result.posts:
        decoration = formatting_by_id[
            source_post.post_id
        ]

        hook = source_post.hook.strip()

        if decoration.emoji.strip():
            hook = (
                f"{decoration.emoji.strip()} "
                f"{hook}"
            )

        final_text = "\n\n".join(
            [
                hook,
                source_post.body.strip(),
                source_post.cta.strip(),
            ]
        )

        # Нормализуем hashtags.
        hashtags = []

        for hashtag in decoration.hashtags:
            hashtag = hashtag.strip()

            if not hashtag:
                continue

            if not hashtag.startswith("#"):
                hashtag = "#" + hashtag

            hashtags.append(hashtag)

        published_posts.append(
            PublishedPost(
                post_id=source_post.post_id,
                topic=source_post.topic,
                text=final_text,
                hashtags=hashtags,
            )
        )

    parsed = PublisherResult(
        posts=published_posts
    )

    return {
        "publisher_result": parsed,
        "messages": [
            AIMessage(
                content=(
                    "[Publisher]\n"
                    + parsed.model_dump_json(
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            )
        ],
    }