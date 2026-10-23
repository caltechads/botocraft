"""
Handwritten helpers for generated Amplify Hosting managers.

Manual deploy uploads a local zip, then starts that deployment. Job start
and job stop stay out of this service. See
``docs/adr/0003-amplify-manual-deploy-uploads-the-zip.md``.
"""

from __future__ import annotations

import time
import urllib.request
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from botocraft.mixins.common import arg_value, coerce_queryset_results
from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.amplify import (
        AmplifyBranch,
        AmplifyWebhook,
        App,
        BackendEnvironment,
        DomainAssociation,
        Job,
    )

#: Statuses after which an Amplify job no longer changes.
_TERMINAL_JOB_STATUSES = frozenset({"SUCCEED", "FAILED", "CANCELLED"})


def _scope_arg(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    name: str,
    position: int,
) -> str | None:
    """
    Read a scope id from keywords, a positional string, or a model argument.

    Args:
        args: Positional arguments, not including ``self``.
        kwargs: Keyword arguments.
        name: Argument or model attribute name.
        position: Positional index when the argument is a string.

    Returns:
        The scope id, or ``None`` when the call did not carry one.

    """
    value = arg_value(args, kwargs, name, position)
    if isinstance(value, str):
        return value
    if args and not isinstance(args[0], str):
        attr = getattr(args[0], name, None)
        if isinstance(attr, str):
            return attr
    return None


def _stamp(result: Any, **fields: str | None) -> Any:
    """
    Copy scope ids onto a model or each model in a queryset.

    Args:
        result: A model, queryset, list, or ``None``.

    Keyword Args:
        fields: Attribute names and values to set when the value is not
            ``None`` and the object has that attribute.

    Returns:
        The same result object.

    """
    if result is None:
        return None
    items = coerce_queryset_results(result) if not hasattr(result, "appId") else None
    if items is None and hasattr(result, "appId"):
        items = [result]
    elif items is None:
        return result
    for item in items:
        for key, value in fields.items():
            if value is not None and hasattr(item, key):
                setattr(item, key, value)
    return result


def amplify_stamp_app_id(func):
    """
    Copy ``appId`` from the call onto branch, domain, or backend results.

    Those shapes omit the owning app id. Later delete and update need it.

    Args:
        func: Generated manager method.

    Returns:
        Wrapped method.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        app_id = _scope_arg(args, kwargs, "appId", 0)
        return _stamp(func(self, *args, **kwargs), appId=app_id)

    return wrapper


def amplify_stamp_job_scope(func):
    """
    Copy ``appId`` and ``branchName`` onto a job result.

    Args:
        func: Generated ``get_job`` method.

    Returns:
        Wrapped method.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        return _stamp(
            func(self, *args, **kwargs),
            appId=_scope_arg(args, kwargs, "appId", 0),
            branchName=_scope_arg(args, kwargs, "branchName", 1),
        )

    return wrapper


def amplify_sync_tags(func):
    """
    Write model ``Tags`` through ``tag_resource`` after update.

    Amplify update operations do not accept tags. Create still sends tags
    on the create request.

    Args:
        func: Generated update method.

    Returns:
        Wrapped method.

    Side Effects:
        Calls ``tag_resource`` when the caller set ``Tags``, the result has
        an ARN, and ``Tags`` is a dict.

    """

    @wraps(func)
    def wrapper(self, model: Any, *args: Any, **kwargs: Any) -> Any:
        result = func(self, model, *args, **kwargs)
        tags = getattr(model, "Tags", None)
        fields_set = getattr(model, "model_fields_set", ())
        arn = getattr(result, "appArn", None) or getattr(result, "branchArn", None)
        if isinstance(tags, dict) and arn and "Tags" in fields_set:
            self.client.tag_resource(resourceArn=arn, tags=tags)
            if hasattr(result, "Tags"):
                result.Tags = tags
        return result

    return wrapper


def _put_zip(url: str, zip_path: str | Path) -> None:
    """
    PUT zip bytes to a presigned Amplify upload URL.

    Args:
        url: Presigned URL from ``CreateDeployment``.
        zip_path: Local zip file.

    Raises:
        HTTPError: Amplify's upload endpoint rejected the PUT.
        FileNotFoundError: ``zip_path`` does not exist.

    Side Effects:
        Sends the file bytes over HTTP.

    """
    request = urllib.request.Request(  # noqa: S310
        url,
        data=Path(zip_path).read_bytes(),
        method="PUT",
        headers={"Content-Type": "application/zip"},
    )
    with urllib.request.urlopen(request) as response:  # noqa: S310
        response.read()


