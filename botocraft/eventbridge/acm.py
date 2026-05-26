from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from botocraft.eventbridge.base import EventBridgeEvent
from botocraft.eventbridge.common import (
    CloudTrailApiCallMixin,
    event_summary,
    first_resource,
)
from botocraft.eventbridge.raw import (
    ACMACMCertificateApproachingExpirationEvent as RawApproachingExpirationEvent,
)
from botocraft.eventbridge.raw import (
    ACMACMCertificateAvailableEvent as RawAvailableEvent,
)
from botocraft.eventbridge.raw import (
    ACMACMCertificateExpiredEvent as RawExpiredEvent,
)
from botocraft.eventbridge.raw import (
    ACMACMCertificateRenewalActionRequiredEvent as RawRenewalActionRequiredEvent,
)
from botocraft.eventbridge.raw import (
    ACMACMCertificateRevokedByCAEvent as RawRevokedByCAEvent,
)
from botocraft.eventbridge.raw import (
    ACMACMCertificateRevokedEvent as RawRevokedEvent,
)
from botocraft.eventbridge.raw import (
    ACMACMCertificateRotatedEvent as RawRotatedEvent,
)
from botocraft.eventbridge.raw.acm import (
    aws_api_call_via_cloudtrail as raw_acm,
)

if TYPE_CHECKING:
    from botocraft.services.acm import ACMCertificate


class ACMCertificateEvent:
    """
    Shared conveniences for native ``aws.acm`` EventBridge wrappers.
    """

    #: EventBridge resource ARNs attached by raw event models.
    resources: list[str]
    #: Boto3 session attached by :class:`~botocraft.eventbridge.factory.EventFactory`.
    session: object | None

    @property
    def certificate_arn(self) -> str | None:
        """
        Return certificate ARN from the first event resource entry.

        Returns:
            Certificate ARN when present, otherwise ``None``.

        """
        return first_resource(self.resources)

    @cached_property
    def certificate(self) -> ACMCertificate | None:
        """
        Return related ACM certificate when session and ARN are available.

        Side Effects:
            Performs a ``DescribeCertificate`` request with attached boto3 session
            when a certificate ARN is present.

        Returns:
            Loaded certificate model when available, otherwise ``None``.

        """
        certificate_arn = self.certificate_arn
        if certificate_arn is None or self.session is None:
            return None

        from botocraft.services.acm import ACMCertificate

        return ACMCertificate.objects.using(self.session).get(certificate_arn)


class ACMCertificateApproachingExpirationEvent(
    ACMCertificateEvent,
    EventBridgeEvent,
    RawApproachingExpirationEvent,
):
    """
    EventBridge wrapper for ACM certificate approaching-expiration notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the approaching-expiration event.

        """
        return event_summary(
            "ACM Certificate Approaching Expiration",
            self,
            days_to_expiry=self.detail.DaysToExpiry,
        )


class ACMCertificateAvailableEvent(
    ACMCertificateEvent,
    EventBridgeEvent,
    RawAvailableEvent,
):
    """
    EventBridge wrapper for ACM certificate available notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the certificate-available event.

        """
        return event_summary(
            "ACM Certificate Available",
            self,
            action=self.detail.Action,
            common_name=self.detail.CommonName,
            certificate_type=self.detail.CertificateType,
        )


class ACMCertificateExpiredEvent(
    ACMCertificateEvent,
    EventBridgeEvent,
    RawExpiredEvent,
):
    """
    EventBridge wrapper for ACM certificate expired notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the certificate-expired event.

        """
        return event_summary(
            "ACM Certificate Expired",
            self,
            common_name=self.detail.CommonName,
            certificate_type=self.detail.CertificateType,
        )


class ACMCertificateRenewalActionRequiredEvent(
    ACMCertificateEvent,
    EventBridgeEvent,
    RawRenewalActionRequiredEvent,
):
    """
    EventBridge wrapper for ACM certificate renewal action required notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the renewal-action-required event.

        """
        return event_summary(
            "ACM Certificate Renewal Action Required",
            self,
            common_name=self.detail.CommonName,
            renewal_status_reason=self.detail.RenewalStatusReason,
            days_to_expiry=self.detail.DaysToExpiry,
        )


class ACMCertificateRevokedEvent(
    ACMCertificateEvent,
    EventBridgeEvent,
    RawRevokedEvent,
):
    """
    EventBridge wrapper for ACM certificate revoked notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the certificate-revoked event.

        """
        return event_summary(
            "ACM Certificate Revoked",
            self,
            common_name=self.detail.CommonName,
            certificate_type=self.detail.CertificateType,
        )


class ACMCertificateRevokedByCAEvent(
    ACMCertificateEvent,
    EventBridgeEvent,
    RawRevokedByCAEvent,
):
    """
    EventBridge wrapper for ACM certificate revoked-by-CA notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the certificate-revoked-by-CA event.

        """
        return event_summary(
            "ACM Certificate Revoked By CA",
            self,
            common_name=self.detail.CommonName,
            revocation_reason=self.detail.RevocationReason,
        )


class ACMCertificateRotatedEvent(
    ACMCertificateEvent,
    EventBridgeEvent,
    RawRotatedEvent,
):
    """
    EventBridge wrapper for ACM certificate rotated notifications.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the certificate-rotated event.

        """
        return event_summary(
            "ACM Certificate Rotated",
            self,
        )


class ACMAWSAPICallViaCloudTrailEvent(
    CloudTrailApiCallMixin,
    ACMCertificateEvent,
    EventBridgeEvent,
    raw_acm.AcmAWSAPICallViaCloudTrailEvent,
):
    """
    EventBridge wrapper for ACM API calls delivered via CloudTrail.
    """

    def __str__(self) -> str:
        """
        Return readable event summary.

        Returns:
            Compact string summary for the CloudTrail API call event.

        """
        return event_summary(
            "ACM AWS API Call Via CloudTrail",
            self,
            event_source=self.detail.eventSource,
            api_call_name=self.detail.eventName,
        )


#: Declarative mapping from EventBridge source/detail-type pairs to wrappers.
EVENT_CLASS_MAP = {
    (
        "aws.acm",
        "ACM Certificate Approaching Expiration",
    ): ACMCertificateApproachingExpirationEvent,
    ("aws.acm", "ACM Certificate Available"): ACMCertificateAvailableEvent,
    ("aws.acm", "ACM Certificate Expired"): ACMCertificateExpiredEvent,
    (
        "aws.acm",
        "ACM Certificate Renewal Action Required",
    ): ACMCertificateRenewalActionRequiredEvent,
    ("aws.acm", "ACM Certificate Revoked"): ACMCertificateRevokedEvent,
    (
        "aws.acm",
        "ACM Certificate Revoked By CA",
    ): ACMCertificateRevokedByCAEvent,
    ("aws.acm", "ACM Certificate Rotated"): ACMCertificateRotatedEvent,
    ("aws.acm", "AWS API Call via CloudTrail"): ACMAWSAPICallViaCloudTrailEvent,
}
