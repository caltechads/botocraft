from typing import Any

from pydantic import Field


class EventBridgeEvent:
    """
    Base class for all EventBridge events.
    """

    session: Any | None = Field(default=None, exclude=True)
