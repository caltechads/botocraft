from functools import wraps
from typing import TYPE_CHECKING, Callable

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.logs import LogGroup, LogGroupSummary


def log_groups_only(
    func: Callable[..., list["LogGroupSummary"]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.ecs.ServiceManager.list` to return a
    :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.ecs.Service` objects instead of only a list of
    ARNs.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        identifiers = func(self, *args, **kwargs)
        arns = [identifier.logGroupArn for identifier in identifiers]
        log_groups = []
        # We have to do this in batches of 50 because the get_many method,
        # which uses the boto3 ``describe_log_groups`` method, only accepts 50 ARNs
        # at a time.
        for i in range(0, len(arns), 50):
            log_groups.extend(self.get_many(logGroupIdentifiers=arns[i : i + 50]))
        return PrimaryBoto3ModelQuerySet(log_groups)

    return wrapper


def create_log_group_extended(
    func: Callable[..., "LogGroup"],
) -> Callable[..., "LogGroup"]:
    """
    Wraps :py:meth:`botocraft.services.logs.LogGroupManager.create` to create a
    log group with extended functionality.
    """

    @wraps(func)
    def wrapper(self, model: "LogGroup") -> "LogGroup":
        # create_log_group returns nothing
        func(self, model)

        # Now add our retention
        self.client.put_retention_policy(
            logGroupName=model.logGroupName,
            retentionInDays=model.retentionInDays,
        )
        # Put our tags
        self.client.tag_log_group(
            logGroupName=model.logGroupName,
            tags=[{"Key": tag.Key, "Value": tag.Value} for tag in model.Tags],
        )

    return wrapper


def convert_log_group_tags(
    func: Callable[..., "LogGroup"],
) -> Callable[..., "LogGroup"]:
    """
    Wraps :py:meth:`botocraft.services.logs.LogGroupManager.get` to convert the
    tags to the format expected by botocraft.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "LogGroup":
        from botocraft.services.common import Tag

        # convert the tags to the format expected by the API
        log_group = func(self, *args, **kwargs)
        response = self.client.list_tags_log_group(
            logGroupName=log_group.logGroupName,
        )
        if response["tags"]:
            log_group.Tags = [Tag(Key=k, Value=v) for k, v in response["tags"].items()]
        return log_group

    return wrapper


def convert_log_groups_tags(
    func: Callable[..., list["LogGroup"]],
) -> Callable[..., list["LogGroup"]]:
    """
    Wraps :py:meth:`botocraft.services.logs.LogGroupManager.get_many` to convert the
    tags to the format expected by botocraft.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "list[LogGroup]":
        from botocraft.services.common import Tag

        # convert the tags to the format expected by the API
        log_groups = func(self, *args, **kwargs)
        for log_group in log_groups:
            response = self.client.list_tags_log_group(
                logGroupName=log_group.logGroupName,
            )
            if response["tags"]:
                log_group.Tags = [
                    Tag(Key=k, Value=v) for k, v in response["tags"].items()
                ]
        return log_groups

    return wrapper


class LogGroupManagerMixin:
    """
    Mixin for the :py:class:`LogGroupManager` class.

    This mixin provides an update method for log groups since there is no
    such method in the AWS API.
    """

    def update(self, model: "LogGroup") -> None:
        """
        There's no generic update method for log groups, so we cobble one
        together from the existing separate update methods.

        - untag_log_group
        - tag_log_group
        - put_retention_policy
        - put_log_group_deletion_protection

        Args:
            model: the :py:class:`LogGroup` to update.

        """
        # First let's deal with tags.  It looks like we have to untag all existing tags,
        # and then tag the new ones.
        response = self.client.list_tags_log_group(
            logGroupName=model.LogGroupName,
        )
        for tag in response["tags"]:
            self.client.untag_log_group(
                logGroupName=model.LogGroupName,
                tagKeys=[tag["Key"]],
            )
        # reformat our tags to the format expected by the API
        tags = [{"Key": tag.Key, "Value": tag.Value} for tag in model.Tags]
        self.client.tag_log_group(
            logGroupName=model.LogGroupName,
            tags=tags,
        )

        # Now let's deal with the retention policy.
        self.client.put_retention_policy(
            logGroupName=model.logGroupName,
            retentionInDays=model.retentionInDays,
        )

        # Finally let's deal with the deletion protection.
        self.client.put_log_group_deletion_protection(
            logGroupName=model.logGroupName,
            deletionProtectionEnabled=model.deletionProtectionEnabled,
        )
