from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, Field


class CalendarStateChange(BaseModel):
    """
    Detail payload for an SSM calendar state change event.
    """

    #: Timestamp when the calendar entered the reported state.
    atTime: AwareDatetime
    #: Timestamp for the next scheduled calendar state transition.
    nextTransitionTime: AwareDatetime
    #: Current state of the calendar.
    state: str


class SSMCalendarStateChangeEvent(BaseModel):
    """
    Raw EventBridge payload for an SSM calendar state change event.
    """

    #: AWS account that emitted the event.
    account: str
    #: Event-specific detail payload from Systems Manager.
    detail: CalendarStateChange
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
    time: AwareDatetime
    #: EventBridge payload version.
    version: str
