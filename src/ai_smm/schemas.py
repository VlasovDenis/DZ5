from typing import Literal

from pydantic import BaseModel, Field


class ContentPlanItem(BaseModel):
    id: int = Field(description="Уникальный номер элемента контент-плана")
    day: str = Field(description="День недели")
    topic: str = Field(description="Тема публикации")
    format: str = Field(description="Формат публикации")
    content_goal: str = Field(description="Цель публикации")
    target_audience: str = Field(description="Целевая аудитория")
    key_message: str = Field(description="Ключевая мысль")
    cta: str = Field(description="Призыв к действию")
    priority: Literal["low", "medium", "high"]


class StrategistResult(BaseModel):
    audience_analysis: str = Field(
        description="Краткий анализ целевой аудитории"
    )
    audience_pains: list[str] = Field(
        description="Основные боли целевой аудитории"
    )
    content_pillars: list[str] = Field(
        description="Основные контентные направления"
    )
    plan: list[ContentPlanItem] = Field(
        description="Контент-план на семь дней"
    )


class PostDraft(BaseModel):
    post_id: int
    topic: str

    hook: str = Field(
        description="Первый абзац или цепляющий заголовок"
    )
    body: str = Field(
        description="Основной текст публикации"
    )
    cta: str = Field(
        description="Призыв к действию"
    )


class CopywriterResult(BaseModel):
    posts: list[PostDraft]


class EditorIssue(BaseModel):
    post_id: int

    category: Literal[
        "content_plan",
        "style",
        "clarity",
        "grammar",
        "cta",
        "fact",
        "format",
        "other",
    ]

    quote: str = Field(
        description=(
            "Точная цитата из текущей версии поста, "
            "к которой относится замечание"
        )
    )

    problem: str = Field(
        description="Что именно не так"
    )

    recommendation: str = Field(
        description="Как Copywriter должен это исправить"
    )

class EditorResult(BaseModel):
    decision: Literal["APPROVED", "REVISE"]

    summary: str = Field(
        description="Краткое резюме редакторской проверки"
    )

    issues: list[EditorIssue] = Field(
        default_factory=list
    )

class PublisherDecoration(BaseModel):
    post_id: int

    emoji: str = Field(
        default="",
        description=(
            "Необязательный один уместный emoji "
            "для оформления публикации"
        ),
    )

    hashtags: list[str] = Field(
        description="От 2 до 5 релевантных хештегов",
        min_length=2,
        max_length=5,
    )


class PublisherFormattingResult(BaseModel):
    posts: list[PublisherDecoration]

class PublishedPost(BaseModel):
    post_id: int
    topic: str
    text: str
    hashtags: list[str]


class PublisherResult(BaseModel):
    posts: list[PublishedPost]