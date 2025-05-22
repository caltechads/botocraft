import json
from typing import TYPE_CHECKING, Any, Union, cast

import boto3.session

from .ecr import (
    ECRAWSAPICallViaCloudTrailEvent,
    ECRImageActionEvent,
    ECRImageScanEvent,
    ECRPullThroughCacheActionEvent,
    ECRReferrerActionEvent,
    ECRReplicationActionEvent,
    ECRScanResourceChangeEvent,
)
from .ecs import (
    ECSAWSAPICallViaCloudTrailEvent,
    ECSContainerInstanceStateChangeEvent,
    ECSServiceActionEvent,
    ECSServiceDeploymentStateChangeEvent,
    ECSTaskStateChangeEvent,
)

if TYPE_CHECKING:
    from . import EventBridgeEvent


class AbstractEventFactory:
    """
    An abstract factory class that returns the proper EventBridge event class
    based on the event type.

    Keyword Args:
        session: The boto3 session to use for sessionizing the event class.
            If not provided, the default session will be used.

    """

    def __init__(self, session: boto3.session.Session | None = None) -> None:
        self.session = session

    def new(self, event_data: str) -> Union["EventBridgeEvent", dict[str, Any]]:
        """
        Return an event class of the type identified by ``event_data``.

        Args:
            event_data: The raw JSON data of the event.

        Returns:
            An event class of the specified type, or the raw event
            data (with a "session" key added) if the type is not recognized.

        """
        data = json.loads(event_data)
        data["session"] = self.session

        return data


class EventFactory(AbstractEventFactory):
    """
    A factory class that returns the proper EventBridge event class to
    based on the event type.

    Keyword Args:
        session: The boto3 session to use for sessionizing the event class.
            If not provided, the default session will be used.

    """

    def new(self, event_data: str) -> Union["EventBridgeEvent", dict[str, Any]]:  # noqa: PLR0911, PLR0912
        """
        Return an event class of the type identified by ``event_data``.

        Args:
            event_data: The raw JSON data of the event.

        Returns:
            An event class of the specified type, or the raw event
            data (with a "session" key added) if the type is not recognized.

        """
        data = cast("dict[str, Any]", super().new(event_data))

        if data["source"] == "aws.ecs":
            if data["detail-type"] == "ECS Task State Change":
                return ECSTaskStateChangeEvent(**data)
            if data["detail-type"] == "ECS Service Action":
                return ECSServiceActionEvent(**data)
            if data["detail-type"] == "ECS Deployment State Change":
                return ECSServiceDeploymentStateChangeEvent(**data)
            if data["detail-type"] == "ECS Container Instance State Change":
                return ECSContainerInstanceStateChangeEvent(**data)
            if data["detail-type"] == "AWS API Call via CloudTrail":
                return ECSAWSAPICallViaCloudTrailEvent(**data)
        if data["source"] == "aws.ecr":
            if data["detail-type"] == "ECR Image Action":
                return ECRImageActionEvent(**data)
            if data["detail-type"] == "ECR Image Scan":
                return ECRImageScanEvent(**data)
            if data["detail-type"] == "ECR Referrer Action":
                return ECRReferrerActionEvent(**data)
            if data["detail-type"] == "ECR Pull Through Cache Action":
                return ECRPullThroughCacheActionEvent(**data)
            if data["detail-type"] == "ECR Replication Action":
                return ECRReplicationActionEvent(**data)
            if data["detail-type"] == "ECR Scan Resource Change":
                return ECRScanResourceChangeEvent(**data)
            if data["detail-type"] == "AWS API Call via CloudTrail":
                return ECRAWSAPICallViaCloudTrailEvent(**data)

        return data
