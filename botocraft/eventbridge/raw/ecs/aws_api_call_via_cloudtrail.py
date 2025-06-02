from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RequestParametersItem(BaseModel):
    """Represents a placement constraint or other parameter for an ECS request."""

    #: The expression for the placement constraint
    expression: str
    #: The type of the placement constraint
    type: str


class RequestParametersItem1(BaseModel):
    """Represents a container definition in the ECS request parameters."""

    #: The name of the container
    containerName: str
    #: The exit code of the container, if it has exited
    exitCode: float | None = None
    #: The network bindings for the container
    networkBindings: List[Dict[str, Any]]
    #: The status of the container
    status: str


class ResponseElementsItemItem1(BaseModel):
    """Represents a container definition in the ECS response elements."""

    #: The Docker image used by the container
    image: str
    #: The network interfaces attached to the container
    networkInterfaces: List[Dict[str, Any]]
    #: The memory allocated to the container
    memory: str | None = None
    #: The ARN of the task this container belongs to
    taskArn: str
    #: The name of the container
    name: str
    #: The CPU units allocated to the container
    cpu: str
    #: The ARN of the container
    containerArn: str
    #: The current status of the container
    lastStatus: str


class AwsvpcConfiguration(BaseModel):
    """Represents the VPC configuration for an ECS task."""

    #: Whether to assign a public IP address to the task
    assignPublicIp: str | None = None
    #: The subnets in which to launch the task
    subnets: List[str] | None = None


class OverridesItem(BaseModel):
    """Represents overrides for a container in the ECS request."""

    #: The resource requirements for the container
    resourceRequirements: List[Dict[str, Any]] | None = None
    #: The environment variables for the container
    environment: List[Dict[str, Any]] | None = None
    #: The memory override for the container
    memory: float | None = None
    #: The name of the container to override
    name: str
    #: The CPU override for the container
    cpu: float | None = None
    #: The command override for the container
    command: List[str] | None = None


class SessionIssuer(BaseModel):
    """Represents the issuer of a session in the user identity context."""

    #: The account ID of the session issuer
    accountId: str
    #: The principal ID of the session issuer
    principalId: str
    #: The type of the session issuer
    type: str
    #: The ARN of the session issuer
    arn: str
    #: The username of the session issuer
    userName: str


class Attributes(BaseModel):
    """Represents session attributes, such as MFA status and creation date."""

    #: Whether MFA was used for authentication
    mfaAuthenticated: str
    #: When the session was created
    creationDate: datetime


class Overrides1Item(BaseModel):
    """Represents overrides for a container in the ECS response."""

    #: The resource requirements for the container
    resourceRequirements: List[Dict[str, Any]] | None = None
    #: The environment variables for the container
    environment: List[Dict[str, Any]] | None = None
    #: The memory override for the container
    memory: float | None = None
    #: The name of the container to override
    name: str
    #: The CPU override for the container
    cpu: float | None = None
    #: The command override for the container
    command: List[str] | None = None


class ResponseElementsItemItemItem(BaseModel):
    """Represents a detail item for an ECS response element attachment."""

    #: The name of the detail
    name: str
    #: The value of the detail
    value: str


class NetworkConfiguration(BaseModel):
    """Represents the network configuration for an ECS task."""

    #: The AWS VPC configuration for the task
    awsvpcConfiguration: AwsvpcConfiguration | None = None


class Overrides(BaseModel):
    """Represents container overrides for an ECS request."""

    #: The overrides for individual containers
    containerOverrides: List[OverridesItem] | None = None


class SessionContext(BaseModel):
    """Represents the session context for a user identity."""

    #: Web identity federation data, if applicable
    webIdFederationData: Dict[str, Any] | None = None
    #: Information about the entity that issued the session
    sessionIssuer: SessionIssuer
    #: Session attributes like MFA status
    attributes: Attributes


class Overrides1(BaseModel):
    """Represents container and inference accelerator overrides for an ECS response."""

    #: The overrides for individual containers
    containerOverrides: List[Overrides1Item]
    #: The overrides for inference accelerators
    inferenceAcceleratorOverrides: List[Dict[str, Any]]


class ResponseElementsItemItem(BaseModel):
    """Represents an attachment for an ECS response element."""

    #: The details of the attachment
    details: List[ResponseElementsItemItemItem]
    #: The ID of the attachment
    id: str
    #: The type of the attachment
    type: str
    #: The status of the attachment
    status: str


