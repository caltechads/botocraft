from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, Field


class Detail(BaseModel):
    """
    Detail payload for this SSM event.
    """

    #: Event field ``created-by``.
    created_by: str = Field(..., alias="created-by")
    #: Event field ``created-time``.
    created_time: AwareDatetime = Field(..., alias="created-time")
    #: Event source identifier.
    source: str
    #: Event field ``status``.
    status: str
    #: Event field ``ops-item-id``.
    ops_item_id: str = Field(..., alias="ops-item-id")
    #: Event field ``title``.
    title: str
    #: Event field ``ops-item-type``.
    ops_item_type: str = Field(..., alias="ops-item-type")
    #: Event field ``description``.
    description: str


class SSMOpsItemCreateEvent(BaseModel):
    """
    Raw EventBridge payload for this SSM event.
    """

    #: EventBridge payload version.
    version: str
    #: Unique identifier for the EventBridge event.
    id: str
    #: EventBridge detail type for the event.
    detail_type: str = Field(..., alias="detail-type")
    #: Event source identifier.
    source: str
    #: AWS account that emitted the event.
    account: str
    #: Timestamp when EventBridge recorded the event.
    time: AwareDatetime
    #: AWS region where the event was emitted.
    region: str
    #: Resources associated with the event.
    resources: list[str]
    #: Event-specific detail payload from Systems Manager.
    detail: Detail
