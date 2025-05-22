from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Generator, List, Union

from botocraft.eventbridge import AbstractEventFactory, EventBridgeEvent, EventFactory

if TYPE_CHECKING:
    from botocraft.services.sqs import Queue


# ----------
# Decorators
# ----------


def queue_list_urls_to_queues(
    func: Callable[..., List["str"]],
) -> Callable[..., List["Queue"]]:
    """
    Wraps a boto3 method that returns a list of SQS queue URLs to return a list
    of :py:class:`Queue` objects instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> List["Queue"]:
        self = args[0]
        urls = func(*args, **kwargs)
        names = [url.split("/")[-1] for url in urls]
        return [self.get(QueueName=name) for name in names]

    return wrapper


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
        event_factory_class: type[AbstractEventFactory] | None = None,
        raw: bool = False,
    ) -> Generator[Union["EventBridgeEvent", dict[str, Any]], None, None]:
        """
        Eternally poll for messages in the queue, and yield them as
        :py:class:`~botocraft.eventbridge.EventBridgeEvent` objects or dicts (if
        we can't identify the event) as they arrive.  This is useful for a job
        that needs to listen continuously for messages on a queue.

        Keyword Args:
            event_factory_class: The class to use to create the event objects.  If not
                provided, the default :py:class:`~botocraft.eventbridge.EventFactory`
                class will be used.
            raw: If ``True``, return the raw message body instead of an event object.
                This is useful for debugging or if you want to handle the message
                yourself.  If ``False``, return an event object, if possible.

        Yields:
            An event object representing the message in the queue, or a dict
            representing the message if the event type is not recognized.

        """
        if event_factory_class:
            factory = event_factory_class(session=self.session)  # type: ignore[attr-defined]
        else:
            factory = EventFactory(session=self.session)  # type: ignore[attr-defined]

        while True:
            messages = self.receive(  # type: ignore[attr-defined]
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
            )
            if not messages:
                continue
            if raw:
                yield from messages
            else:
                events = [factory.new(message.body) for message in messages]
                yield from events
