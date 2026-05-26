import json

import pytest

from botocraft.eventbridge.factory import EventFactory


def _event_payload(
    detail_type: str,
    detail: dict[str, object],
    *,
    resources: list[str] | None = None,
) -> dict[str, object]:
    return {
        "version": "0",
        "id": "01234567-0123-0123-0123-0123456789ab",
        "detail-type": detail_type,
        "source": "aws.es",
        "account": "123456789012",
        "time": "2024-11-16T00:58:37Z",
        "region": "us-east-1",
        "resources": resources
        or ["arn:aws:es:us-east-1:123456789012:domain/test-domain"],
        "detail": detail,
    }


@pytest.mark.parametrize(
    ("payload", "expected_type_name"),
    [
        (
            _event_payload(
                "Amazon OpenSearch Service Software Update Notification",
                {
                    "event": "Service Software Update",
                    "status": "Available",
                    "severity": "Informational",
                    "description": "Update available.",
                },
            ),
            "OpenSearchSoftwareUpdateNotificationEvent",
        ),
        (
            _event_payload(
                "Amazon OpenSearch Service Auto-Tune Notification",
                {
                    "event": "Auto-Tune Event",
                    "status": "Started",
                    "severity": "Informational",
                    "description": "Applying tuning changes.",
                    "startTime": "2024-11-16T00:58:37Z",
                    "scheduleTime": "2024-11-16T00:00:00Z",
                },
            ),
            "OpenSearchAutoTuneNotificationEvent",
        ),
        (
            _event_payload(
                "Amazon OpenSearch Service Cluster Status Notification",
                {
                    "event": "Low Disk Space",
                    "status": "Warning",
                    "severity": "Medium",
                    "description": "Low disk space warning.",
                },
            ),
            "OpenSearchClusterStatusNotificationEvent",
        ),
        (
            _event_payload(
                "Domain Error Notification",
                {
                    "event": "KMS Key Inaccessible",
                    "status": "Error",
                    "severity": "High",
                    "description": "KMS key inaccessible.",
                },
            ),
            "OpenSearchDomainErrorNotificationEvent",
        ),
        (
            _event_payload(
                "Amazon OpenSearch Service Notification",
                {
                    "event": "Domain Isolation Notification",
                    "status": "Error",
                    "severity": "High",
                    "description": "Domain isolated.",
                },
            ),
            "OpenSearchNotificationEvent",
        ),
        (
            _event_payload(
                "Amazon OpenSearch Service Maintenance Update",
                {
                    "event": "Service Maintenance",
                    "status": "Completed",
                    "severity": "Informational",
                    "description": "Maintenance completed.",
                },
            ),
            "OpenSearchMaintenanceUpdateEvent",
        ),
        (
            _event_payload(
                "Amazon OpenSearch Service Domain Update Notification",
                {
                    "event": "Domain Update Validation",
                    "status": "Failed",
                    "severity": "High",
                    "description": "Validation failure.",
                },
            ),
            "OpenSearchDomainUpdateNotificationEvent",
        ),
        (
            _event_payload(
                "Amazon OpenSearch Service VPC Endpoint Notification",
                {
                    "event": "VPC Endpoint Create Validation",
                    "status": "Failed",
                    "severity": "High",
                    "description": "Endpoint validation failed.",
                },
            ),
            "OpenSearchVPCEndpointNotificationEvent",
        ),
        (
            _event_payload(
                "AWS API Call via CloudTrail",
                {
                    "eventVersion": "1.10",
                    "userIdentity": {"type": "IAMUser"},
                    "eventTime": "2024-11-16T00:58:37Z",
                    "eventSource": "es.amazonaws.com",
                    "eventName": "UpdateDomainConfig",
                    "awsRegion": "us-east-1",
                    "sourceIPAddress": "127.0.0.1",
                    "userAgent": "aws-cli/2.0",
                    "requestParameters": {"domainName": "test-domain"},
                    "responseElements": None,
                    "requestID": "request-id",
                    "eventID": "event-id",
                    "readOnly": False,
                    "resources": [],
                    "eventType": "AwsApiCall",
                    "managementEvent": True,
                    "recipientAccountId": "123456789012",
                    "eventCategory": "Management",
                },
            ),
            "OpenSearchAWSAPICallViaCloudTrailEvent",
        ),
    ],
)
def test_event_factory_builds_opensearch_events(
    payload: dict[str, object],
    expected_type_name: str,
) -> None:
    event = EventFactory().new(json.dumps(payload))

    assert type(event).__name__ == expected_type_name


def test_opensearch_event_exposes_domain_name() -> None:
    event = EventFactory().new(
        json.dumps(
            _event_payload(
                "Amazon OpenSearch Service Notification",
                {
                    "event": "High Shard Count",
                    "status": "Warning",
                    "severity": "Low",
                    "description": "Shard count warning.",
                },
                resources=[
                    "arn:aws:es:us-east-1:123456789012:domain/example-domain",
                ],
            )
        )
    )

    assert not isinstance(event, dict)
    assert type(event).__name__ == "OpenSearchNotificationEvent"
    assert event.domain_name == "example-domain"
