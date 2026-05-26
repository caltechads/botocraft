import json
from typing import TYPE_CHECKING, Any, ClassVar

import boto3.session

from .acm import EVENT_CLASS_MAP as ACM_EVENT_CLASS_MAP
from .codepipeline import EVENT_CLASS_MAP as CODEPIPELINE_EVENT_CLASS_MAP
from .ecr import EVENT_CLASS_MAP as ECR_EVENT_CLASS_MAP
from .ecs import EVENT_CLASS_MAP as ECS_EVENT_CLASS_MAP
from .elasticsearch import EVENT_CLASS_MAP as ELASTICSEARCH_EVENT_CLASS_MAP
from .opensearch import EVENT_CLASS_MAP as OPENSEARCH_EVENT_CLASS_MAP
from .ssm import EVENT_CLASS_MAP as SSM_EVENT_CLASS_MAP

if TYPE_CHECKING:
    from . import EventBridgeEvent


class AbstractEventFactory:
    """
    Return the proper EventBridge event class for a raw JSON payload.

    Keyword Args:
        session: The boto3 session to use for sessionizing the event class.
            If not provided, the default session will be used.

    """

    #: Mapping from ``(source, detail-type)`` pairs to event classes.
    event_class_map: ClassVar[dict[tuple[str, str], type["EventBridgeEvent"]]] = {}

    def __init__(self, session: boto3.session.Session | None = None) -> None:
        """
        Initialize factory with an optional boto3 session.

        Keyword Args:
            session: Session attached to created event objects.

        """
        #: Session attached to created event objects.
        self.session = session

    def _deserialize_event_data(self, event_data: str) -> dict[str, Any]:
        """
        Decode raw EventBridge JSON and attach the active session.

        Args:
            event_data: The raw JSON data of the event.

        Returns:
            Deserialized event payload with ``session`` attached.

        """
        data = json.loads(event_data)
        data["session"] = self.session
        return data

    def new(self, event_data: str) -> "EventBridgeEvent | dict[str, Any]":
        """
        Return an event class of the type identified by ``event_data``.

        Args:
            event_data: The raw JSON data of the event.

        Returns:
            An event class of the specified type, or the raw event
            data (with a "session" key added) if the type is not recognized.

        """
        data = self._deserialize_event_data(event_data)
        event_class = self.event_class_map.get((data["source"], data["detail-type"]))
        if event_class is None:
            return data
        return event_class(**data)


class EventFactory(AbstractEventFactory):
    """
    Default EventBridge factory backed by declarative wrapper mappings.

    Keyword Args:
        session: The boto3 session to use for sessionizing the event class.
            If not provided, the default session will be used.

    """

    #: Default EventBridge wrapper mapping for supported services.
    event_class_map: ClassVar[dict[tuple[str, str], type["EventBridgeEvent"]]] = {
        **ACM_EVENT_CLASS_MAP,
        **CODEPIPELINE_EVENT_CLASS_MAP,
        **ECS_EVENT_CLASS_MAP,
        **ECR_EVENT_CLASS_MAP,
        **ELASTICSEARCH_EVENT_CLASS_MAP,
        **OPENSEARCH_EVENT_CLASS_MAP,
        **SSM_EVENT_CLASS_MAP,
    }
