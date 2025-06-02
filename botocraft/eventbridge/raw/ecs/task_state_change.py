from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field, RootModel


class Details(BaseModel):
    """
    A details of a :py:class:`AttachmentDetails` object in the context of
    a ECS task state change event.
    """

    #: The name of the detail
    name: str | None = None
    #: The value of the detail
    value: str | None = None


class AttachmentDetails(BaseModel):
    """
    Details of the attachment, used to represent the details of an attachment in
    the context of an ECS task state change event.
    """

    #: The attachment ID
    id: str | None = None
    #: The type of the attachment
    type: str | None = None
    #: The status of the attachment
    status: str | None = None
    #: The details of the attachment
    details: list[Details] = Field(default_factory=list)


class AttributesDetails(BaseModel):
    """
    The details of an attribute in the context of an ECS task state change event.
    """

    #: The name of the attribute
    name: str | None = None
    #: The value of the attribute
    value: str | None = None


class NetworkInterfaceDetails(BaseModel):
    """
    The details of a network interface in the context of an ECS task state change event.
    """

    #: The private IPv4 address of the network interface
    privateIpv4Address: str | None = None
    # The private IPv6 address of the network interface
    ipv6Address: str | None = None
    #: The attachment ID of the network interface
    attachmentId: str | None = None


class NetworkBindingDetails(BaseModel):
    """
    Network binding details in the context of an ECS task state change event.
    """

    #: The host binding IP address
    bindIP: str | None = None
    #: The host binding protocol
    protocol: str | None = None
    #: The container port
    containerPort: float | None = None
    #: The host port
    hostPort: float | None = None


class Environment(RootModel[dict[str, str]]):
    pass


class ContainerDetails(BaseModel):
    """
    Details about a container in the task definition in the context of an ECS
    task state change event.
    """

    #: The full URL for the image used to run the container
    image: str | None = None
    #: The digest of the image used to run the container
    imageDigest: str | None = None
    #: The list of network interfaces attached to the container
    networkInterfaces: list[NetworkInterfaceDetails] = Field(default_factory=list)
    #: The list of network bindings for the container
    networkBindings: list[NetworkBindingDetails] = Field(default_factory=list)
    #: The minimum amount of memory required to the container
    memory: str | None = None
    #: The maximum amount of memory allowed to the container
    memoryReservation: str | None = None
    #: The ARN of the task that the container is part of
    taskArn: str
    #: The name of the container
    name: str
    #: The exit code of the container if it has stopped
    exitCode: float | None = None
    #: The maximum amount of CPU allowed to the container
    cpu: str | None = None
    #: The ARN of the container
    containerArn: str
    #: The last status of the container
    lastStatus: str
    #: The runtime ID of the container
    runtimeId: str | None = None
    #: The reason why the container has :py:attr:`lastStatus`
    reason: str | None = None
    #: A list of GPU IDs that the container is using
    gpuIds: list[str] | None = None


class OverridesItem(BaseModel):
    """
    Overrides for a single container in the task definition.
    """

    #: Overrides to environment variables
    environment: list[Environment] = Field(default_factory=list)
    #: Overrides to container memory
    memory: float | None = None
    #: The name of the container these overrides apply to
    name: str
    # Overrides to container CPU
    cpu: float | None = None
    #: Overrides to container command
    command: list[str] | None = None


class Overrides(BaseModel):
    """
    Overrides to the task definition in the context of an ECS task state change
    event.  These are specified in the ``RunTask`` API call.
    """

    #: Container overrides
    containerOverrides: list[OverridesItem] = Field(default_factory=list)


class ECSTaskStateChange(BaseModel):
    """
    The main details of the ECS task state change event.  This is the ``detail``
    field.  in the json of the event.
    """

    #: Container overrides
    overrides: Overrides
    #: If the task is stopped, the time it was stopped in UTC
    executionStoppedAt: datetime | None = None
    #: The task maximum amount of memory
    memory: str | None = None
    #: A list of attachments to the task
    attachments: list[AttachmentDetails] = Field(default_factory=list)
    #: A list of attributes for the task
    attributes: list[AttributesDetails] = Field(default_factory=list)
    #: The time the images for the started being pulled, in UTC
    pullStartedAt: datetime | None = None
    #: The ARN of the task
    taskArn: str
    #: The time the task was started, in UTC
    startedAt: datetime | None = None
    #: The time the task was created, in UTC
    createdAt: datetime
    #: The ARN of the cluster the task is running in
    clusterArn: str
    connectivity: str | None = None
    #: The platform version of the ECS infrastructure
    platformVersion: str | None = None
    #: The ARN of the container instance the task is running on, if any
    #: (Fargate tasks do not have a container instance)
    containerInstanceArn: str | None = None
    #: The launch type of the task
    #: (EC2 or Fargate)
    launchType: str | None = None
    #: ? not sure what this is
    group: str | None = None
    #: If the task was updated, the time it was updated in UTC
    updatedAt: datetime
    #: The AWS code describing why the task was stopped
    stopCode: str | None = None
    #: THe time the pulls of all the images for the task ended, in UTC
    pullStoppedAt: datetime | None = None
    #: The time connectivity was established, in UTC
    connectivityAt: datetime | None = None
    #: The ARN of the IAM role or user used that started the task
    startedBy: str | None = None
    #: The maximum amount of CPU allowed to the task
    cpu: str | None = None
    #: ? not sure what this is
    version: float
    #: The time we received the stop task request, in UTC
    stoppingAt: datetime | None = None
    #: The time the task was stopped, in UTC
    stoppedAt: datetime | None = None
    #: The ARN of the task definition used to start the task
    taskDefinitionArn: str
    #: The reason why the task was stopped
    stoppedReason: str | None = None
    #: The list of containers in the task
    containers: list[ContainerDetails] = Field(default_factory=list)
    #: The desired status of the task
    desiredStatus: str
    #: The current status of the task
    lastStatus: str
    #: The availability zone the task is running in
    availabilityZone: str | None = None


class ECSTaskStateChangeEvent(BaseModel):
    #: Where the meat of the event is
    detail: ECSTaskStateChange
    #: The human readable name of the event
    detail_type: str = Field(..., alias="detail-type")
    #: The resources the event applies to.  This will be a list of ARNs
    resources: list[str]
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
