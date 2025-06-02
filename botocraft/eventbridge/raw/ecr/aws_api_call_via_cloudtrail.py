from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AWSAPICallViaCloudTrailItem(BaseModel):
    """
    Represents a resource involved in an AWS API call via CloudTrail.  Contains
    identifiers for AWS resources that were accessed or modified during the API
    call.
    """

    #: The AWS account ID that owns the resource
    accountId: str
    #: The Amazon Resource Name (ARN) of the resource
    ARN: str


class RequestParametersItem(BaseModel):
    """
    Represents an image identifier in an ECR API request.  Used to specify which
    container image is being referenced in operations like BatchGetImage.
    """

    #: The tag of the container image
    imageTag: str


class SessionIssuer(BaseModel):
    """
    Represents the entity that issued the session in the user identity context.
    Contains information about the IAM entity (user or role) that created the
    session.
    """

    #: The AWS account ID that owns the entity
    accountId: str
    #: The unique identifier of the entity
    principalId: str
    #: The type of the entity (e.g., "Role", "User")
    type: str
    #: The ARN of the entity
    arn: str
    #: The name of the entity
    userName: str


class Attributes(BaseModel):
    """
    Represents attributes of the session used for the API call.  Includes
    security-related information about the session.
    """

    #: Indicates whether multi-factor authentication was used to create the session
    mfaAuthenticated: str
    #: The timestamp when the session was created
    creationDate: datetime


class RequestParameters(BaseModel):
    """
    Represents the parameters of an ECR API request.
    Contains the details of what was requested in the API call.
    """

    #: The media types that the API client accepts
    acceptedMediaTypes: List[str]
    #: The AWS account ID that owns the ECR registry
    registryId: str
    #: The name of the ECR repository being accessed
    repositoryName: str
    #: The list of image identifiers being requested
    imageIds: List[RequestParametersItem]


class SessionContext(BaseModel):
    """
    Represents the session context for a user identity.
    Contains detailed information about the session used to make the API call.
    """

    #: Federation data if the session was created through web identity federation
    webIdFederationData: Dict[str, Any]
    #: Information about the entity that issued the session
    sessionIssuer: SessionIssuer
    #: Session attributes like MFA status and creation time
    attributes: Attributes


class UserIdentity(BaseModel):
    """
    Represents the identity of the user that performed the API call.  Contains
    information about the AWS principal (user, role, or service) that made the
    request.
    """

    #: The context of the session used for the API call
    sessionContext: SessionContext
    #: The access key ID used to sign the request
    accessKeyId: str
    #: The AWS account ID that the user belongs to
    accountId: str
    #: The unique identifier of the principal
    principalId: str
    #: The type of the identity (e.g., "AssumedRole", "IAMUser")
    type: str
    #: The ARN of the principal
    arn: str
    #: The AWS service that made the request, if applicable
    invokedBy: str


class AWSAPICallViaCloudTrail(BaseModel):
    """
    Represents the details of an AWS API call as recorded by CloudTrail.
    Contains comprehensive information about the API request, including who made
    it, what was requested, and the response.
    """

    #: The parameters sent with the API request
    requestParameters: RequestParameters
    #: The identity of the user that made the API call
    userIdentity: UserIdentity
    #: The unique identifier of the event
    eventID: str
    #: The AWS region where the request was made
    awsRegion: str
    #: The version of the CloudTrail event format
    eventVersion: str
    #: The response elements returned by the API
    responseElements: Dict[str, Any]
    #: The IP address where the request originated from
    sourceIPAddress: str
    #: The AWS service that the request was made to (e.g., "ecr.amazonaws.com")
    eventSource: str
    #: The resources involved in the API call
    resources: List[AWSAPICallViaCloudTrailItem]
    #: The user agent of the client that made the request
    userAgent: str
    #: The type of the event (e.g., "AwsApiCall")
    eventType: str
    #: The request ID of the API call
    requestID: str
    #: The timestamp when the API call was made
    eventTime: datetime
    #: The name of the API call (e.g., "BatchGetImage")
    eventName: str


class ECRAWSAPICallViaCloudTrailEvent(BaseModel):
    """
    Represents a complete AWS CloudTrail event as delivered by EventBridge.
    Wraps the CloudTrail API call details with EventBridge metadata.
    """

    #: The detailed information about the API call
    detail: AWSAPICallViaCloudTrail
    #: The human-readable type of the event (e.g., "AWS API Call via CloudTrail")
    detail_type: str = Field(..., alias="detail-type")
    #: The AWS resources involved in the event
    resources: List[str]
    #: The unique identifier of the event
    id: str
    #: The source of the event (e.g., "aws.ecr")
    source: str
    #: The timestamp when the event was generated
    time: datetime
    #: The AWS region where the event occurred
    region: str
    #: The version of the event schema
    version: str
    #: The AWS account ID where the event occurred
    account: str
