from typing_extensions import NotRequired

from langgraph.graph import MessagesState

from ai_smm.schemas import (
    CopywriterResult,
    EditorResult,
    PublisherResult,
    StrategistResult,
)


class SMMState(MessagesState):
    # Исходное задание
    task: str
    niche: str
    target_audience: str
    social_network: str

    verified_product_facts: list[str]
    
    selected_post_ids: list[int]

    # Результаты агентов
    strategist_result: NotRequired[StrategistResult]
    copywriter_result: NotRequired[CopywriterResult]
    editor_result: NotRequired[EditorResult]
    publisher_result: NotRequired[PublisherResult]

    # Управление циклом Editor -> Copywriter
    revision_count: int
    max_revisions: int
    editor_approved: bool
    forced_publish: bool