def _read_text(url: str) -> str:
    """
    Download a presigned Amplify URL and decode it as text.

    Args:
        url: Presigned log or artifact URL.

    Returns:
        The response body as text.

    Raises:
        HTTPError: The URL rejected the download.

    Side Effects:
        Sends an HTTP GET.

    """
    request = urllib.request.Request(url)  # noqa: S310
    with urllib.request.urlopen(request) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="replace")


def _boto_create(
    manager: Any,
    operation: str,
    method: str,
    response_key: str,
    model_cls: type[Any],
    **kwargs: Any,
) -> Any:
    """
    Call an Amplify create operation with request members only.

    Response fields such as ARNs and timestamps are not accepted. ``None``
    values are omitted. A returned model that has ``appId`` copies it from
    the call when the caller passed one.

    Args:
        manager: Manager whose client and ``sessionize`` are used.
        operation: Botocore operation name, such as ``CreateApp``.
        method: Boto3 client method name, such as ``create_app``.
        response_key: Response member that holds the created resource.
        model_cls: Model class for that resource.

    Keyword Args:
        kwargs: Members of the operation input shape.

    Returns:
        The created model with a session attached.

    Raises:
        TypeError: A required member is missing, or a keyword is not in
            the input shape.

    Side Effects:
        Creates the resource in Amplify.

    """
    shape = manager.client.meta.service_model.operation_model(operation).input_shape
    allowed = set(shape.members)
    unknown = sorted(set(kwargs) - allowed)
    if unknown:
        names = ", ".join(unknown)
        msg = f"{operation} got unexpected keyword argument(s): {names}"
        raise TypeError(msg)
    missing = [name for name in shape.required_members if kwargs.get(name) is None]
    if missing:
        names = ", ".join(missing)
        msg = f"{operation} missing required argument(s): {names}"
        raise TypeError(msg)
    payload = {key: value for key, value in kwargs.items() if value is not None}
    response = getattr(manager.client, method)(**payload)
    model = model_cls(**response[response_key])
    app_id = kwargs.get("appId")
    if isinstance(app_id, str):
        model.appId = app_id
    manager.sessionize(model)
    return model


def _page(client: Any, operation: str, result_key: str, **kwargs: Any) -> list[Any]:
    """
    Follow ``nextToken`` for an Amplify list that has no boto paginator.

    Args:
        client: Amplify boto3 client.
        operation: Client method name.
        result_key: Response member that holds the page of results.

    Keyword Args:
        kwargs: Arguments for the first call. ``nextToken`` is overwritten.

    Returns:
        Combined result members from every page.

    """
    items: list[Any] = []
    token: str | None = None
    seen: set[str] = set()
    call = getattr(client, operation)
    while True:
        request = {key: value for key, value in kwargs.items() if value is not None}
        if token:
            request["nextToken"] = token
        response = call(**request)
        items.extend(response.get(result_key) or [])
        token = response.get("nextToken")
        if not token or token in seen:
            return items
        seen.add(token)


class AmplifyAppManagerMixin:
    """
    Create an Amplify app from CreateApp inputs and download its access log.

    ``create`` takes boto request members. ``name`` is the only required
    one. ``access_log_text`` downloads the body behind ``generate_access_logs``.
    """

    #: Boto3 Amplify client used by the generated manager.
    client: Any

    def create(self, **kwargs: Any) -> App:
        """
        Create an app from CreateApp inputs.

        Pass boto names such as ``name``, ``platform``, ``repository``, and
        ``tags``. Response fields such as ``appId`` and ``appArn`` are rejected.

        Keyword Args:
            kwargs: CreateApp request members. ``name`` is required.

        Returns:
            The created app.

        Raises:
            TypeError: A required member is missing, or a keyword is not a
                CreateApp member.

        Side Effects:
            Creates the app in Amplify.

        """
        from botocraft.services.amplify import App

        return _boto_create(self, "CreateApp", "create_app", "app", App, **kwargs)

    def access_log_text(
        self,
        domainName: str,  # noqa: N803
        appId: str,  # noqa: N803
        **kwargs: Any,
    ) -> str:
        """
        Download this app's access log.

        Args:
            domainName: Domain name Amplify uses to select the log.
            appId: Amplify app id.

        Keyword Args:
            kwargs: ``startTime`` and ``endTime`` for ``generate_access_logs``.

        Returns:
            The access log body.

        Raises:
            HTTPError: The log URL rejected the download.

        Side Effects:
            Asks Amplify for a log URL and downloads that URL.

        """
        url = self.generate_access_logs(domainName, appId, **kwargs)  # type: ignore[attr-defined]
        return _read_text(url)