class RequestParameters(BaseModel):
    """Represents the parameters sent in an ECS API request via CloudTrail."""

    #: The network configuration for the task
    networkConfiguration: NetworkConfiguration | None = None
    #: Overrides for the task
    overrides: Overrides | None = None
    #: Placement constraints for the task
    placementConstraints: List[RequestParametersItem] | None = None
    #: The cluster on which to run the task
    cluster: str | None = None
    #: The reason for the request
    reason: str | None = None
    #: When task execution stopped, if applicable
    executionStoppedAt: str | None = None
    #: When image pulling stopped, if applicable
    pullStoppedAt: str | None = None
    #: The entity that started the task
    startedBy: str | None = None
    #: When image pulling started, if applicable
    pullStartedAt: str | None = None
    #: The number of tasks to start
    count: float | None = None
    #: The task ID or ARN
    task: str | None = None
    #: The container instance on which to run the task
    containerInstance: str | None = None
    #: The containers to include in the task
    containers: List[RequestParametersItem1] | None = None
    #: The task definition to use
    taskDefinition: str | None = None
    #: Whether to enable ECS managed tags
    enableECSManagedTags: bool | None = None
    #: The launch type for the task (EC2 or FARGATE)
    launchType: str | None = None
    #: The desired status of the task
    status: str | None = None


class UserIdentity(BaseModel):
    """Represents the identity of the user that initiated the ECS API call."""

    #: The context of the session
    sessionContext: SessionContext
    #: The access key ID used for the request
    accessKeyId: str
    #: The AWS account ID of the user
    accountId: str
    #: The principal ID of the user
    principalId: str
    #: The type of the identity
    type: str
    #: The ARN of the identity
    arn: str
    #: The AWS service that invoked the API call, if applicable
    invokedBy: str | None = None


class ResponseElementsItem(BaseModel):
    """Represents a single ECS task or resource returned in the ECS API response."""

    #: Task overrides
    overrides: Overrides1
    #: The task memory
    memory: str
    #: Attachments to the task
    attachments: List[ResponseElementsItemItem]
    #: The ARN of the role or user that submitted the request
    startedBy: str | None = None
    #: The ARN of the task
    taskArn: str
    #: The CPU of the task
    cpu: str
    #: The version number of the task
    version: float
    #: The tags associated with the task
    tags: List[Dict[str, Any]]
    #: When the task was created
    createdAt: str
    #: The ARN of the cluster in which the task is running
    clusterArn: str
    #: The ARN of the task definition for the task
    taskDefinitionArn: str
    #: The platform version (FARGATE only)
    platformVersion: str | None = None
    #: A list of container definitions
    containers: List[ResponseElementsItemItem1]
    #: The ARN of the container instance on which the task is running
    #: (Fargate tasks have no container instance)
    containerInstanceArn: str | None = None
    #: The last status of the task
    lastStatus: str
    #: The desired status of the task
    desiredStatus: str
    #: The ECS group for the task
    group: str
    #: The launch type of the task (e.g., EC2, FARGATE)
    launchType: str


class ResponseElements(BaseModel):
    """Represents the response elements returned by the ECS API call."""

    #: The endpoint URL
    endpoint: str | None = None
    #: Any failures that occurred during the API call
    failures: List[Dict[str, Any]] | None = None
    #: The telemetry endpoint URL
    telemetryEndpoint: str | None = None
    #: The tasks returned in the response
    tasks: List[ResponseElementsItem] | None = None
    #: The acknowledgment message, if any
    acknowledgment: str | None = None


class AWSAPICallViaCloudTrail(BaseModel):
    """
    Represents the detail of an AWS API call event as recorded by CloudTrail for ECS.
    """

    #: The API response
    responseElements: ResponseElements
    #: The API request
    requestParameters: RequestParameters
    #: The identity of the user that initiated the event
    userIdentity: UserIdentity
    #: The ID of the event
    eventID: str
    #: The name of the region in which the event occurred
    awsRegion: str
    #: The version of the event
    eventVersion: str
    #: The source IP of the user that initiated the event
    sourceIPAddress: str
    #: The source of the event
    eventSource: str
    #: The UserAgent of the request
    userAgent: str
    #: The event type
    eventType: str
    #: The request ID of the event in CloudTrail
    requestID: str
    #: The time the event was created
    eventTime: datetime
    #: The name of the event
    eventName: str


class ECSAWSAPICallViaCloudTrailEvent(BaseModel):
    """
    Represents a full ECS API call event as received from EventBridge, wrapping
    the CloudTrail detail.
    """

    #: Where the meat of the event is
    detail: AWSAPICallViaCloudTrail
    #: The human readable name of the event
    detail_type: str = Field(..., alias="detail-type")
    #: The resources the event applies to. This will be a list of ARNs
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
