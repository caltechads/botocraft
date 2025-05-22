import boto3


class EventBridgeEvent:
    """
    Base class for all EventBridge events.
    """

    session: boto3.session.Session | None = None
