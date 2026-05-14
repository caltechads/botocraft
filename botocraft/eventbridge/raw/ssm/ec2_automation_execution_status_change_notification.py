from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, Field


class Detail(BaseModel):
    """
    Detail payload for this SSM event.
    """

    #: Event field ``ExecutionId``.
    ExecutionId: str
    #: Event field ``Definition``.
    Definition: str
    #: Event field ``DefinitionVersion``.
    DefinitionVersion: float
    #: Event field ``Status``.
    Status: str
    #: Event field ``StartTime``.
    StartTime: str
    #: Event field ``EndTime``.
    EndTime: str
    #: Event field ``Time``.
    Time: float
    #: Event field ``ExecutedBy``.
    ExecutedBy: str


class SSMEC2AutomationExecutionStatusChangeNotificationEvent(BaseModel):
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