class AmplifyBranchManagerMixin:
    """
    Create a branch from CreateBranch inputs, and publish a local zip.

    ``create`` accepts CreateBranch members by boto name. ``deploy_zip``
    uploads a zip and starts that deployment. ``wait=True`` returns the
    job after it reaches ``SUCCEED``, ``FAILED``, or ``CANCELLED``.
    """

    #: Boto3 Amplify client used by the generated manager.
    client: Any

    def create(self, **kwargs: Any) -> AmplifyBranch:
        """
        Create a branch from CreateBranch inputs.

        Keyword Args:
            kwargs: CreateBranch request members. ``appId`` and
                ``branchName`` are required.

        Returns:
            The created branch, with ``appId`` set from the call.

        Raises:
            TypeError: A required member is missing, or a keyword is not a
                CreateBranch member.

        Side Effects:
            Creates the branch in Amplify.

        """
        from botocraft.services.amplify import AmplifyBranch

        return _boto_create(
            self,
            "CreateBranch",
            "create_branch",
            "branch",
            AmplifyBranch,
            **kwargs,
        )

    def deploy_zip(  # noqa: PLR0913
        self,
        appId: str,  # noqa: N803
        branchName: str,  # noqa: N803
        zip_path: str | Path,
        *,
        wait: bool = False,
        timeout: float = 900,
        interval: float = 5,
    ) -> Job:
        """
        Publish a local zip to this branch.

        Args:
            appId: Amplify app id.
            branchName: Branch that receives the zip.
            zip_path: Local zip file. Amplify does not build it.

        Keyword Args:
            wait: When ``True``, poll until the job finishes.
            timeout: Seconds to wait when ``wait`` is ``True``.
            interval: Seconds between job reads when ``wait`` is ``True``.

        Returns:
            The job for this deploy, including steps. With ``wait=True``,
            the status is ``SUCCEED``, ``FAILED``, or ``CANCELLED``.

        Raises:
            ValueError: ``CreateDeployment`` did not return a job id and a
                zip upload URL.
            HTTPError: The presigned URL rejected the upload. The deploy
                is not started.
            TimeoutError: ``wait`` is ``True`` and the job is still running
                after ``timeout`` seconds.

        Side Effects:
            Creates a deployment, uploads the zip, and starts the deploy.
            When ``wait`` is ``True``, reads the job until it finishes.

        """
        from botocraft.services.amplify import Job

        created = self.client.create_deployment(appId=appId, branchName=branchName)
        upload_url = created.get("zipUploadUrl")
        job_id = created.get("jobId")
        if not isinstance(upload_url, str) or not isinstance(job_id, str):
            msg = "CreateDeployment did not return a zip upload URL and job id"
            raise ValueError(msg)  # noqa: TRY004
        _put_zip(upload_url, zip_path)
        self.client.start_deployment(appId=appId, branchName=branchName, jobId=job_id)
        response = self.client.get_job(appId=appId, branchName=branchName, jobId=job_id)
        job = Job(**response["job"])
        job.appId = appId
        job.branchName = branchName
        self.sessionize(job)  # type: ignore[attr-defined]
        if wait:
            return job.wait(timeout=timeout, interval=interval)
        return job


class AmplifyDomainAssociationManagerMixin:
    """
    Create a domain association from CreateDomainAssociation inputs.

    ``appId``, ``domainName``, and ``subDomainSettings`` are required.
    ``subDomainSettings`` items use ``prefix`` and ``branchName``.
    """

    #: Boto3 Amplify client used by the generated manager.
    client: Any

    def create(self, **kwargs: Any) -> DomainAssociation:
        """
        Create a domain association from CreateDomainAssociation inputs.

        Keyword Args:
            kwargs: CreateDomainAssociation request members.

        Returns:
            The created domain association, with ``appId`` set from the call.

        Raises:
            TypeError: A required member is missing, or a keyword is not a
                CreateDomainAssociation member.

        Side Effects:
            Creates the domain association in Amplify.

        """
        from botocraft.services.amplify import DomainAssociation

        return _boto_create(
            self,
            "CreateDomainAssociation",
            "create_domain_association",
            "domainAssociation",
            DomainAssociation,
            **kwargs,
        )


