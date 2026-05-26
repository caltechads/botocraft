from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, Field


class ACMCertificateRotated(BaseModel):
    """
    Detail payload for ACM certificate rotation notifications.

    AWS documents this event with an empty ``detail`` object; optional fields may
    appear in real traffic when ACM adds new detail keys.
    """


class ACMACMCertificateRotatedEvent(BaseModel):
    """
    Top-level EventBridge envelope for ACM certificate rotation events.
    """

    #: Rotation detail payload (often empty).
    detail: ACMCertificateRotated
    #: EventBridge detail type.
    detail_type: str = Field(..., alias="detail-type")
    #: EventBridge event identifier.
    id: str
    #: Event source identifier.
    source: str
    #: EventBridge timestamp.
    time: AwareDatetime
    #: AWS region where EventBridge emitted the event.
    region: str
    #: EventBridge resource list.
    resources: list[str]
    #: EventBridge envelope version.
    version: str
    #: AWS account ID that emitted the event.
    account: str
