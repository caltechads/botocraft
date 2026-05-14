from __future__ import annotations

from pydantic import BaseModel, Field


class Detail(BaseModel):
    """
    Detail payload for this SSM event.
    """

    #: Event field ``description``.
    description: str
    #: Event field ``name``.
    name: str
    #: Event field ``operation``.
    operation: str
    #: Event field ``type``.
    type: str


class SSMParameterStoreChangeEvent(BaseModel):
    """
    Raw EventBridge payload for this SSM event.
    """

    #: AWS account that emitted the event.
    account: str
    #: Event-specific detail payload from Systems Manager.
    detail: Detail
    #: EventBridge detail type for the event.
    detail_type: str = Field(..., alias="detail-type")
    #: Unique identifier for the EventBridge event.
    id: str
    #: AWS region where the event was emitted.
    region: str
    #: Resources associated with the event.
    resources: list[str]
    #: Event source identifier.
    source: str
    #: Timestamp when EventBridge recorded the event.
    time: str
    #: EventBridge payload version.
    version: str