class AmplifyWebhookManagerMixin:
    """
    Create and list webhooks for one app.

    ``ListWebhooks`` returns ``nextToken`` and is not a boto paginator, so
    the generated list method cannot call ``get_paginator``. ``create``
    takes ``appId`` and ``branchName``.
    """

    #: Boto3 Amplify client used by the generated manager.
    client: Any

    def create(self, **kwargs: Any) -> AmplifyWebhook:
        """
        Create a webhook from CreateWebhook inputs.

        Keyword Args:
            kwargs: CreateWebhook request members. ``appId`` and
                ``branchName`` are required. ``description`` is optional.

        Returns:
            The created webhook.

        Raises:
            TypeError: A required member is missing, or a keyword is not a
                CreateWebhook member.

        Side Effects:
            Creates the webhook in Amplify.

        """
        from botocraft.services.amplify import AmplifyWebhook

        return _boto_create(
            self,
            "CreateWebhook",
            "create_webhook",
            "webhook",
            AmplifyWebhook,
            **kwargs,
        )

    def list(self, appId: str) -> PrimaryBoto3ModelQuerySet:  # noqa: N803
        """
        Return webhooks for one app.

        Args:
            appId: Amplify app id.

        Returns:
            A queryset of webhooks.

        """
        from botocraft.services.amplify import AmplifyWebhook

        hooks = [
            AmplifyWebhook(**raw)
            for raw in _page(self.client, "list_webhooks", "webhooks", appId=appId)
        ]
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", hooks))
        self.sessionize(query_set)  # type: ignore[attr-defined]
        return query_set


class AmplifyBackendEnvironmentManagerMixin:
    """
    Create and list backend environments for one app.

    ``ListBackendEnvironments`` is not a boto paginator. ``create`` takes
    ``appId`` and ``environmentName``.
    """

    #: Boto3 Amplify client used by the generated manager.
    client: Any

    def create(self, **kwargs: Any) -> BackendEnvironment:
        """
        Create a backend environment from CreateBackendEnvironment inputs.

        Keyword Args:
            kwargs: CreateBackendEnvironment request members. ``appId`` and
                ``environmentName`` are required.

        Returns:
            The created backend environment, with ``appId`` set from the call.

        Raises:
            TypeError: A required member is missing, or a keyword is not a
                CreateBackendEnvironment member.

        Side Effects:
            Creates the backend environment in Amplify.

        """
        from botocraft.services.amplify import BackendEnvironment

        return _boto_create(
            self,
            "CreateBackendEnvironment",
            "create_backend_environment",
            "backendEnvironment",
            BackendEnvironment,
            **kwargs,
        )

    def list(self, appId: str) -> PrimaryBoto3ModelQuerySet:  # noqa: N803
        """
        Return backend environments for one app.

        Args:
            appId: Amplify app id.

        Returns:
            A queryset of backend environments with ``appId`` set.

        """
        from botocraft.services.amplify import BackendEnvironment

        environments = []
        for raw in _page(
            self.client,
            "list_backend_environments",
            "backendEnvironments",
            appId=appId,
        ):
            environment = BackendEnvironment(**raw)
            environment.appId = appId
            environments.append(environment)
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", environments))
        self.sessionize(query_set)  # type: ignore[attr-defined]
        return query_set


class AmplifyJobManagerMixin:
    """
    Read and delete Amplify jobs.

    ``ListJobs`` returns summaries. ``list`` loads each job with ``GetJob``
    so the result includes steps. There is no start or stop method.
    """

    #: Boto3 Amplify client used by the generated manager.
    client: Any

    def list(self, appId: str, branchName: str) -> PrimaryBoto3ModelQuerySet:  # noqa: N803
        """
        Return full jobs for one branch.

        Args:
            appId: Amplify app id.
            branchName: Branch name.

        Returns:
            A queryset of jobs with steps and scope ids set.

        """
        from botocraft.services.amplify import Job

        summaries: list[dict[str, Any]] = []
        paginator = self.client.get_paginator("list_jobs")
        for page in paginator.paginate(appId=appId, branchName=branchName):
            summaries.extend(page.get("jobSummaries") or [])
        jobs: list[Boto3Model] = []
        for summary in summaries:
            response = self.client.get_job(
                appId=appId,
                branchName=branchName,
                jobId=summary["jobId"],
            )
            job = Job(**response["job"])
            job.appId = appId
            job.branchName = branchName
            jobs.append(job)
        self.sessionize(jobs)  # type: ignore[attr-defined]
        return PrimaryBoto3ModelQuerySet(jobs)

    def delete(self, appId: str, branchName: str, jobId: str) -> Job:  # noqa: N803
        """
        Delete one job and return the job as it existed before deletion.

        Args:
            appId: Amplify app id.
            branchName: Branch name.
            jobId: Job id.

        Returns:
            The job loaded before ``delete_job``.

        Side Effects:
            Deletes the job in Amplify.

        """
        from botocraft.services.amplify import Job

        response = self.client.get_job(
            appId=appId,
            branchName=branchName,
            jobId=jobId,
        )
        job = Job(**response["job"])
        job.appId = appId
        job.branchName = branchName
        self.client.delete_job(appId=appId, branchName=branchName, jobId=jobId)
        self.sessionize(job)  # type: ignore[attr-defined]
        return job


