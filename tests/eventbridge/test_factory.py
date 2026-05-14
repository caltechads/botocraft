import json
from typing import ClassVar

from pydantic import BaseModel

from botocraft.eventbridge.base import EventBridgeEvent
from botocraft.eventbridge.ecr import ECRImageActionEvent
from botocraft.eventbridge.ecs import ECSTaskStateChangeEvent
from botocraft.eventbridge.factory import EventFactory
from botocraft.eventbridge.ssm import SSMCalendarStateChangeEvent


def test_event_factory_builds_ecs_event() -> None:
    event = EventFactory().new(
        json.dumps(
            {
                "version": "0",
                "id": "1",
                "detail-type": "ECS Task State Change",
                "source": "aws.ecs",
                "account": "123456789012",
                "time": "2024-01-01T00:00:00Z",
                "region": "us-west-2",
                "resources": [],
                "detail": {
                    "clusterArn": (
                        "arn:aws:ecs:us-west-2:123456789012:cluster/default"
                    ),
                    "taskArn": "arn:aws:ecs:us-west-2:123456789012:task/default/abc",
                    "taskDefinitionArn": (
                        "arn:aws:ecs:us-west-2:123456789012:task-definition/family:1"
                    ),
                    "overrides": {"containerOverrides": []},
                    "desiredStatus": "RUNNING",
                    "launchType": "FARGATE",
                    "attributes": [],
                    "containers": [],
                    "availabilityZone": "us-west-2a",
                    "lastStatus": "RUNNING",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:00:00Z",
                    "version": 1,
                },
            }
        )
    )

    assert isinstance(event, ECSTaskStateChangeEvent)


def test_event_factory_builds_ecr_event() -> None:
    event = EventFactory().new(
        json.dumps(
            {
                "version": "0",
                "id": "1",
                "detail-type": "ECR Image Action",
                "source": "aws.ecr",
                "account": "123456789012",
                "time": "2024-01-01T00:00:00Z",
                "region": "us-west-2",
                "resources": [],
                "detail": {
                    "repository-name": "repo",
                    "image-digest": "sha256:abc",
                    "image-tag": "latest",
                    "action-type": "PUSH",
                    "result": "SUCCESS",
                },
            }
        )
    )

    assert isinstance(event, ECRImageActionEvent)


def test_event_factory_builds_ssm_event() -> None:
    event = EventFactory().new(
        json.dumps(
            {
                "version": "0",
                "id": "1",
                "detail-type": "Calendar State Change",
                "source": "aws.ssm",
                "account": "123456789012",
                "time": "2024-01-01T00:00:00Z",
                "region": "us-west-2",
                "resources": [
                    (
                        "arn:aws:ssm:us-west-2:123456789012:"
                        "document/MyChangeCalendar"
                    )
                ],
                "detail": {
                    "atTime": "2024-01-01T00:00:00Z",
                    "nextTransitionTime": "2024-01-01T01:00:00Z",
                    "state": "OPEN",
                },
            }
        )
    )

    assert isinstance(event, SSMCalendarStateChangeEvent)
    assert event.calendar_arn == (
        "arn:aws:ssm:us-west-2:123456789012:document/MyChangeCalendar"
    )
    assert event.is_open is True


def test_event_factory_supports_declarative_extension() -> None:
    class SyntheticEvent(EventBridgeEvent, BaseModel):
        source: str
        detail: dict[str, str]

    class SyntheticFactory(EventFactory):
        event_class_map: ClassVar = {
            **EventFactory.event_class_map,
            ("aws.synthetic", "Synthetic Detail Type"): SyntheticEvent,
        }

    event = SyntheticFactory().new(
        json.dumps(
            {
                "source": "aws.synthetic",
                "detail-type": "Synthetic Detail Type",
                "detail": {"kind": "demo"},
            }
        )
    )

    assert isinstance(event, SyntheticEvent)
