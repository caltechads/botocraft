from __future__ import annotations

from botocraft.eventbridge.base import EventBridgeEvent
from botocraft.eventbridge.common import CloudTrailApiCallMixin, event_summary
from botocraft.eventbridge.raw import (
    ElasticsearchAutoTuneNotificationEvent as RawOSAutoTuneEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchAWSAPICallViaCloudTrailEvent as RawOSAWSAPICallEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchClusterStatusNotificationEvent as RawOSClusterStatusEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchDomainErrorNotificationEvent as RawOSDomainErrorEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchDomainUpdateNotificationEvent as RawOSDomainUpdateEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchMaintenanceUpdateEvent as RawOSMaintenanceEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchNotificationEvent as RawOSNotificationEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchSoftwareUpdateNotificationEvent as RawOSSWUpdateEvent,
)
from botocraft.eventbridge.raw import (
    ElasticsearchVPCEndpointNotificationEvent as RawOSVPCEndpointEvent,
)
from botocraft.eventbridge.search import SearchServiceDomainEvent


class OpenSearchSoftwareUpdateNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSSWUpdateEvent,
):
    """
    Friendly wrapper for ``Amazon OpenSearch Service`` software updates.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for software update event.

        """
        return event_summary(
            "OpenSearch Software Update Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class OpenSearchAutoTuneNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSAutoTuneEvent,
):
    """
    Friendly wrapper for ``Amazon OpenSearch Service`` Auto-Tune events.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for Auto-Tune event.

        """
        return event_summary(
            "OpenSearch Auto-Tune Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class OpenSearchClusterStatusNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSClusterStatusEvent,
):
    """
    Friendly wrapper for OpenSearch cluster status notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for cluster status event.

        """
        return event_summary(
            "OpenSearch Cluster Status Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class OpenSearchDomainErrorNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSDomainErrorEvent,
):
    """
    Friendly wrapper for OpenSearch domain error notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for domain error event.

        """
        return event_summary(
            "OpenSearch Domain Error Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class OpenSearchNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSNotificationEvent,
):
    """
    Friendly wrapper for generic OpenSearch notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for generic notification event.

        """
        return event_summary(
            "OpenSearch Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class OpenSearchMaintenanceUpdateEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSMaintenanceEvent,
):
    """
    Friendly wrapper for OpenSearch maintenance update events.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for maintenance event.

        """
        return event_summary(
            "OpenSearch Maintenance Update",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class OpenSearchDomainUpdateNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSDomainUpdateEvent,
):
    """
    Friendly wrapper for OpenSearch domain update notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for domain update event.

        """
        return event_summary(
            "OpenSearch Domain Update Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class OpenSearchVPCEndpointNotificationEvent(
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSVPCEndpointEvent,
):
    """
    Friendly wrapper for OpenSearch VPC endpoint notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for VPC endpoint event.

        """
        return event_summary(
            "OpenSearch VPC Endpoint Notification",
            self,
            domain_name=self.domain_name,
            event=self.detail.event,
            status=self.detail.status,
            severity=self.detail.severity,
        )


class OpenSearchAWSAPICallViaCloudTrailEvent(
    CloudTrailApiCallMixin,
    SearchServiceDomainEvent,
    EventBridgeEvent,
    RawOSAWSAPICallEvent,
):
    """
    Friendly wrapper for OpenSearch CloudTrail API call events.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for CloudTrail API call event.

        """
        return event_summary(
            "OpenSearch AWS API Call via CloudTrail",
            self,
            domain_name=self.domain_name,
            event_name=self.detail.eventName,
            event_source=self.detail.eventSource,
        )


#: Declarative mapping from EventBridge source/detail-type pairs to wrappers.
EVENT_CLASS_MAP = {
    (
        "aws.es",
        "Amazon OpenSearch Service Software Update Notification",
    ): OpenSearchSoftwareUpdateNotificationEvent,
    (
        "aws.es",
        "Amazon OpenSearch Service Auto-Tune Notification",
    ): OpenSearchAutoTuneNotificationEvent,
    (
        "aws.es",
        "Amazon OpenSearch Service Cluster Status Notification",
    ): OpenSearchClusterStatusNotificationEvent,
    (
        "aws.es",
        "Domain Error Notification",
    ): OpenSearchDomainErrorNotificationEvent,
    (
        "aws.es",
        "Amazon OpenSearch Service Notification",
    ): OpenSearchNotificationEvent,
    (
        "aws.es",
        "Amazon OpenSearch Service Maintenance Update",
    ): OpenSearchMaintenanceUpdateEvent,
    (
        "aws.es",
        "Amazon OpenSearch Service Domain Update Notification",
    ): OpenSearchDomainUpdateNotificationEvent,
    (
        "aws.es",
        "Amazon OpenSearch Service VPC Endpoint Notification",
    ): OpenSearchVPCEndpointNotificationEvent,
    (
        "aws.es",
        "AWS API Call via CloudTrail",
    ): OpenSearchAWSAPICallViaCloudTrailEvent,
}
