import json

import pytest
from pydantic import BaseModel

from botocraft.eventbridge.elbv2 import Elbv2AWSAPICallViaCloudTrailEvent
from botocraft.eventbridge.factory import EventFactory

_LOAD_BALANCER_ARN = (
    "arn:aws:elasticloadbalancing:us-west-2:123456789012:"
    "loadbalancer/app/my-lb/2453ed029918f21f"
)


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
        "source": "aws.elasticloadbalancing",
        "account": "123456789012",
        "time": "2024-11-16T00:58:37Z",
        "region": "us-west-2",
        "resources": resources or [_LOAD_BALANCER_ARN],
        "detail": detail,
    }


@pytest.mark.parametrize(
    ("payload", "expected_type"),
    [
        (
            _event_payload(
                "AWS API Call via CloudTrail",
                {
                    "eventVersion": "1.11",
                    "userIdentity": {
                        "type": "AssumedRole",
                        "principalId": "EXAMPLE:session",
                        "arn": (
                            "arn:aws:sts::123456789012:assumed-role/"
                            "Admin/session"
                        ),
                    },
                    "eventTime": "2026-03-07T00:51:06Z",
                    "eventSource": "elasticloadbalancing.amazonaws.com",
                    "eventName": "CreateLoadBalancer",
                    "awsRegion": "us-west-2",
                    "sourceIPAddress": "192.0.2.1",
                    "userAgent": "aws-cli/2.33.13",
                    "requestParameters": {
                        "name": "my-lb",
                        "type": "application",
                    },
                    "responseElements": {
                        "loadBalancers": [
                            {
                                "loadBalancerArn": _LOAD_BALANCER_ARN,
                                "loadBalancerName": "my-lb",
                            }
                        ],
                    },
                    "requestID": "a1b2c3d4-5678-90ab-cdef-EXAMPLE55555",
                    "eventID": "a1b2c3d4-5678-90ab-cdef-EXAMPLE66666",
                    "readOnly": False,
                    "resources": [
                        {
                            "type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
                            "ARN": _LOAD_BALANCER_ARN,
                        }
                    ],
                    "eventType": "AwsApiCall",
                    "apiVersion": "2015-12-01",
                    "managementEvent": True,
                    "recipientAccountId": "123456789012",
                    "eventCategory": "Management",
                },
            ),
            Elbv2AWSAPICallViaCloudTrailEvent,
        ),
    ],
)
def test_event_factory_builds_elbv2_event(
    payload: dict[str, object],
    expected_type: type[object],
) -> None:
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, expected_type)


def test_elbv2_cloudtrail_event_parsed_request() -> None:
    payload = _event_payload(
        "AWS API Call via CloudTrail",
        {
            "eventVersion": "1.11",
            "eventTime": "2026-03-07T00:51:06Z",
            "eventSource": "elasticloadbalancing.amazonaws.com",
            "eventName": "CreateLoadBalancer",
            "awsRegion": "us-west-2",
            "requestParameters": {
                "name": "my-lb",
                "type": "application",
            },
        },
    )
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, Elbv2AWSAPICallViaCloudTrailEvent)
    parsed = event.parsed_request()
    assert isinstance(parsed, BaseModel)
    assert parsed.Name == "my-lb"  # type: ignore[attr-defined]


def test_elbv2_cloudtrail_event_parsed_request_unknown_operation() -> None:
    payload = _event_payload(
        "AWS API Call via CloudTrail",
        {
            "eventVersion": "1.11",
            "eventTime": "2026-03-07T00:51:06Z",
            "eventSource": "elasticloadbalancing.amazonaws.com",
            "eventName": "NotARealOperationName",
            "awsRegion": "us-west-2",
            "requestParameters": {"name": "my-lb"},
        },
    )
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, Elbv2AWSAPICallViaCloudTrailEvent)
    assert event.parsed_request() == {"name": "my-lb"}


def test_elbv2_cloudtrail_event_load_balancer_arn() -> None:
    payload = _event_payload(
        "AWS API Call via CloudTrail",
        {
            "eventVersion": "1.11",
            "eventTime": "2026-03-07T00:51:06Z",
            "eventSource": "elasticloadbalancing.amazonaws.com",
            "eventName": "CreateLoadBalancer",
            "awsRegion": "us-west-2",
            "requestParameters": {"name": "my-lb"},
        },
    )
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, Elbv2AWSAPICallViaCloudTrailEvent)
    assert event.load_balancer_arn == _LOAD_BALANCER_ARN
