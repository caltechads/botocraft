import json

import pytest
from pydantic import BaseModel

from botocraft.eventbridge.elasticache import (
    ElastiCacheAWSAPICallViaCloudTrailEvent,
    ElastiCacheCacheCreatedEvent,
    ElastiCacheCacheCreationFailedEvent,
    ElastiCacheCacheDeletedEvent,
    ElastiCacheCacheLimitApproachingEvent,
    ElastiCacheCacheUpdateFailedEvent,
    ElastiCacheCacheUpdatedEvent,
    ElastiCacheNotificationEvent,
    ElastiCacheSnapshotCopyFailedEvent,
    ElastiCacheSnapshotCreatedEvent,
    ElastiCacheSnapshotCreationFailedEvent,
    ElastiCacheSnapshotExportFailedEvent,
)
from botocraft.eventbridge.factory import EventFactory

_CLUSTER_ARN = (
    "arn:aws:elasticache:us-east-1:123456789012:cluster:my-cluster"
)


def _notification_detail(
    *,
    source_type: str = "cache-cluster",
    message: str = "Cache is created and ready to use.",
) -> dict[str, object]:
    return {
        "EventCategories": ["creation"],
        "EventID": "01234567-0123-0123-0123-012345678901",
        "Message": message,
        "SourceArn": _CLUSTER_ARN,
        "SourceIdentifier": "my-cluster",
        "SourceType": source_type,
    }


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
        "source": "aws.elasticache",
        "account": "123456789012",
        "time": "2024-11-16T00:58:37Z",
        "region": "us-east-1",
        "resources": resources or [_CLUSTER_ARN],
        "detail": detail,
    }


@pytest.mark.parametrize(
    ("detail_type", "expected_type"),
    [
        ("Cache Created", ElastiCacheCacheCreatedEvent),
        ("Cache Creation Failed", ElastiCacheCacheCreationFailedEvent),
        ("Cache Deleted", ElastiCacheCacheDeletedEvent),
        ("Cache Limit Approaching", ElastiCacheCacheLimitApproachingEvent),
        ("Cache Update Failed", ElastiCacheCacheUpdateFailedEvent),
        ("Cache Updated", ElastiCacheCacheUpdatedEvent),
        ("Snapshot Copy Failed", ElastiCacheSnapshotCopyFailedEvent),
        ("Snapshot Created", ElastiCacheSnapshotCreatedEvent),
        ("Snapshot Creation Failed", ElastiCacheSnapshotCreationFailedEvent),
        ("Snapshot Export Failed", ElastiCacheSnapshotExportFailedEvent),
    ],
)
def test_event_factory_builds_elasticache_notification_event(
    detail_type: str,
    expected_type: type[ElastiCacheNotificationEvent],
) -> None:
    event = EventFactory().new(
        json.dumps(
            _event_payload(
                detail_type,
                _notification_detail(),
            )
        )
    )
    assert isinstance(event, expected_type)
    assert event.source_identifier == "my-cluster"
    assert event.source_type == "cache-cluster"
    assert event.message == "Cache is created and ready to use."


def test_event_factory_builds_elasticache_cloudtrail_event() -> None:
    payload = _event_payload(
        "AWS API Call via CloudTrail",
        {
            "eventVersion": "1.11",
            "eventTime": "2026-03-07T00:51:06Z",
            "eventSource": "elasticache.amazonaws.com",
            "eventName": "CreateCacheCluster",
            "awsRegion": "us-east-1",
            "requestParameters": {
                "cacheClusterId": "my-cluster",
                "engine": "redis",
            },
        },
    )
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, ElastiCacheAWSAPICallViaCloudTrailEvent)


def test_elasticache_cloudtrail_event_parsed_request() -> None:
    payload = _event_payload(
        "AWS API Call via CloudTrail",
        {
            "eventVersion": "1.11",
            "eventTime": "2026-03-07T00:51:06Z",
            "eventSource": "elasticache.amazonaws.com",
            "eventName": "CreateCacheCluster",
            "awsRegion": "us-east-1",
            "requestParameters": {
                "cacheClusterId": "my-cluster",
                "engine": "redis",
            },
        },
    )
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, ElastiCacheAWSAPICallViaCloudTrailEvent)
    parsed = event.parsed_request()
    assert isinstance(parsed, BaseModel)
    assert parsed.CacheClusterId == "my-cluster"  # type: ignore[attr-defined]


def test_elasticache_cloudtrail_event_parsed_request_unknown_operation() -> None:
    payload = _event_payload(
        "AWS API Call via CloudTrail",
        {
            "eventVersion": "1.11",
            "eventTime": "2026-03-07T00:51:06Z",
            "eventSource": "elasticache.amazonaws.com",
            "eventName": "NotARealOperationName",
            "awsRegion": "us-east-1",
            "requestParameters": {"cacheClusterId": "my-cluster"},
        },
    )
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, ElastiCacheAWSAPICallViaCloudTrailEvent)
    assert event.parsed_request() == {"cacheClusterId": "my-cluster"}
