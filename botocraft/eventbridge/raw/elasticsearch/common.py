from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict


class ElasticsearchNotificationDetail(BaseModel):
    """
    Flexible detail payload for docs-derived ``aws.es`` service events.

    AWS documents the supported ``detail-type`` values for Amazon OpenSearch
    Service and shows example payloads with a stable core of event metadata plus
    a few optional timestamps. Extra fields stay allowed because some
    event-specific payloads include additional attributes beyond the examples.
    """

    #: Allow additional documented-but-variable keys across ``aws.es`` events.
    model_config = ConfigDict(extra="allow")

    #: Service-specific event family or operation name.
    event: str
    #: Current lifecycle status for the notification.
    status: str
    #: Severity level attached by the service.
    severity: str
    #: Human-readable description from the service.
    description: str
    #: Scheduled execution time when the service reports one.
    scheduleTime: datetime | None = None
    #: Start time for in-progress operations when present.
    startTime: datetime | None = None
    #: Completion timestamp when the operation has finished.
    completionTime: datetime | None = None


class ElasticsearchCloudTrailDetail(BaseModel):
    """
    Detail payload for ``aws.es`` events delivered through CloudTrail.
    """

    #: Allow CloudTrail operation-specific request and response payload fields.
    model_config = ConfigDict(extra="allow")

    #: Version of the CloudTrail event format.
    eventVersion: str
    #: Identity context for the principal that made the API call.
    userIdentity: dict[str, object] | None = None
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
    #: Request payload recorded by CloudTrail.
    requestParameters: dict[str, object] | None = None
    #: Response payload recorded by CloudTrail.
    responseElements: dict[str, object] | None = None
    #: Request identifier assigned by the service.
    requestID: str | None = None
    #: Unique CloudTrail event identifier.
    eventID: str | None = None
    #: Whether the API call was read-only.
    readOnly: bool | None = None
    #: Resource descriptors attached to the CloudTrail detail payload.
    resources: list[dict[str, object]] | None = None
    #: CloudTrail event type, such as ``AwsApiCall``.
    eventType: str | None = None
    #: Whether CloudTrail marked the event as a management event.
    managementEvent: bool | None = None
    #: Recipient account ID for the event.
    recipientAccountId: str | None = None
    #: CloudTrail event category, such as ``Management``.
    eventCategory: str | None = None
