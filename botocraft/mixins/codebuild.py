"""Handwritten helpers for the generated CodeBuild service managers."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Iterable, cast

from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.codebuild import (
        Build,
        BuildBatch,
        CommandExecution,
        Fleet,
        Project,
        Report,
        ReportGroup,
        Sandbox,
        Webhook,
    )

#: Maximum resource names or identifiers to send in a single CodeBuild batch API call.
_BATCH_CHUNK_SIZE: int = 100


def _arg_value(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    name: str,
    position: int,
) -> Any:
    """
    Return a manager-call argument from keyword or positional form.

    Args:
        args: Positional arguments forwarded into the generated manager method.
        kwargs: Keyword arguments forwarded into the generated manager method.
        name: Keyword argument name to prefer.
        position: Positional argument index after ``self``.

    Returns:
        The matched value, or ``None`` when absent.

    """
    if name in kwargs:
        return kwargs[name]
    if len(args) > position:
        return args[position]
    return None


def _chunked(items: list[str], size: int) -> Iterable[list[str]]:
    """
    Yield fixed-size chunks from a list of strings.

    Args:
        items: Values to chunk.
        size: Maximum chunk length.

    Yields:
        Consecutive slices no longer than ``size``.

    """
    for index in range(0, len(items), size):
        yield items[index : index + size]


def _coerce_queryset_results(value: Any) -> list[Any]:
    """
    Normalize list or queryset results into a plain Python list.

    Args:
        value: Either a :class:`PrimaryBoto3ModelQuerySet` or a ``list``.

    Returns:
        A list of underlying result objects.

    """
    if isinstance(value, PrimaryBoto3ModelQuerySet):
        return list(value.results)
    if value is None:
        return []
    return list(value)


def project_response_to_project(
    func: Callable[..., Any],
) -> Callable[..., Project | None]:
    """
    Convert wrapped project responses into public :class:`Project` models.

    Args:
        func: Generated manager method returning a nested project payload.

    Returns:
        Wrapped manager method returning a public :class:`Project` model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.codebuild import Project

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        if isinstance(response, Project):
            self.sessionize(response)
            return response
        payload = response.model_dump(exclude_none=True)
        project_payload = payload.get("project", payload)
        project = Project(**project_payload)
        self.sessionize(project)
        return project

    return wrapper


