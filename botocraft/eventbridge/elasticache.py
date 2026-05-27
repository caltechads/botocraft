from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Protocol

from botocraft.eventbridge.base import EventBridgeEvent
from botocraft.eventbridge.common import (
    CloudTrailApiCallMixin,
    event_summary,
    first_resource,
)
from botocraft.eventbridge.raw import (
    ElasticacheCacheCreatedEvent as RawCacheCreatedEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheCacheCreationFailedEvent as RawCacheCreationFailedEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheCacheDeletedEvent as RawCacheDeletedEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheCacheLimitApproachingEvent as RawCacheLimitApproachingEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheCacheUpdatedEvent as RawCacheUpdatedEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheCacheUpdateFailedEvent as RawCacheUpdateFailedEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheSnapshotCopyFailedEvent as RawSnapshotCopyFailedEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheSnapshotCreatedEvent as RawSnapshotCreatedEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheSnapshotCreationFailedEvent as RawSnapshotCreationFailedEvent,
)
from botocraft.eventbridge.raw import (
    ElasticacheSnapshotExportFailedEvent as RawSnapshotExportFailedEvent,
)
from botocraft.eventbridge.raw.elasticache import (
    aws_api_call_via_cloudtrail as raw_elasticache,
)

if TYPE_CHECKING:
    from botocraft.services.elasticache import CacheCluster, ReplicationGroup


class ElastiCacheNotificationDetailProtocol(Protocol):
    """Structural type for native ElastiCache notification detail payloads."""

    #: ElastiCache resource ARN named by the event.
    SourceArn: str
    #: ElastiCache source identifier such as a cluster ID.
    SourceIdentifier: str
    #: ElastiCache source type such as ``cache-cluster``.
    SourceType: str
    #: Human-readable ElastiCache event message.
    Message: str


class ElastiCacheNotificationEvent:
    """
    Shared conveniences for native ``aws.elasticache`` EventBridge wrappers.
    """

    #: Native ElastiCache notification detail payload.
    detail: ElastiCacheNotificationDetailProtocol

    #: EventBridge resource ARNs attached by raw event models.
    resources: list[str]
    #: Boto3 session attached by :class:`~botocraft.eventbridge.factory.EventFactory`.
    session: object | None

    @property
    def source_arn(self) -> str:
        """
        Return the ElastiCache resource ARN named in the event detail.

        Returns:
            Source ARN from the event detail payload.

        """
        return self.detail.SourceArn

    @property
    def source_identifier(self) -> str:
        """
        Return the ElastiCache source identifier from the event detail.

        Returns:
            Source identifier such as a cluster or replication group ID.

        """
        return self.detail.SourceIdentifier

    @property
    def source_type(self) -> str:
        """
        Return the ElastiCache source type from the event detail.

        Returns:
            Source type string such as ``cache-cluster`` or ``replication-group``.

        """
        return self.detail.SourceType

    @property
    def message(self) -> str:
        """
        Return the human-readable ElastiCache event message.

        Returns:
            Message text from the event detail payload.

        """
        return self.detail.Message

    @property
    def resource_arn(self) -> str | None:
        """
        Return the first EventBridge resource ARN when present.

        Returns:
            First resource ARN from the envelope, otherwise ``None``.

        """
        return first_resource(self.resources)

    @cached_property
    def cache_cluster(self) -> CacheCluster | None:
        """
        Return related cache cluster when session and source type allow lookup.

        Side Effects:
            Performs a ``DescribeCacheClusters`` request with attached boto3
            session when the source type indicates a cache cluster.

        Returns:
            Loaded cache cluster model when available, otherwise ``None``.

        """
        source_type = self.source_type.lower()
        if "cache-cluster" not in source_type and "serverless-cache" not in source_type:
            return None
        if self.session is None:
            return None

        from botocraft.services.elasticache import CacheCluster

        return CacheCluster.objects.using(self.session).get(
            CacheClusterId=self.source_identifier,
        )

    @cached_property
    def replication_group(self) -> ReplicationGroup | None:
        """
        Return related replication group when session and source type allow lookup.

        Side Effects:
            Performs a ``DescribeReplicationGroups`` request with attached boto3
            session when the source type indicates a replication group.

        Returns:
            Loaded replication group model when available, otherwise ``None``.

        """
        if "replication-group" not in self.source_type.lower():
            return None
        if self.session is None:
            return None

        from botocraft.services.elasticache import ReplicationGroup

        return ReplicationGroup.objects.using(self.session).get(
            ReplicationGroupId=self.source_identifier,
        )


def _notification_summary(event_name: str, event: ElastiCacheNotificationEvent) -> str:
    """
    Build readable summary for native ElastiCache notification wrappers.

    Args:
        event_name: Human-readable event name shown in the summary.
        event: Notification event instance being rendered.

    Returns:
        Compact summary string for the event.

    """
    return event_summary(
        event_name,
        event,
        source_identifier=event.source_identifier,
        source_type=event.source_type,
        message=event.message,
    )


class ElastiCacheCacheCreatedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawCacheCreatedEvent,
):
    """EventBridge wrapper for ElastiCache cache-created notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the cache-created event.

        """
        return _notification_summary("ElastiCache Cache Created", self)


class ElastiCacheCacheCreationFailedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawCacheCreationFailedEvent,
):
    """EventBridge wrapper for ElastiCache cache-creation-failed notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the cache-creation-failed event.

        """
        return _notification_summary("ElastiCache Cache Creation Failed", self)


class ElastiCacheCacheDeletedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawCacheDeletedEvent,
):
    """EventBridge wrapper for ElastiCache cache-deleted notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the cache-deleted event.

        """
        return _notification_summary("ElastiCache Cache Deleted", self)


class ElastiCacheCacheLimitApproachingEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawCacheLimitApproachingEvent,
):
    """EventBridge wrapper for ElastiCache cache-limit-approaching notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the cache-limit-approaching event.

        """
        return _notification_summary("ElastiCache Cache Limit Approaching", self)


class ElastiCacheCacheUpdateFailedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawCacheUpdateFailedEvent,
):
    """EventBridge wrapper for ElastiCache cache-update-failed notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the cache-update-failed event.

        """
        return _notification_summary("ElastiCache Cache Update Failed", self)


class ElastiCacheCacheUpdatedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawCacheUpdatedEvent,
):
    """EventBridge wrapper for ElastiCache cache-updated notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the cache-updated event.

        """
        return _notification_summary("ElastiCache Cache Updated", self)


class ElastiCacheSnapshotCopyFailedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawSnapshotCopyFailedEvent,
):
    """EventBridge wrapper for ElastiCache snapshot-copy-failed notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the snapshot-copy-failed event.

        """
        return _notification_summary("ElastiCache Snapshot Copy Failed", self)


class ElastiCacheSnapshotCreatedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawSnapshotCreatedEvent,
):
    """EventBridge wrapper for ElastiCache snapshot-created notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the snapshot-created event.

        """
        return _notification_summary("ElastiCache Snapshot Created", self)


class ElastiCacheSnapshotCreationFailedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawSnapshotCreationFailedEvent,
):
    """EventBridge wrapper for ElastiCache snapshot-creation-failed notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the snapshot-creation-failed event.

        """
        return _notification_summary("ElastiCache Snapshot Creation Failed", self)


class ElastiCacheSnapshotExportFailedEvent(
    ElastiCacheNotificationEvent,
    EventBridgeEvent,
    RawSnapshotExportFailedEvent,
):
    """EventBridge wrapper for ElastiCache snapshot-export-failed notifications."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the snapshot-export-failed event.

        """
        return _notification_summary("ElastiCache Snapshot Export Failed", self)


class ElastiCacheAWSAPICallViaCloudTrailEvent(
    CloudTrailApiCallMixin,
    EventBridgeEvent,
    raw_elasticache.ElasticacheAWSAPICallViaCloudTrailEvent,
):
    """EventBridge wrapper for ElastiCache API calls delivered via CloudTrail."""

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the CloudTrail API call event.

        """
        return event_summary(
            "ElastiCache AWS API Call Via CloudTrail",
            self,
            event_source=self.detail.eventSource,
            api_call_name=self.detail.eventName,
        )


#: Declarative mapping from EventBridge source/detail-type pairs to wrappers.
EVENT_CLASS_MAP = {
    ("aws.elasticache", "Cache Created"): ElastiCacheCacheCreatedEvent,
    (
        "aws.elasticache",
        "Cache Creation Failed",
    ): ElastiCacheCacheCreationFailedEvent,
    ("aws.elasticache", "Cache Deleted"): ElastiCacheCacheDeletedEvent,
    (
        "aws.elasticache",
        "Cache Limit Approaching",
    ): ElastiCacheCacheLimitApproachingEvent,
    ("aws.elasticache", "Cache Update Failed"): ElastiCacheCacheUpdateFailedEvent,
    ("aws.elasticache", "Cache Updated"): ElastiCacheCacheUpdatedEvent,
    (
        "aws.elasticache",
        "Snapshot Copy Failed",
    ): ElastiCacheSnapshotCopyFailedEvent,
    ("aws.elasticache", "Snapshot Created"): ElastiCacheSnapshotCreatedEvent,
    (
        "aws.elasticache",
        "Snapshot Creation Failed",
    ): ElastiCacheSnapshotCreationFailedEvent,
    (
        "aws.elasticache",
        "Snapshot Export Failed",
    ): ElastiCacheSnapshotExportFailedEvent,
    (
        "aws.elasticache",
        "AWS API Call via CloudTrail",
    ): ElastiCacheAWSAPICallViaCloudTrailEvent,
}
