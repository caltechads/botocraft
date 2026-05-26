import json
from unittest.mock import MagicMock, patch

import pytest

from botocraft.eventbridge.acm import (
    ACMAWSAPICallViaCloudTrailEvent,
    ACMCertificateApproachingExpirationEvent,
    ACMCertificateAvailableEvent,
    ACMCertificateExpiredEvent,
    ACMCertificateRenewalActionRequiredEvent,
    ACMCertificateRevokedByCAEvent,
    ACMCertificateRevokedEvent,
    ACMCertificateRotatedEvent,
)
from botocraft.eventbridge.factory import EventFactory

_CERTIFICATE_ARN = (
    "arn:aws:acm:us-east-1:123456789012:certificate/61f50cd4-45b9-4259-b049-d0a53682fa4b"
)


def _event_payload(
    detail_type: str,
    detail: dict[str, object],
) -> dict[str, object]:
    return {
        "version": "0",
        "id": "01234567-0123-0123-0123-0123456789ab",
        "detail-type": detail_type,
        "source": "aws.acm",
        "account": "123456789012",
        "time": "2020-09-30T06:51:08Z",
        "region": "us-east-1",
        "resources": [_CERTIFICATE_ARN],
        "detail": detail,
    }


@pytest.mark.parametrize(
    ("payload", "expected_type"),
    [
        (
            _event_payload(
                "ACM Certificate Approaching Expiration",
                {"DaysToExpiry": 31, "Exportable": False},
            ),
            ACMCertificateApproachingExpirationEvent,
        ),
        (
            _event_payload(
                "ACM Certificate Available",
                {
                    "Action": "ISSUANCE",
                    "CertificateCreatedDate": "2019-12-22T18:43:48Z",
                    "CertificateExpirationDate": "2020-12-22T18:43:48Z",
                    "CertificateType": "AMAZON_ISSUED",
                    "CommonName": "example.com",
                    "DaysToExpiry": 198,
                    "DomainValidationMethod": "DNS",
                    "Exported": False,
                    "InUse": True,
                },
            ),
            ACMCertificateAvailableEvent,
        ),
        (
            _event_payload(
                "ACM Certificate Expired",
                {
                    "CertificateCreatedDate": "2018-12-22T18:43:48Z",
                    "CertificateExpirationDate": "2019-12-22T18:43:48Z",
                    "CertificateType": "AMAZON_ISSUED",
                    "CommonName": "example.com",
                    "DomainValidationMethod": "DNS",
                    "Exported": False,
                    "InUse": True,
                },
            ),
            ACMCertificateExpiredEvent,
        ),
        (
            _event_payload(
                "ACM Certificate Renewal Action Required",
                {
                    "CertificateCreatedDate": "2018-12-22T18:43:48Z",
                    "CertificateExpirationDate": "2019-12-22T18:43:48Z",
                    "CertificateType": "AMAZON_ISSUED",
                    "CommonName": "example.com",
                    "DaysToExpiry": 30,
                    "DomainValidationMethod": "DNS",
                    "Exported": False,
                    "InUse": True,
                    "RenewalStatusReason": "CAA_ERROR",
                },
            ),
            ACMCertificateRenewalActionRequiredEvent,
        ),
        (
            _event_payload(
                "ACM Certificate Revoked",
                {
                    "CertificateExpirationDate": "2019-12-22T18:43:48Z",
                    "CertificateType": "AMAZON_ISSUED",
                    "CommonName": "example.com",
                    "Exportable": True,
                },
            ),
            ACMCertificateRevokedEvent,
        ),
        (
            _event_payload(
                "ACM Certificate Revoked By CA",
                {
                    "CertificateExpirationDate": "2019-12-22T18:43:48Z",
                    "CertificateRevocationDate": "2019-12-20T18:43:48Z",
                    "CertificateSerial": "00:11:22",
                    "CertificateType": "PRIVATE",
                    "CommonName": "example.com",
                    "Exportable": True,
                    "RevocationReason": "KEY_COMPROMISE",
                },
            ),
            ACMCertificateRevokedByCAEvent,
        ),
        (
            _event_payload("ACM Certificate Rotated", {}),
            ACMCertificateRotatedEvent,
        ),
        (
            _event_payload(
                "AWS API Call via CloudTrail",
                {
                    "eventVersion": "1.11",
                    "eventTime": "2026-03-07T00:51:06Z",
                    "eventSource": "acm.amazonaws.com",
                    "eventName": "RequestCertificate",
                    "awsRegion": "us-east-1",
                    "requestParameters": {
                        "domainName": "example.com",
                    },
                },
            ),
            ACMAWSAPICallViaCloudTrailEvent,
        ),
    ],
)
def test_event_factory_builds_acm_events(
    payload: dict[str, object],
    expected_type: type[object],
) -> None:
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, expected_type)


@patch("botocraft.services.acm.ACMCertificate.objects")
def test_acm_event_loads_certificate(mock_certificate_objects: MagicMock) -> None:
    session = MagicMock()
    certificate_model = MagicMock(name="certificate-model")
    mock_certificate_manager = MagicMock()
    mock_certificate_manager.get.return_value = certificate_model
    mock_certificate_objects.using.return_value = mock_certificate_manager

    event = EventFactory(session=session).new(
        json.dumps(
            _event_payload(
                "ACM Certificate Approaching Expiration",
                {"DaysToExpiry": 31},
            )
        )
    )

    assert isinstance(event, ACMCertificateApproachingExpirationEvent)
    assert event.certificate_arn == _CERTIFICATE_ARN
    assert event.certificate is certificate_model
    mock_certificate_objects.using.assert_called_once_with(session)
    mock_certificate_manager.get.assert_called_once_with(_CERTIFICATE_ARN)
