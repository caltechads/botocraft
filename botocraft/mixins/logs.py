# mypy: disable-error-code="attr-defined"
from __future__ import annotations

import time
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

from botocore.exceptions import WaiterError

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from collections.abc import Iterator

    from botocraft.services.logs import (
        GetQueryResultsResponse,
        LogGroup,
        LogGroupSummary,
        QueryDefinition,
        QueryStatistics,
        ResultField,
        StartQueryResponse,
    )

#: Terminal CloudWatch Logs Insights query statuses.
_TERMINAL_QUERY_STATUSES = frozenset(
    {"Complete", "Failed", "Cancelled", "Timeout", "Unknown"}
)


def log_groups_only(
    func: Callable[..., list[LogGroupSummary]],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Wraps :py:meth:`botocraft.services.ecs.ServiceManager.list` to return a
    :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.ecs.Service` objects instead of only a list of
    ARNs.

    Args:
        func: Manager list method returning log group summaries.

    Returns:
        Wrapped method returning hydrated log groups.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> PrimaryBoto3ModelQuerySet:
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
    func: Callable[..., LogGroup],
) -> Callable[..., LogGroup]:
    """
    Wraps :py:meth:`botocraft.services.logs.LogGroupManager.create` to create a
    log group with extended functionality.

    Args:
        func: Generated create method.

    Returns:
        Wrapped create method that applies retention and tags.

    """

    @wraps(func)
    def wrapper(self, model: LogGroup) -> LogGroup:
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
    func: Callable[..., LogGroup],
) -> Callable[..., LogGroup]:
    """
    Wraps :py:meth:`botocraft.services.logs.LogGroupManager.get` to convert the
    tags to the format expected by botocraft.

    Args:
        func: Generated get method.

    Returns:
        Wrapped get method with tag enrichment.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> LogGroup:
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
    func: Callable[..., list[LogGroup]],
) -> Callable[..., list[LogGroup]]:
    """
    Wraps :py:meth:`botocraft.services.logs.LogGroupManager.get_many` to convert the
    tags to the format expected by botocraft.

    Args:
        func: Generated get-many method.

    Returns:
        Wrapped method with tag enrichment on each log group.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> list[LogGroup]:
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


def _iter_query_definitions(
    manager: Any,
    *,
    queryLanguage: str | None = None,  # noqa: N803
    queryDefinitionNamePrefix: str | None = None,  # noqa: N803
    maxResults: int | None = None,  # noqa: N803
) -> Iterator[QueryDefinition]:
    """
    Yield query definitions across all ``describe_query_definitions`` pages.

    Args:
        manager: Generated :py:class:`~botocraft.services.logs.QueryDefinitionManager`.

    Keyword Args:
        queryLanguage: Optional query language filter.
        queryDefinitionNamePrefix: Optional name prefix filter.
        maxResults: Optional page size for each describe call.

    Yields:
        :py:class:`~botocraft.services.logs.QueryDefinition` models from each page.

    """
    from botocraft.services.logs import DescribeQueryDefinitionsResponse

    next_token: str | None = None
    while True:
        request: dict[str, Any] = {}
        if queryLanguage is not None:
            request["queryLanguage"] = queryLanguage
        if queryDefinitionNamePrefix is not None:
            request["queryDefinitionNamePrefix"] = queryDefinitionNamePrefix
        if maxResults is not None:
            request["maxResults"] = maxResults
        if next_token is not None:
            request["nextToken"] = next_token

        response = manager.client.describe_query_definitions(**request)
        parsed = DescribeQueryDefinitionsResponse(**response)
        if parsed.queryDefinitions:
            yield from parsed.queryDefinitions
        next_token = parsed.nextToken
        if not next_token:
            break


def paginate_query_definitions(
    func: Callable[..., PrimaryBoto3ModelQuerySet],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Wrap generated ``list()`` to page through all query definitions.

    Args:
        func: Generated manager ``list`` method (single-page without paginator).

    Returns:
        Wrapped method returning all pages as a queryset.

    """

    @wraps(func)
    def wrapper(self, *_args, **kwargs) -> PrimaryBoto3ModelQuerySet:
        results = list(
            _iter_query_definitions(
                self,
                queryLanguage=kwargs.get("queryLanguage"),
                queryDefinitionNamePrefix=kwargs.get("queryDefinitionNamePrefix"),
                maxResults=kwargs.get("maxResults"),
            )
        )
        self.sessionize(results)
        return PrimaryBoto3ModelQuerySet(results)

    return wrapper


def query_definition_from_put(
    func: Callable[..., str | None],
) -> Callable[..., QueryDefinition | None]:
    """
    Hydrate a full query definition after ``put_query_definition``.

    Args:
        func: Generated create/update method returning ``queryDefinitionId``.

    Returns:
        Wrapped method returning hydrated
        :py:class:`~botocraft.services.logs.QueryDefinition`.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> QueryDefinition | None:
        query_definition_id = func(self, *args, **kwargs)
        if query_definition_id is None:
            return None
        return self.get(query_definition_id)

    return wrapper


class LogGroupManagerMixin:
    """
    Mixin for the :py:class:`LogGroupManager` class.

    This mixin provides an update method for log groups since there is no
    such method in the AWS API, plus CloudWatch Logs Insights query helpers.
    """

    def update(self, model: LogGroup) -> None:
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

    def wait_for_query_results(
        self,
        query_id: str,
        *,
        poll_interval: float = 1.0,
        max_attempts: int = 120,
    ) -> GetQueryResultsResponse:
        """
        Poll ``get_query_results`` until the query reaches a terminal status.

        Args:
            query_id: CloudWatch Logs Insights query identifier.

        Keyword Args:
            poll_interval: Seconds to sleep between poll attempts.
            max_attempts: Maximum poll attempts before raising.

        Raises:
            WaiterError: If the query does not reach a terminal status in time.

        Returns:
            Final :py:class:`~botocraft.services.logs.GetQueryResultsResponse`.

        """
        attempt = 0
        response: GetQueryResultsResponse | None = None
        while attempt < max_attempts:
            response = self.get_query_results(queryId=query_id)
            if response.status in _TERMINAL_QUERY_STATUSES:
                return response
            attempt += 1
            time.sleep(poll_interval)

        reason = f"Max attempts exceeded waiting for query {query_id!r}"
        raise WaiterError(
            name="logs_query_complete",
            reason=reason,
            last_response=response.model_dump() if response is not None else {},
        )

    def _collect_query_result_pages(
        self,
        query_id: str,
        *,
        initial_response: GetQueryResultsResponse | None = None,
    ) -> tuple[list[list[ResultField]], QueryStatistics | None]:
        """
        Aggregate all result pages for a completed Insights query.

        Args:
            query_id: CloudWatch Logs Insights query identifier.

        Keyword Args:
            initial_response: Optional first results page to include.

        Returns:
            Tuple of aggregated result rows and final query statistics.

        """
        rows: list[list[ResultField]] = []
        statistics: QueryStatistics | None = None
        next_token: str | None = None
        first_page = True

        while True:
            if first_page and initial_response is not None:
                page = initial_response
                first_page = False
            else:
                kwargs: dict[str, Any] = {"queryId": query_id}
                if next_token is not None:
                    kwargs["nextToken"] = next_token
                page = self.get_query_results(**kwargs)

            statistics = page.statistics
            if page.results:
                rows.extend(page.results)
            next_token = page.nextToken
            if not next_token:
                break

        return rows, statistics

    def run_query(  # noqa: PLR0913
        self,
        *,
        queryString: str,  # noqa: N803
        startTime: int,  # noqa: N803
        endTime: int,  # noqa: N803
        logGroupName: str | None = None,  # noqa: N803
        logGroupNames: list[str] | None = None,  # noqa: N803
        logGroupIdentifiers: list[str] | None = None,  # noqa: N803
        queryLanguage: str | None = None,  # noqa: N803
        limit: int | None = None,
        poll_interval: float = 1.0,
        max_attempts: int = 120,
    ) -> tuple[list[list[ResultField]], QueryStatistics | None]:
        """
        Start an Insights query, wait for completion, and return all result rows.

        Keyword Args:
            queryString: CloudWatch Logs Insights query string.
            startTime: Query start time as Unix epoch seconds.
            endTime: Query end time as Unix epoch seconds.
            logGroupName: Optional single log group name.
            logGroupNames: Optional list of log group names.
            logGroupIdentifiers: Optional log group names or ARNs.
            queryLanguage: Optional query language (for example ``CWLI`` or ``SQL``).
            limit: Optional maximum number of log events to return.
            poll_interval: Seconds between status polls.
            max_attempts: Maximum poll attempts while waiting for completion.

        Raises:
            WaiterError: If polling times out before a terminal status.
            RuntimeError: If the query finishes in a non-complete terminal status.

        Returns:
            Aggregated result rows and query statistics.

        """
        start_response: StartQueryResponse = self.start_query(
            queryString=queryString,
            startTime=startTime,
            endTime=endTime,
            logGroupName=logGroupName,
            logGroupNames=logGroupNames,
            logGroupIdentifiers=logGroupIdentifiers,
            queryLanguage=queryLanguage,
            limit=limit,
        )
        query_id = cast("str", start_response.queryId)
        final = self.wait_for_query_results(
            query_id,
            poll_interval=poll_interval,
            max_attempts=max_attempts,
        )
        if final.status != "Complete":
            msg = (
                f"CloudWatch Logs Insights query {query_id!r} finished with "
                f"status {final.status!r}"
            )
            raise RuntimeError(msg)
        return self._collect_query_result_pages(query_id, initial_response=final)


class QueryDefinitionManagerMixin:
    """
    Mixin for :py:class:`~botocraft.services.logs.QueryDefinitionManager`.

    Provides get-by-id and saved-query execution helpers not covered by
    generated CRUD methods alone.
    """

    def get(self, query_definition_id: str) -> QueryDefinition | None:
        """
        Return one saved query definition by identifier.

        Args:
            query_definition_id: Query definition ID returned by
                ``put_query_definition``.

        Returns:
            Matching :py:class:`~botocraft.services.logs.QueryDefinition`, or
            ``None`` when not found.

        """
        for definition in _iter_query_definitions(self):
            if definition.queryDefinitionId == query_definition_id:
                self.sessionize(definition)
                return definition
        return None

    def start_query(
        self,
        model: QueryDefinition,
        *,
        startTime: int,  # noqa: N803
        endTime: int,  # noqa: N803
        limit: int | None = None,
    ) -> StartQueryResponse:
        """
        Run a saved query definition over a time window.

        Args:
            model: Saved :py:class:`~botocraft.services.logs.QueryDefinition`.
            startTime: Query start time as Unix epoch seconds.
            endTime: Query end time as Unix epoch seconds.

        Keyword Args:
            limit: Optional maximum number of log events to return.

        Returns:
            :py:class:`~botocraft.services.logs.StartQueryResponse` with
            ``queryId``.

        """
        from botocraft.services.logs import LogGroupManager

        manager = LogGroupManager()
        manager.session = self.session
        return manager.start_query(
            queryString=cast("str", model.queryString),
            startTime=startTime,
            endTime=endTime,
            logGroupNames=model.logGroupNames,
            queryLanguage=model.queryLanguage,
            limit=limit,
        )
