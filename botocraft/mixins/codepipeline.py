from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.codepipeline import ActionType, Pipeline, PipelineExecution


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


def _pipeline_from_payload(payload: dict[str, Any]) -> "Pipeline":
    """
    Build a public Pipeline model from flattened payload data.

    Args:
        payload: Flattened pipeline payload from a service response.

    Returns:
        A public Pipeline model.

    """
    from botocraft.services.codepipeline import Pipeline

    if payload.get("pipelineName") is not None and payload.get("name") is None:
        payload["name"] = payload.pop("pipelineName")
    return Pipeline(**payload)


def _flatten_pipeline_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten CodePipeline wrapper responses into Pipeline constructor data.

    Args:
        payload: Wrapper response data from create, update, or get operations.

    Returns:
        Flat constructor data for a Pipeline model.

    """
    pipeline = dict(payload.get("pipeline", {}))
    metadata = cast("dict[str, Any]", payload.get("metadata", {}))
    if metadata.get("pipelineArn") is not None:
        pipeline["pipelineArn"] = metadata["pipelineArn"]
    return pipeline


def pipeline_response_to_pipeline(
    func: Callable[..., Any],
) -> Callable[..., "Pipeline | None"]:
    """
    Convert wrapped pipeline responses into public Pipeline models.

    Args:
        func: Generated manager method returning a wrapped pipeline response.

    Returns:
        Wrapped manager method returning a public Pipeline model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "Pipeline | None":
        response = func(self, *args, **kwargs)
        if response is None:
            return None
        pipeline = _pipeline_from_payload(
            _flatten_pipeline_payload(response.model_dump(exclude_none=True))
        )
        self.sessionize(pipeline)
        return pipeline

    return wrapper


def pipeline_summaries_to_pipelines(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Convert list summaries into public Pipeline models.

    ``ListPipelines`` returns only summary fields. After collecting summaries,
    this wrapper calls :py:meth:`PipelineManager.get` once per pipeline so each
    result is a full :py:class:`Pipeline` (stages, artifact stores, variables,
    triggers, ``pipelineArn``, and related fields from ``GetPipeline``). When
    the wrapped ``list`` method is called with ``version`` set, that value is
    forwarded to each ``get``; when ``version`` is omitted, each ``get`` loads
    the latest revision.

    Args:
        func: Generated list method returning summary-like pipeline entries.

    Returns:
        Wrapped list method returning fully hydrated Pipeline models.

    Side Effects:
        Performs one ``GetPipeline`` call per listed pipeline, in order, after
        ``ListPipelines`` pagination completes.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        hydrate_version = kwargs.get("version")
        results = func(self, *args, **kwargs)
        if not isinstance(results, PrimaryBoto3ModelQuerySet):
            results = PrimaryBoto3ModelQuerySet(results)
        pipelines: list[Boto3Model] = []
        for item in results.results:
            thin = _pipeline_from_payload(item.model_dump(exclude_none=True))
            pipeline_name = thin.pipelineName
            if pipeline_name:
                full = self.get(pipeline_name, version=hydrate_version)
                if full is not None:
                    pipelines.append(full)
                    continue
            pipelines.append(thin)
        query_set = PrimaryBoto3ModelQuerySet(pipelines)
        self.sessionize(query_set)
        return query_set

    return wrapper


def pipeline_execution_response_to_pipeline_execution(
    func: Callable[..., Any],
) -> Callable[..., "PipelineExecution | None"]:
    """
    Convert wrapped execution responses into public PipelineExecution models.

    Args:
        func: Generated manager method returning a wrapped execution response.

    Returns:
        Wrapped manager method returning a public PipelineExecution model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PipelineExecution | None":
        from botocraft.services.codepipeline import PipelineExecution

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        payload = response.model_dump(exclude_none=True).get("pipelineExecution", {})
        if payload.get("pipelineName") is None:
            pipeline_name = _arg_value(args, kwargs, "pipelineName", 0)
            if pipeline_name is not None:
                payload["pipelineName"] = pipeline_name
        execution = PipelineExecution(**payload)
        self.sessionize(execution)
        return execution

    return wrapper


def pipeline_execution_list_add_pipeline_name(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Reattach pipeline context to listed execution summaries.

    Args:
        func: Generated list method returning execution summaries.

    Returns:
        Wrapped list method with ``pipelineName`` restored on each result.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.codepipeline import PipelineExecution

        pipeline_name = _arg_value(args, kwargs, "pipelineName", 0)
        results = func(self, *args, **kwargs)
        if not isinstance(results, PrimaryBoto3ModelQuerySet):
            results = PrimaryBoto3ModelQuerySet(results)
        executions = []
        for item in results.results:
            payload = item.model_dump(exclude_none=True)
            if pipeline_name is not None:
                payload["pipelineName"] = pipeline_name
            executions.append(PipelineExecution(**payload))
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", executions))
        self.sessionize(query_set)
        return query_set

    return wrapper


def action_type_response_to_action_type(
    func: Callable[..., Any],
) -> Callable[..., "ActionType | None"]:
    """
    Convert wrapped custom-action responses into public ActionType models.

    Args:
        func: Generated manager method returning a wrapped action-type response.

    Returns:
        Wrapped manager method returning a public ActionType model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "ActionType | None":
        from botocraft.services.codepipeline import ActionType

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        payload = response.model_dump(exclude_none=True)
        action_type_payload = dict(payload.get("actionType", {}))
        action_type = ActionType(**action_type_payload)
        self.sessionize(action_type)
        return action_type

    return wrapper


def action_type_declaration_response_to_action_type(
    func: Callable[..., Any],
) -> Callable[..., "ActionType | None"]:
    """
    Convert detail action-type responses into public ActionType models.

    Args:
        func: Generated manager method returning a detail action-type response.

    Returns:
        Wrapped manager method returning a public ActionType model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "ActionType | None":
        from botocraft.services.codepipeline import ActionType

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        payload = response.model_dump(exclude_none=True).get("actionType", {})
        action_type = ActionType(**payload)
        self.sessionize(action_type)
        return action_type

    return wrapper
