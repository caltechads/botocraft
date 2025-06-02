from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import List

from pydantic import BaseModel, Field


class ECSServiceDeploymentStateChange(BaseModel):
    """
    The main body of the ECS Service Deployment State Change event.
    """

    #: The name of the event
    eventName: str
    #: The type of the event
    eventType: str
    #: The service deployment ID.
    #:
    #: .. note::
    #:    This is not the same as the
    #:    py:class:`~botocraft.services.ecs.ServiceDeployment` ARN.  Not sure
    #:    what this is, really.
    deploymentId: str
    #: The time the Service Deployment was created
    updatedAt: datetime
    #: The reason the Service Deployment was started
    reason: str | None = None


class ECSServiceDeploymentStateChangeEvent(BaseModel):
    """
    An ECS Service Deployment State Change Event class.

    .. important::

        There's no schema in the EventBridge schema registry for this event,
        so this is a best effort attempt to create a schema for it manually.
    """

    #: Where the meat of the event is
    detail: ECSServiceDeploymentStateChange
    #: The human readable name of the event
    detail_type: str = Field(..., alias="detail-type")
    #: The resources the event applies to.  This will be a list of ARNs
    resources: List[str]
    #: The ID of the event
    id: str
    #: The source of the event, e.g. "aws.ecs"
    source: str
    #: The region the event was generated in
    region: str
    #: The time the event was generated, in UTC
    time: datetime
    #: The version of the schema for the event
    version: str
    #: The account the event was generated in
    account: str
