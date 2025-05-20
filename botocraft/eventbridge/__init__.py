import boto3.session

from .factory import AbstractEventFactory, EventFactory  # noqa: F401


class EventBridgeEvent:
    """
    Base class for all EventBridge events.
    """

    session: boto3.session.Session | None = None