def project_names_to_projects(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate string project names into full :class:`Project` models.

    Args:
        func: Generated ``list`` / ``list_shared`` method returning name strings.

    Returns:
        Wrapped method returning a queryset of :class:`Project` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.codebuild import Project

        raw = func(self, *args, **kwargs)
        names = [
            item for item in _coerce_queryset_results(raw) if isinstance(item, str)
        ]
        if not names:
            return PrimaryBoto3ModelQuerySet([])
        projects: list[Project] = []
        for chunk in _chunked(names, _BATCH_CHUNK_SIZE):
            resp = self.client.batch_get_projects(names=chunk)
            projects.extend(
                Project(**project_payload)
                for project_payload in (resp.get("projects") or [])
            )
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", projects))
        self.sessionize(query_set)
        return query_set

    return wrapper


def build_response_to_build(
    func: Callable[..., Any],
) -> Callable[..., Build | None]:
    """
    Convert wrapped build responses into public :class:`Build` models.

    Args:
        func: Generated manager method returning a nested build payload.

    Returns:
        Wrapped manager method returning a public :class:`Build` model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.codebuild import Build

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        if isinstance(response, Build):
            self.sessionize(response)
            return response
        payload = response.model_dump(exclude_none=True)
        build_payload = payload.get("build", payload)
        build = Build(**build_payload)
        self.sessionize(build)
        return build

    return wrapper


def _hydrate_build_ids(self: Any, ids: list[str]) -> PrimaryBoto3ModelQuerySet:
    """
    Materialize build identifiers into :class:`Build` models.

    Args:
        self: The active manager instance with a configured boto3 client.
        ids: Build identifiers returned by list-style APIs.

    Returns:
        A queryset of hydrated :class:`Build` instances.

    """
    from botocraft.services.codebuild import Build

    if not ids:
        return PrimaryBoto3ModelQuerySet([])
    builds: list[Build] = []
    for chunk in _chunked(ids, _BATCH_CHUNK_SIZE):
        resp = self.client.batch_get_builds(ids=chunk)
        builds.extend(
            Build(**build_payload) for build_payload in (resp.get("builds") or [])
        )
    query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", builds))
    self.sessionize(query_set)
    return query_set


def build_ids_to_builds(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate list-build identifiers into :class:`Build` models.

    Args:
        func: Generated ``list`` method returning identifier strings.

    Returns:
        Wrapped method returning a queryset of :class:`Build` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        raw = func(self, *args, **kwargs)
        ids = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        return _hydrate_build_ids(self, ids)

    return wrapper


def build_ids_to_builds_with_project(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate per-project list-build identifiers into :class:`Build` models.

    Args:
        func: Generated ``list_for_project`` method returning identifier strings.

    Returns:
        Wrapped method returning a queryset of :class:`Build` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.codebuild import Build

        project_name = _arg_value(args, kwargs, "projectName", 0)
        raw = func(self, *args, **kwargs)
        ids = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        query_set = _hydrate_build_ids(self, ids)
        if project_name is not None:
            adjusted: list[Build] = []
            for item in query_set.results:
                payload = item.model_dump(exclude_none=True)
                if payload.get("projectName") is None:
                    payload["projectName"] = project_name
                adjusted.append(Build(**payload))
            query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", adjusted))
            self.sessionize(query_set)
        return query_set

    return wrapper


def build_batch_response_to_build_batch(
    func: Callable[..., Any],
) -> Callable[..., BuildBatch | None]:
    """
    Convert wrapped build batch responses into public :class:`BuildBatch` models.

    Args:
        func: Generated manager method returning a nested build batch payload.

    Returns:
        Wrapped manager method returning a public :class:`BuildBatch` model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.codebuild import BuildBatch

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        if isinstance(response, BuildBatch):
            self.sessionize(response)
            return response
        payload = response.model_dump(exclude_none=True)
        batch_payload = payload.get("buildBatch", payload)
        batch = BuildBatch(**batch_payload)
        self.sessionize(batch)
        return batch

    return wrapper


def _hydrate_build_batch_ids(self: Any, ids: list[str]) -> PrimaryBoto3ModelQuerySet:
    """
    Materialize build batch identifiers into :class:`BuildBatch` models.

    Args:
        self: The active manager instance with a configured boto3 client.
        ids: Build batch identifiers returned by list-style APIs.

    Returns:
        A queryset of hydrated :class:`BuildBatch` instances.

    """
    from botocraft.services.codebuild import BuildBatch

    if not ids:
        return PrimaryBoto3ModelQuerySet([])
    batches: list[BuildBatch] = []
    for chunk in _chunked(ids, _BATCH_CHUNK_SIZE):
        resp = self.client.batch_get_build_batches(ids=chunk)
        batches.extend(
            BuildBatch(**batch_payload)
            for batch_payload in (resp.get("buildBatches") or [])
        )
    query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", batches))
    self.sessionize(query_set)
    return query_set


def build_batch_ids_to_build_batches(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate list batch identifiers into :class:`BuildBatch` models.

    Args:
        func: Generated ``list`` method returning identifier strings.

    Returns:
        Wrapped method returning a queryset of :class:`BuildBatch` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        raw = func(self, *args, **kwargs)
        ids = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        return _hydrate_build_batch_ids(self, ids)

    return wrapper


def build_batch_ids_to_build_batches_with_project(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate per-project batch identifiers into :class:`BuildBatch` models.

    Args:
        func: Generated ``list_for_project`` method returning identifier strings.

    Returns:
        Wrapped method returning a queryset of :class:`BuildBatch` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.codebuild import BuildBatch

        project_name = _arg_value(args, kwargs, "projectName", 0)
        raw = func(self, *args, **kwargs)
        ids = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        query_set = _hydrate_build_batch_ids(self, ids)
        if project_name is not None:
            adjusted: list[BuildBatch] = []
            for item in query_set.results:
                payload = item.model_dump(exclude_none=True)
                if payload.get("projectName") is None:
                    payload["projectName"] = project_name
                adjusted.append(BuildBatch(**payload))
            query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", adjusted))
            self.sessionize(query_set)
        return query_set

    return wrapper


def fleet_response_to_fleet(
    func: Callable[..., Any],
) -> Callable[..., Fleet | None]:
    """
    Convert wrapped fleet responses into public :class:`Fleet` models.

    Args:
        func: Generated manager method returning a nested fleet payload.

    Returns:
        Wrapped manager method returning a public :class:`Fleet` model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.codebuild import Fleet

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        if isinstance(response, Fleet):
            self.sessionize(response)
            return response
        payload = response.model_dump(exclude_none=True)
        fleet_payload = payload.get("fleet", payload)
        fleet = Fleet(**fleet_payload)
        self.sessionize(fleet)
        return fleet

    return wrapper


def fleet_names_to_fleets(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate fleet name strings into full :class:`Fleet` models.

    Args:
        func: Generated ``list`` method returning fleet name strings.

    Returns:
        Wrapped method returning a queryset of :class:`Fleet` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.codebuild import Fleet

        raw = func(self, *args, **kwargs)
        names = [
            item for item in _coerce_queryset_results(raw) if isinstance(item, str)
        ]
        if not names:
            return PrimaryBoto3ModelQuerySet([])
        fleets: list[Fleet] = []
        for chunk in _chunked(names, _BATCH_CHUNK_SIZE):
            resp = self.client.batch_get_fleets(names=chunk)
            fleets.extend(
                Fleet(**fleet_payload) for fleet_payload in (resp.get("fleets") or [])
            )
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", fleets))
        self.sessionize(query_set)
        return query_set

    return wrapper


def report_group_response_to_report_group(
    func: Callable[..., Any],
) -> Callable[..., ReportGroup | None]:
    """
    Convert wrapped report group responses into public :class:`ReportGroup` models.

    Args:
        func: Generated manager method returning a nested report group payload.

    Returns:
        Wrapped manager method returning a public :class:`ReportGroup` model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.codebuild import ReportGroup

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        if isinstance(response, ReportGroup):
            self.sessionize(response)
            return response
        payload = response.model_dump(exclude_none=True)
        group_payload = payload.get("reportGroup", payload)
        group = ReportGroup(**group_payload)
        self.sessionize(group)
        return group

    return wrapper


def _hydrate_report_group_arns(self: Any, arns: list[str]) -> PrimaryBoto3ModelQuerySet:
    """
    Materialize report group ARNs into :class:`ReportGroup` models.

    Args:
        self: The active manager instance with a configured boto3 client.
        arns: Report group ARNs returned by list-style APIs.

    Returns:
        A queryset of hydrated :class:`ReportGroup` instances.

    """
    from botocraft.services.codebuild import ReportGroup

    if not arns:
        return PrimaryBoto3ModelQuerySet([])
    groups: list[ReportGroup] = []
    for chunk in _chunked(arns, _BATCH_CHUNK_SIZE):
        resp = self.client.batch_get_report_groups(reportGroupArns=chunk)
        groups.extend(
            ReportGroup(**group_payload)
            for group_payload in (resp.get("reportGroups") or [])
        )
    query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", groups))
    self.sessionize(query_set)
    return query_set


def report_group_arns_to_report_groups(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate report group ARN strings into :class:`ReportGroup` models.

    Args:
        func: Generated ``list`` / ``list_shared`` method returning ARN strings.

    Returns:
        Wrapped method returning a queryset of :class:`ReportGroup` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        raw = func(self, *args, **kwargs)
        arns = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        return _hydrate_report_group_arns(self, arns)

    return wrapper


def _hydrate_report_arns(self: Any, arns: list[str]) -> PrimaryBoto3ModelQuerySet:
    """
    Materialize report ARNs into :class:`Report` models.

    Args:
        self: The active manager instance with a configured boto3 client.
        arns: Report ARNs returned by list-style APIs.

    Returns:
        A queryset of hydrated :class:`Report` instances.

    """
    from botocraft.services.codebuild import Report

    if not arns:
        return PrimaryBoto3ModelQuerySet([])
    reports: list[Report] = []
    for chunk in _chunked(arns, _BATCH_CHUNK_SIZE):
        resp = self.client.batch_get_reports(reportArns=chunk)
        reports.extend(
            Report(**report_payload) for report_payload in (resp.get("reports") or [])
        )
    query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", reports))
    self.sessionize(query_set)
    return query_set


def report_arns_to_reports(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate report ARN strings into :class:`Report` models.

    Args:
        func: Generated ``list`` method returning ARN strings.

    Returns:
        Wrapped method returning a queryset of :class:`Report` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        raw = func(self, *args, **kwargs)
        arns = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        return _hydrate_report_arns(self, arns)

    return wrapper


def report_arns_to_reports_with_group(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate report ARNs listed for a report group into :class:`Report` models.

    Args:
        func: Generated ``list_for_report_group`` method returning ARN strings.

    Returns:
        Wrapped method returning a queryset of :class:`Report` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        raw = func(self, *args, **kwargs)
        arns = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        return _hydrate_report_arns(self, arns)

    return wrapper


def webhook_response_with_project_name(
    func: Callable[..., Any],
) -> Callable[..., Webhook | None]:
    """
    Attach ``projectName`` context to webhook responses that omit it.

    Args:
        func: Generated ``create`` / ``update`` webhook method.

    Returns:
        Wrapped method returning a hydrated :class:`Webhook` model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.codebuild import Webhook

        project_name = kwargs.get("projectName")
        if project_name is None:
            model_arg = _arg_value(args, kwargs, "model", 0)
            if model_arg is not None and hasattr(model_arg, "projectName"):
                project_name = getattr(model_arg, "projectName", None)
        response = func(self, *args, **kwargs)
        if response is None:
            return None
        if isinstance(response, Webhook):
            if project_name is not None and response.projectName is None:
                payload = response.model_dump(exclude_none=True)
                payload["projectName"] = project_name
                merged = Webhook(**payload)
                self.sessionize(merged)
                return merged
            self.sessionize(response)
            return response
        payload = response.model_dump(exclude_none=True)
        webhook_payload = payload.get("webhook", payload)
        if project_name is not None and webhook_payload.get("projectName") is None:
            webhook_payload["projectName"] = project_name
        webhook = Webhook(**webhook_payload)
        self.sessionize(webhook)
        return webhook

    return wrapper


def sandbox_response_to_sandbox(
    func: Callable[..., Any],
) -> Callable[..., Sandbox | None]:
    """
    Convert wrapped sandbox responses into public :class:`Sandbox` models.

    Args:
        func: Generated sandbox lifecycle method returning nested payloads.

    Returns:
        Wrapped manager method returning a public :class:`Sandbox` model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.codebuild import Sandbox

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        if isinstance(response, Sandbox):
            self.sessionize(response)
            return response
        payload = response.model_dump(exclude_none=True)
        sandbox_payload = payload.get("sandbox", payload)
        sandbox = Sandbox(**sandbox_payload)
        self.sessionize(sandbox)
        return sandbox

    return wrapper


def _hydrate_sandbox_ids(self: Any, ids: list[str]) -> PrimaryBoto3ModelQuerySet:
    """
    Materialize sandbox identifiers into :class:`Sandbox` models.

    Args:
        self: The active manager instance with a configured boto3 client.
        ids: Sandbox identifiers returned by list-style APIs.

    Returns:
        A queryset of hydrated :class:`Sandbox` instances.

    """
    from botocraft.services.codebuild import Sandbox

    if not ids:
        return PrimaryBoto3ModelQuerySet([])
    sandboxes: list[Sandbox] = []
    for chunk in _chunked(ids, _BATCH_CHUNK_SIZE):
        resp = self.client.batch_get_sandboxes(ids=chunk)
        sandboxes.extend(
            Sandbox(**sandbox_payload)
            for sandbox_payload in (resp.get("sandboxes") or [])
        )
    query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", sandboxes))
    self.sessionize(query_set)
    return query_set


def sandbox_ids_to_sandboxes(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate sandbox identifier strings into :class:`Sandbox` models.

    Args:
        func: Generated ``list`` method returning identifier strings.

    Returns:
        Wrapped method returning a queryset of :class:`Sandbox` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        raw = func(self, *args, **kwargs)
        ids = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        return _hydrate_sandbox_ids(self, ids)

    return wrapper


def sandbox_ids_to_sandboxes_with_project(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Hydrate per-project sandbox identifiers into :class:`Sandbox` models.

    Args:
        func: Generated ``list_for_project`` method returning identifier strings.

    Returns:
        Wrapped method returning a queryset of :class:`Sandbox` instances.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        from botocraft.services.codebuild import Sandbox

        project_name = _arg_value(args, kwargs, "projectName", 0)
        raw = func(self, *args, **kwargs)
        ids = [item for item in _coerce_queryset_results(raw) if isinstance(item, str)]
        query_set = _hydrate_sandbox_ids(self, ids)
        if project_name is not None:
            adjusted: list[Sandbox] = [
                (
                    Sandbox(**{**payload, "projectName": project_name})
                    if payload.get("projectName") is None
                    else item
                )
                for item in query_set.results
                for payload in [item.model_dump(exclude_none=True)]
            ]
            query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", adjusted))
            self.sessionize(query_set)
        return query_set

    return wrapper


def command_execution_response_to_command_execution(
    func: Callable[..., Any],
) -> Callable[..., CommandExecution | None]:
    """
    Convert wrapped command execution responses into public models.

    Args:
        func: Generated ``start`` method on :class:`CommandExecution` managers.

    Returns:
        Wrapped manager method returning a :class:`CommandExecution` model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        from botocraft.services.codebuild import CommandExecution

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        if isinstance(response, CommandExecution):
            self.sessionize(response)
            return response
        payload = response.model_dump(exclude_none=True)
        execution_payload = payload.get("commandExecution", payload)
        execution = CommandExecution(**execution_payload)
        self.sessionize(execution)
        return execution

    return wrapper
