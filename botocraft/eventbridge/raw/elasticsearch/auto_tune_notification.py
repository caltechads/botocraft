from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field

from .common import ElasticsearchNotificationDetail  # noqa: TC001


class ElasticsearchAutoTuneNotificationEvent(BaseModel):
    """
    Top-level EventBridge envelope for ``aws.es`` Auto-Tune notifications.
    """

    #: Detailed Auto-Tune notification payload.
    detail: ElasticsearchNotificationDetail
    #: EventBridge envelope version.
    version: str
    #: EventBridge event identifier.
    id: str
    #: EventBridge detail type.
    detail_type: str = Field(..., alias="detail-type")
    #: Event source identifier.
    source: str
    #: AWS account ID that emitted the event.
    account: str
    #: EventBridge timestamp.
    time: datetime
    #: AWS region where EventBridge emitted the event.
    region: str
    #: EventBridge resource list.
    resources: list[str]