class AmplifyArtifactManagerMixin:
    """
    List artifact records for one job.

    ``ListArtifacts`` is not a boto paginator. Download URLs are the
    generated ``url`` method.
    """

    #: Boto3 Amplify client used by the generated manager.
    client: Any

    def list(
        self,
        appId: str,  # noqa: N803
        branchName: str,  # noqa: N803
        jobId: str,  # noqa: N803
    ) -> PrimaryBoto3ModelQuerySet:
        """
        Return artifact records for one job.

        Args:
            appId: Amplify app id.
            branchName: Branch name.
            jobId: Job id.

        Returns:
            A queryset of artifacts.

        """
        from botocraft.services.amplify import Artifact

        artifacts = [
            Artifact(**raw)
            for raw in _page(
                self.client,
                "list_artifacts",
                "artifacts",
                appId=appId,
                branchName=branchName,
                jobId=jobId,
            )
        ]
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", artifacts))
        self.sessionize(query_set)  # type: ignore[attr-defined]
        return query_set


class AmplifyJobModelMixin:
    """
    Poll one job until it finishes, and read a single step log.

    ``wait`` stops on ``SUCCEED``, ``FAILED``, or ``CANCELLED``. ``log_text``
    downloads the failed step when one exists, otherwise the latest step
    that has a log URL.
    """

    def wait(self, *, timeout: float = 900, interval: float = 5) -> Job:
        """
        Poll this job until it finishes.

        Keyword Args:
            timeout: Seconds to wait before raising ``TimeoutError``.
            interval: Seconds between reads.

        Returns:
            The job whose status is ``SUCCEED``, ``FAILED``, or ``CANCELLED``.

        Raises:
            ValueError: ``appId`` or ``branchName`` is missing, or a later
                read does not return the job.
            TimeoutError: The job is still running after ``timeout`` seconds.

        Side Effects:
            Reads the job until it finishes or the timeout elapses.

        """
        from botocraft.services.amplify import Job

        if not self.appId or not self.branchName:  # type: ignore[attr-defined]
            msg = "job is missing appId or branchName"
            raise ValueError(msg)
        job_id = self.summary.jobId  # type: ignore[attr-defined]
        deadline = time.monotonic() + timeout
        current: Job = cast("Job", self)
        while current.summary.status not in _TERMINAL_JOB_STATUSES:
            if time.monotonic() >= deadline:
                status = current.summary.status
                msg = f"job {job_id} still {status} after {timeout}s"
                raise TimeoutError(msg)
            time.sleep(interval)
            fetched = Job.objects.using(self.session).get(  # type: ignore[attr-defined]
                self.appId,  # type: ignore[attr-defined]
                self.branchName,  # type: ignore[attr-defined]
                job_id,
            )
            if fetched is None:
                msg = f"job {job_id} disappeared"
                raise ValueError(msg)
            current = fetched
        return current

    def log_text(self) -> str:
        """
        Download one step log for this job.

        A failed step is chosen before any other step. One URL is downloaded.

        Returns:
            The log body.

        Raises:
            ValueError: No step has a log URL.
            HTTPError: The log URL rejected the download.

        Side Effects:
            Sends one HTTP GET.

        """
        steps = list(self.steps or [])  # type: ignore[attr-defined]
        failed = [step for step in steps if step.status == "FAILED" and step.logUrl]
        chosen = failed[0] if failed else None
        if chosen is None:
            for step in reversed(steps):
                if step.logUrl:
                    chosen = step
                    break
        if chosen is None:
            msg = "job has no step log URL"
            raise ValueError(msg)
        return chosen.log_text()


class AmplifyStepModelMixin:
    """
    Download the log URL on one Amplify job step.
    """

    def log_text(self) -> str:
        """
        Download this step's log.

        Returns:
            The log body.

        Raises:
            ValueError: This step has no log URL.
            HTTPError: The log URL rejected the download.

        Side Effects:
            Sends one HTTP GET.

        """
        if not self.logUrl:  # type: ignore[attr-defined]
            msg = "step has no log URL"
            raise ValueError(msg)
        return _read_text(self.logUrl)  # type: ignore[attr-defined]
