from __future__ import annotations

from typing import TYPE_CHECKING

from botocraft.eventbridge.base import EventBridgeEvent
from botocraft.eventbridge.common import (
    CloudTrailApiCallMixin,
    event_summary,
    first_resource,
)
from botocraft.eventbridge.raw.elbv2 import (
    aws_api_call_via_cloudtrail as raw_elbv2,
)

if TYPE_CHECKING:
    from botocraft.services.elbv2 import LoadBalancer


class Elbv2AWSAPICallViaCloudTrailEvent(
    CloudTrailApiCallMixin,
    EventBridgeEvent,
    raw_elbv2.Elbv2AWSAPICallViaCloudTrailEvent,
):
    """
    EventBridge wrapper for ELBv2 API calls delivered via CloudTrail.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the CloudTrail API call event.

        """
        return event_summary(
            "ELBv2 AWS API Call Via CloudTrail",
            self,
            event_source=self.detail.eventSource,
            api_call_name=self.detail.eventName,
        )

    @property
    def load_balancer_arn(self) -> str | None:
        """
        Return load balancer ARN from the first EventBridge resource entry.

        Returns:
            Load balancer ARN when present, otherwise ``None``.

        """
        resource_arn = first_resource(self.resources)
        if resource_arn is None:
            return None
        if ":loadbalancer/" in resource_arn:
            return resource_arn
        return None

    @property
    def load_balancer(self) -> LoadBalancer | None:
        """
        Return related load balancer when session and ARN are available.

        Side Effects:
            Performs a ``DescribeLoadBalancers`` request with attached boto3
            session when a load balancer ARN is present.

        Returns:
            Loaded load balancer model when available, otherwise ``None``.

        """
        load_balancer_arn = self.load_balancer_arn
        if load_balancer_arn is None or self.session is None:
            return None

        from botocraft.services.elbv2 import LoadBalancer

        return LoadBalancer.objects.using(self.session).get(load_balancer_arn)


#: Declarative mapping from EventBridge source/detail-type pairs to wrappers.
EVENT_CLASS_MAP = {
    (
        "aws.elasticloadbalancing",
        "AWS API Call via CloudTrail",
    ): Elbv2AWSAPICallViaCloudTrailEvent,
}
