from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field

from .common import ElasticsearchCloudTrailDetail  # noqa: TC001


class ElasticsearchAWSAPICallViaCloudTrailEvent(BaseModel):
    """
    Top-level EventBridge envelope for ``aws.es`` CloudTrail API call events.
    """

    #: Detailed CloudTrail API call payload.
    detail: ElasticsearchCloudTrailDetail
    #: EventBridge detail type.
    detail_type: str = Field(..., alias="detail-type")
    #: EventBridge resource list.
    resources: list[str]
    #: EventBridge event identifier.
    id: str
    #: Event source identifier.
    source: str
    #: EventBridge timestamp.
    time: datetime
    #: AWS region where EventBridge emitted the event.
    region: str
    #: EventBridge envelope version.
    version: str
    #: AWS account ID that emitted the event.
    account: str
