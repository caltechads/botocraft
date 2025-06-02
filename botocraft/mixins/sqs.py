from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Generator, List, Optional, Union

if TYPE_CHECKING:
    from botocraft.eventbridge import AbstractEventFactory, EventBridgeEvent
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
    from botocraft.services.sqs import Message


# ----------
# Decorators
# ----------


def queue_list_urls_to_queues(
    func: Callable[..., List["str"]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps a boto3 method that returns a list of SQS queue URLs to return a list
    of :py:class:`Queue` objects instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        self = args[0]
        urls = func(*args, **kwargs)
        names = [url.split("/")[-1] for url in urls]
        return PrimaryBoto3ModelQuerySet([self.get(QueueName=name) for name in names])

    return wrapper


def queue_recieve_messages_add_queue_url(
    func: Callable[..., List["Message"]],
) -> Callable[..., List["Message"]]:
    """
    Wraps a boto3 method that receives messages from an SQS queue to return
    a list of :py:class:`~botocraft.services.sqs.Message` objects with the
    queue URL added.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> List["Message"]:
        queue_url = args[1]
        messages = func(*args, **kwargs)

        if not messages:
            return []
        for message in messages:
            message.QueueUrl = queue_url
        return messages

    return wrapper


def queue_recieve_messages_add_event_factory(
    func: Callable[..., List["Message"]],
) -> Callable[..., List["Message"]]:
    """
    Wraps a boto3 method that receives messages from an SQS queue to return
    a list of :py:class:`~botocraft.services.sqs.Message` objects with the
    EventFactoryClass added.  This is useful for converting the message body
    to an event object.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> List["Message"]:
        from botocraft.eventbridge import EventFactory

        event_factory_class = kwargs.pop("EventFactoryClass", None)
        messages = func(*args, **kwargs)

        if not messages:
            return []
        if not event_factory_class:
            event_factory_class = EventFactory
        for message in messages:
            message.EventFactoryClass = event_factory_class
        return messages

    return wrapper


# -------------
# Mixin Classes
# -------------


class QueueManagerMixin:
    """
    A mixin class that extends :py:class:`~botocraft.services.sqs.QueueManager`
    to add the :py:meth:`get` method to retrieve a queue by name.   Queues are
    not first class objects in AWS SQS, so this is a convenience method to
    retrieve a queue by name and return our bespoke
    :py:class:`~botocraft.service.sqs.Queue` object.
    """

    def get(self, QueueName: str):  # noqa: N803
        """
        Get a queue by name.

        Args:
            QueueName: The name of the queue to retrieve.

        Raises:
            botocore.exceptions.ClientError: If the queue does not exist or if
              there is an error retrieving it.

        Returns:
            An object representing the queue, including its URL,
              attributes, and tags.

        """
        from botocraft.services import Queue, Tag

        sqs = self.client  # type: ignore[attr-defined]
        response = sqs.get_queue_url(QueueName=QueueName)
        queue_url = response["QueueUrl"]
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["All"],
        )
        attributes = response["Attributes"]
        tags = sqs.list_queue_tags(QueueUrl=queue_url)
        # Unfortunately the tags are returned as a dict with the key "Tags" and
        # the value being a dict of tags. We need to extract the tags from this
        # dict and convert them to a list of dicts, like TagsDictMixin expects
        if "Tags" not in tags:
            tags["Tags"] = []
        else:
            tags["Tags"] = [Tag(Key=k, Value=v) for k, v in tags["Tags"].items()]

        queue = Queue(
            QueueName=QueueName,
            QueueUrl=queue_url,
            Attributes=attributes if attributes else None,
            Tags=tags["Tags"],
        )
        queue.set_session(self.session)  # type: ignore[attr-defined]
        return queue


class QueueModelMixin:
    """
    A mixin class that extends :py:class:`~botocraft.services.sqs.Queue`
    to provide a generator that will yield all the messages in the queue
    eternally.  This is useful for a job that needs to listen continuously
    for messages on a queue.
    """

    def poll(
        self,
        EventFactoryClass: Optional["AbstractEventFactory"] = None,  # noqa: N803
    ) -> Generator["Message", None, None]:
        """
        Eternally poll for messages in the queue, and yield them as
        :py:class:`~botocraft.eventbridge.EventBridgeEvent` objects or dicts (if
        we can't identify the event) as they arrive.  This is useful for a job
        that needs to listen continuously for messages on a queue.

        Keyword Args:
            EventFactoryClass: The class to use to convert the message body
                to an event object.  If not provided, the default
                :py:class:`~botocraft.eventbridge.EventFactory` class will be used.

        Yields:
            A :py:class:`~botocraft.services.sqs.Message` from the queue

        """
        while True:
            messages = self.receive(  # type: ignore[attr-defined]
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                EventFactoryClass=EventFactoryClass,  # type: ignore[attr-defined]
            )
            if not messages:
                continue
            yield from messages


class MessageModelMixin:
    """
    A mixin class that extends :py:class:`~botocraft.services.sqs.Message`
    to provide a method to convert the message body to an event object.
    """

    @property
    def event(self) -> Union["EventBridgeEvent", dict[str, Any]]:
        """
        Convert the message body to an event object using the
        :py:class:`~botocraft.eventbridge.EventFactory` class.

        Returns:
            An event object or dict representing the message body.

        """
        if not hasattr(self, "EventFactoryClass"):
            msg = "EventFactoryClass is not set on the message."
            raise ValueError(msg)
        return self.EventFactoryClass().new(self.Body)  # type: ignore[attr-defined]
