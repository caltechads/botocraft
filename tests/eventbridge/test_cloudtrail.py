from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pytest
from pydantic import BaseModel

from botocraft.eventbridge.acm import ACMAWSAPICallViaCloudTrailEvent
from botocraft.eventbridge.cloudtrail import (
    CloudTrailApiCallMixin,
    request_model_for_operation,
    service_name_from_event_source,
)
from botocraft.eventbridge.codepipeline import CodePipelineAWSAPICallViaCloudTrailEvent
from botocraft.eventbridge.factory import EventFactory


def test_service_name_from_event_source_strips_amazonaws_suffix() -> None:
    assert service_name_from_event_source("acm.amazonaws.com") == "acm"


def test_service_name_from_event_source_uses_alias_table() -> None:
    assert service_name_from_event_source("monitoring.amazonaws.com") == "cloudwatch"


@pytest.mark.parametrize(
    ("service_name", "event_name"),
    [
        ("acm", "RequestCertificate"),
        ("codepipeline", "StartPipelineExecution"),
    ],
)
def test_request_model_for_operation_builds_cached_model(
    service_name: str,
    event_name: str,
) -> None:
    first = request_model_for_operation(service_name, event_name)
    second = request_model_for_operation(service_name, event_name)
    assert first is not None
    assert first is second


def test_request_model_for_operation_returns_none_for_unknown_operation() -> None:
    assert request_model_for_operation("acm", "NotARealOperationName") is None


@dataclass
class _AcmRequestCertificateDetail:
    eventSource: str = "acm.amazonaws.com"
    eventName: str = "RequestCertificate"
    requestParameters: dict[str, Any] | None = field(
        default_factory=lambda: {"domainName": "example.com"}
    )


class _MixinHost(CloudTrailApiCallMixin):
    def __init__(self) -> None:
        self.detail = _AcmRequestCertificateDetail()


def test_parsed_request_returns_validated_model_for_cloudtrail_keys() -> None:
    parsed = _MixinHost().parsed_request()
    assert isinstance(parsed, BaseModel)
    assert parsed.DomainName == "example.com"  # type: ignore[attr-defined]


def test_parsed_request_returns_raw_dict_when_operation_unknown() -> None:
    @dataclass
    class _Detail:
        eventSource: str = "acm.amazonaws.com"
        eventName: str = "NotARealOperationName"
        requestParameters: dict[str, Any] | None = field(
            default_factory=lambda: {"domainName": "example.com"}
        )

    class _Host(CloudTrailApiCallMixin):
        def __init__(self) -> None:
            self.detail = _Detail()

    parsed = _Host().parsed_request()
    assert parsed == {"domainName": "example.com"}


def test_event_factory_acm_cloudtrail_event_supports_parsed_request() -> None:
    payload = {
        "version": "0",
        "id": "event-id",
        "detail-type": "AWS API Call via CloudTrail",
        "source": "aws.acm",
        "account": "123456789012",
        "time": "2026-03-07T00:51:06Z",
        "region": "us-east-1",
        "resources": [],
        "detail": {
            "eventVersion": "1.11",
            "eventTime": "2026-03-07T00:51:06Z",
            "eventSource": "acm.amazonaws.com",
            "eventName": "RequestCertificate",
            "awsRegion": "us-east-1",
            "requestParameters": {"domainName": "example.com"},
        },
    }
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, ACMAWSAPICallViaCloudTrailEvent)
    parsed = event.parsed_request()
    assert isinstance(parsed, BaseModel)
    assert parsed.DomainName == "example.com"  # type: ignore[attr-defined]


def test_event_factory_codepipeline_cloudtrail_event_supports_parsed_request() -> None:
    payload = {
        "version": "0",
        "id": "event-id",
        "detail-type": "AWS API Call via CloudTrail",
        "source": "aws.codepipeline",
        "account": "123456789012",
        "time": "2026-03-07T00:51:06Z",
        "region": "us-west-2",
        "resources": [],
        "detail": {
            "eventVersion": "1.11",
            "eventTime": "2026-03-07T00:51:06Z",
            "eventSource": "codepipeline.amazonaws.com",
            "eventName": "StartPipelineExecution",
            "awsRegion": "us-west-2",
            "requestParameters": {"name": "myPipeline"},
        },
    }
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, CodePipelineAWSAPICallViaCloudTrailEvent)
    parsed = event.parsed_request()
    assert isinstance(parsed, BaseModel)
    assert parsed.name == "myPipeline"  # type: ignore[attr-defined]
