from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from pydantic import BaseModel, Field


class ACMAWSAPICallViaCloudTrail(BaseModel):
    """
    Detail payload for an ACM API call delivered via CloudTrail.

    The EventBridge reference documents the event-pattern contract for this
    event family but not a service-specific full schema, so flexible mapping
    fields remain ``dict[str, Any]`` where request and response shapes vary by
    API operation.
    """

    #: Version of the CloudTrail event format.
    eventVersion: str
    #: Identity context for the principal that made the API call.
    userIdentity: dict[str, Any] | None = None
    #: Timestamp when the API call happened.
    eventTime: datetime
    #: AWS service endpoint that received the API call.
    eventSource: str
    #: API operation name recorded by CloudTrail.
    eventName: str
    #: AWS region where the API call was made.
    awsRegion: str
    #: Source IP address for the request.
    sourceIPAddress: str | None = None
    #: User agent reported for the caller.
    userAgent: str | None = None
    #: Request payload recorded by CloudTrail for the API operation.
    requestParameters: dict[str, Any] | None = None
    #: Response payload recorded by CloudTrail for the API operation.
    responseElements: dict[str, Any] | None = None
    #: Request identifier assigned by the service.
    requestID: str | None = None
    #: Unique CloudTrail event identifier.
    eventID: str | None = None
    #: Whether the API call was read-only.
    readOnly: bool | None = None
    #: Resource descriptors attached to the CloudTrail detail payload.
    resources: list[dict[str, Any]] | None = None
    #: CloudTrail event type, such as ``AwsApiCall``.
    eventType: str | None = None
    #: Service API version when CloudTrail records one.
    apiVersion: str | None = None
    #: Whether CloudTrail marked the event as a management event.
    managementEvent: bool | None = None
    #: Recipient account ID for the event.
    recipientAccountId: str | None = None
    #: CloudTrail event category, such as ``Management``.
    eventCategory: str | None = None
    #: TLS metadata when CloudTrail records it.
    tlsDetails: dict[str, Any] | None = None
    #: Console-session marker when CloudTrail records it.
    sessionCredentialFromConsole: str | None = None


class AcmAWSAPICallViaCloudTrailEvent(BaseModel):
    """
    Top-level EventBridge envelope for ACM CloudTrail API call events.
    """

    #: Detailed CloudTrail API call payload.
    detail: ACMAWSAPICallViaCloudTrail
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
