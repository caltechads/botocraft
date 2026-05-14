from .base import EventBridgeEvent
from .raw import SSMCalendarStateChangeEvent as RawSSMCalendarStateChangeEvent


class SSMCalendarStateChangeEvent(EventBridgeEvent, RawSSMCalendarStateChangeEvent):
    """
    EventBridge event for Systems Manager calendar state changes.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the calendar state transition event.

        """
        return (
            f"<Event: SSM Calendar State Change: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"state={self.detail.state}, "
            f"next_transition_time={self.detail.nextTransitionTime}>"
        )

    @property
    def calendar_arn(self) -> str | None:
        """
        Return the calendar ARN carried by the event resources list.

        Returns:
            Calendar ARN when the event names one resource, otherwise ``None``.

        """
        if not self.resources:
            return None
        return self.resources[0]

    @property
    def is_open(self) -> bool:
        """
        Check whether the calendar is currently open.

        Returns:
            ``True`` when the event reports an ``OPEN`` state.

        """
        return self.detail.state.upper() == "OPEN"

    @property
    def is_closed(self) -> bool:
        """
        Check whether the calendar is currently closed.

        Returns:
            ``True`` when the event reports a ``CLOSED`` state.

        """
        return self.detail.state.upper() == "CLOSED"


#: Declarative mapping from EventBridge source/detail-type pairs to wrappers.
EVENT_CLASS_MAP = {
    ("aws.ssm", "Calendar State Change"): SSMCalendarStateChangeEvent,
}
