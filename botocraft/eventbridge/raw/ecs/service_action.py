from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import List

from pydantic import BaseModel, Field


class ECSServiceAction(BaseModel):
    """
    The main body of the ECS Service Action event.
    """

    #: A list of ARNs of the capacity providers associated with the service.
    capacityProviderArns: List[str] | None = None
    #: The ARN of the cluster associated with the service.
    clusterArn: str
    #: The time the event was created
    createdAt: datetime | None = None
    #: The name of the event
    eventName: str
    #: The type of the event
    eventType: str
    #: A reason for the event
    reason: str | None = None
    #: The desired count of tasks in the service
    desiredCount: float | None = None
    #: The container port of the service  (What if I have multiple ports?)
    containerPort: float | None = None
    #: The list of task ARNs associated with the service
    taskArns: List[str] | None = None
    #: The list of task set ARNs associated with the service
    taskSetArns: List[str] | None = None
    #: The list of container instance ARNs associated with the service
    containerInstanceArns: List[str] | None = None
    #: The list of EC2 instance IDs associated with the service
    ec2InstanceIds: List[str] | None = None
    #: The list of target group ARNs associated with the service
    targetGroupArns: List[str] | None = None
    #: The list of service registry ARNs associated with the service
    serviceRegistryArns: List[str] | None = None
    #: Not sure what this is
    targets: List[str] | None = None


class ECSServiceActionEvent(BaseModel):
    #: Where the meat of the event is
    detail: ECSServiceAction
    #: The account the event was generated in
    account: str
    #: The human readable name of the event
    detail_type: str = Field(..., alias="detail-type")
    #: The ID of the event
    id: str
    #: The region the event was generated in
    region: str
    #: The resources the event applies to.  This will be a list of ARNs
    resources: List[str]
    #: The source of the event, e.g. "aws.ecs"
    source: str
    #: The time the event was generated, in UTC
    time: datetime
    #: The version of the schema for the event
    version: str
