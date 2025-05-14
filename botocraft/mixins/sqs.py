from functools import wraps
from typing import TYPE_CHECKING, Callable, List

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
        from botocraft.services.sqs import Queue

        sqs = self.client  # type: ignore[attr-defined]
        response = sqs.get_queue_url(QueueName=QueueName)
        queue_url = response["QueueUrl"]
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["All"],
        )
        attributes = response["Attributes"]
        tags = sqs.list_queue_tags(QueueUrl=queue_url)
        if "Tags" not in tags:
            tags["Tags"] = {}
        return Queue(
            QueueName=QueueName,
            QueueUrl=queue_url,
            Attributes=attributes if attributes else None,
            Tags=tags["Tags"],
        )
