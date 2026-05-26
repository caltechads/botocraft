import json

import pytest

from botocraft.eventbridge.factory import EventFactory


def _event_payload(detail_type: str, detail: dict[str, object]) -> dict[str, object]:
    return {
        "version": "0",
        "id": "01234567-0123-0123-0123-0123456789ab",
        "detail-type": detail_type,
        "source": "aws.es",
        "account": "123456789012",
        "time": "2024-11-16T00:58:37Z",
        "region": "us-east-1",
        "resources": ["arn:aws:es:us-east-1:123456789012:domain/test-domain"],
        "detail": detail,
    }


@pytest.mark.parametrize(
    ("payload", "expected_type_name"),
    [
        (
            _event_payload(
                "Amazon ES Service Software Update Notification",
                {
                    "event": "Service Software Update",
                    "status": "Cancelled",
                    "severity": "Informational",
                    "description": "Legacy update event.",
                },
            ),
            "ElasticsearchSoftwareUpdateNotificationEvent",
        ),
        (
            _event_payload(
                "Amazon ES Auto-Tune Notification",
                {
                    "event": "Auto-Tune Event",
                    "status": "Completed",
                    "severity": "Informational",
                    "description": "Legacy auto-tune event.",
                    "completionTime": "2024-11-16T01:00:00Z",
                },
            ),
            "ElasticsearchAutoTuneNotificationEvent",
        ),
    ],
)
def test_event_factory_builds_elasticsearch_legacy_events(
    payload: dict[str, object],
    expected_type_name: str,
) -> None:
    event = EventFactory().new(json.dumps(payload))

    assert type(event).__name__ == expected_type_name
