from __future__ import annotations

from botocraft.eventbridge.base import EventBridgeEvent
from botocraft.eventbridge.common import event_summary
from botocraft.eventbridge.raw import (
    ElasticsearchAutoTuneNotificationEvent as RawElasticsearchAutoTuneNotificationEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchSoftwareUpdateNotificationEvent as RawESSWUpdateEvent,
)
from botocraft.eventbridge.search import SearchServiceDomainEvent


class ElasticsearchSoftwareUpdateNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawESSWUpdateEvent,
):
    """
    Friendly wrapper for legacy ``Amazon ES`` software update notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for software update event.

        """
        return event_summary(
            "Elasticsearch Software Update Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class ElasticsearchAutoTuneNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawElasticsearchAutoTuneNotificationEvent,
):
    """
    Friendly wrapper for legacy ``Amazon ES`` Auto-Tune notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for Auto-Tune event.

        """
        return event_summary(
            "Elasticsearch Auto-Tune Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


#: Declarative mapping from EventBridge source/detail-type pairs to wrappers.
EVENT_CLASS_MAP = {
    (
        "aws.es",
        "Amazon ES Service Software Update Notification",
    ): ElasticsearchSoftwareUpdateNotificationEvent,
    (
        "aws.es",
        "Amazon ES Auto-Tune Notification",
    ): ElasticsearchAutoTuneNotificationEvent,
}
