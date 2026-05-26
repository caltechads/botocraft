from typing import Any, Protocol


class EventSummaryProtocol(Protocol):
    """
    Structural type for EventBridge metadata used in summary rendering.
    """

    #: AWS account that emitted the event.
    account: str
    #: Event source identifier.
    source: str
    #: Timestamp when EventBridge recorded the event.
    time: Any
    #: AWS region where the event was emitted.
    region: str
    #: Resources associated with the event.
    resources: list[str]


#: Index of the first resource in an EventBridge resources list.
FIRST_RESOURCE_INDEX = 0
#: Index of the second resource in an EventBridge resources list.
SECOND_RESOURCE_INDEX = 1
#: Minimum resource count needed to safely read the first resource ARN.
FIRST_RESOURCE_COUNT = 1
#: Minimum resource count needed to safely read the second resource ARN.
SECOND_RESOURCE_COUNT = 2


def first_resource(resources: list[str]) -> str | None:
    """
    Return the first resource ARN from an event payload.

    Args:
        resources: Resource ARNs carried on the EventBridge event.

    Returns:
        The first resource ARN when present, otherwise ``None``.

    """
    if len(resources) < FIRST_RESOURCE_COUNT:
        return None
    return resources[FIRST_RESOURCE_INDEX]


def second_resource(resources: list[str]) -> str | None:
    """
    Return the second resource ARN from an event payload.

    Args:
        resources: Resource ARNs carried on the EventBridge event.

    Returns:
        The second resource ARN when present, otherwise ``None``.

    """
    if len(resources) < SECOND_RESOURCE_COUNT:
        return None
    return resources[SECOND_RESOURCE_INDEX]


def event_summary(
    event_name: str,
    event: EventSummaryProtocol,
    **details: object,
) -> str:
    """
    Build a readable string representation for an EventBridge wrapper.

    Args:
        event_name: Human-readable event name shown in the summary.
        event: Event instance being rendered.

    Keyword Args:
        details: Extra event-specific fields to append to the summary.

    Returns:
        Compact summary string for the event.

    """
    parts = [
        f"account={event.account}",
        f"source={event.source}",
        f"time={event.time}",
        f"region={event.region}",
        f"resources={event.resources}",
    ]
    parts.extend(
        f"{name}={value}"
        for name, value in details.items()
        if value is not None and value != ""
    )
    return f"<Event: {event_name}: " + ", ".join(parts) + ">"
