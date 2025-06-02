from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import List

from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    """
    Version information about the ECS agent and docker.
    """

    #: The version of docker on this container instance
    dockerVersion: str | None = None
    #: The hash of the ECS agent image
    agentHash: str | None = None
    #: The version of the ECS agent
    agentVersion: str | None = None


class Detail(BaseModel):
    """
    A detail of an :py:class:`AttachmentDetails` object.
    """

    #: The name of the detail
    name: str | None = None
    #: The value of the detail
    value: str | None = None


class AttachmentDetails(BaseModel):
    """
    Details of an attachment, used to represent the details of an attachment in
    the context of an ECS container instance state change event.
    """

    #: The attachment ID
    id: str | None = None
    #: The type of the attachment
    type: str | None = None
    #: The status of the attachment
    status: str | None = None
    #: The details of the attachment
    details: List[Detail] | None = None


class AttributesDetails(BaseModel):
    """
    Details of an attribute.
    """

    #: The name of the attribute
    name: str | None = None
    #: The value of the attribute
    value: str | None = None


class ResourceDetails(BaseModel):
    """
    Details of a resource (CPU, Memory, etc).

    .. note::

        Only one of the following values will be set, depending on the type of
        resource.  The type of resource is specified in the `type` field.
        The type of resource is one of the following:
        - `INTEGER`: :py:attr:`integerValue`
        - `LONG`: :py:attr:`longValue`
        - `DOUBLE`: :py:attr:`doubleValue`
        - `STRING`: :py:attr:`stringSetValue`

    """

    #: An integer value of the resource
    integerValue: float | None = None
    #: A long value of the resource
    longValue: float | None = None
    #: A double value of the resource
    doubleValue: float | None = None
    #: The name of the resource
    name: str
    #: A string value of the resource
    stringSetValue: List[str] | None = None
    #: The type of the resource
    type: str


class ECSContainerInstanceStateChange(BaseModel):
    """
    That main body of the ECS Container Instance State Change event.
    """

    #: Info about docker and the ECS agent
    versionInfo: VersionInfo
    #: The ID of the EC2 instance
    ec2InstanceId: str | None = None
    #: Any attachments associated with the container instance
    attachments: List[AttachmentDetails] | None = None
    #: The list of registered resources associated with the container instance
    #: e.g. CPU, memory, etc.
    registeredResources: List[ResourceDetails]
    #: The list of remaining resources associated with the container instance
    #: e.g. CPU, memory, etc.
    remainingResources: List[ResourceDetails]
    #: How many tasks are running on the container instance
    runningTasksCount: float | None = None
    #: The time the container instance was registered
    registeredAt: datetime | None = None
    #: Whether the container instance is connected to the ECS agent
    agentConnected: bool
    #: Whether the ECS agent needs to be updated
    agentUpdateStatus: str | None = None
    #: not sure what this is
    version: float
    #: The number of tasks that are pending on the container instance
    pendingTasksCount: float | None = None
    #: The ARN of the ECS cluster the container instance is registered to
    clusterArn: str
    #: The attributes associated with the container instance
    attributes: List[AttributesDetails] | None = None
    #: The ARN of the container instance
    containerInstanceArn: str
    #: The status of the container instance
    status: str
    #: A reason for the status of the container instance
    statusReason: str | None = None
    #: The time the container instance was updated
    updatedAt: datetime
    #: not sure what this is
    accountType: str | None = None


class ECSContainerInstanceStateChangeEvent(BaseModel):
    #: Where the meat of the event is
    detail: ECSContainerInstanceStateChange
    #: The human readable name of the event
    detail_type: str = Field(..., alias="detail-type")
    #: The resources the event applies to.  This will be a list of ARNs
    resources: List[str]
    #: The ID of the event
    id: str
    #: The source of the event, e.g. "aws.ecs"
    source: str
    #: The time the event was generated, in UTC
    time: datetime
    #: The region the event was generated in
    region: str
    #: The version of the schema for the event
    version: str
    #: The account the event was generated in
    account: str
