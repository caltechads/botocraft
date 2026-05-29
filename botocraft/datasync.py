# ruff: noqa: N803,PLR0913
"""User-facing AWS DataSync workflow helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

import boto3

from botocraft.services.datasync import (
    DataSyncAgent,
    DataSyncAgentManager,
    DataSyncFilterRule,
    DataSyncLocationAzureBlob,
    DataSyncLocationAzureBlobManager,
    DataSyncLocationEfs,
    DataSyncLocationEfsManager,
    DataSyncLocationFsxLustre,
    DataSyncLocationFsxLustreManager,
    DataSyncLocationFsxOntap,
    DataSyncLocationFsxOntapManager,
    DataSyncLocationFsxOpenZfs,
    DataSyncLocationFsxOpenZfsManager,
    DataSyncLocationFsxWindows,
    DataSyncLocationFsxWindowsManager,
    DataSyncLocationHdfs,
    DataSyncLocationHdfsManager,
    DataSyncLocationNfs,
    DataSyncLocationNfsManager,
    DataSyncLocationObjectStorage,
    DataSyncLocationObjectStorageManager,
    DataSyncLocationS3,
    DataSyncLocationS3Manager,
    DataSyncLocationSmb,
    DataSyncLocationSmbManager,
    DataSyncManifestConfig,
    DataSyncOptions,
    DataSyncTask,
    DataSyncTaskExecution,
    DataSyncTaskExecutionManager,
    DataSyncTaskManager,
    TagListEntry,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

__all__ = [
    "DataSyncAccountContext",
    "DataSyncAgentFacade",
    "DataSyncCrossAccountSpec",
    "DataSyncExecutionFacade",
    "DataSyncJobDefinition",
    "DataSyncJobProgress",
    "DataSyncJobRun",
    "DataSyncLocationCatalog",
    "DataSyncTaskFacade",
    "DataSyncWorkspace",
    "assume_role_account_context",
]

#: Type variable for concrete generated DataSync location models.
LocationModel = TypeVar(
    "LocationModel",
    DataSyncLocationAzureBlob,
    DataSyncLocationEfs,
    DataSyncLocationFsxLustre,
    DataSyncLocationFsxOntap,
    DataSyncLocationFsxOpenZfs,
    DataSyncLocationFsxWindows,
    DataSyncLocationHdfs,
    DataSyncLocationNfs,
    DataSyncLocationObjectStorage,
    DataSyncLocationS3,
    DataSyncLocationSmb,
)
#: Type variable for generated DataSync models handled by CRUD facades.
CrudModel = TypeVar(
    "CrudModel",
    DataSyncAgent,
    DataSyncLocationAzureBlob,
    DataSyncLocationEfs,
    DataSyncLocationFsxLustre,
    DataSyncLocationFsxOntap,
    DataSyncLocationFsxOpenZfs,
    DataSyncLocationFsxWindows,
    DataSyncLocationHdfs,
    DataSyncLocationNfs,
    DataSyncLocationObjectStorage,
    DataSyncLocationS3,
    DataSyncLocationSmb,
    DataSyncTask,
)

#: Execution statuses that end polling in ``DataSyncJobRun.wait``.
_TERMINAL_EXECUTION_STATUSES = frozenset({"SUCCESS", "ERROR"})
#: Minimum number of colon-separated ARN parts.
_MIN_ARN_PARTS = 5
#: Index of the AWS account ID component inside an ARN.
_ARN_ACCOUNT_ID_INDEX = 4


def _bind_manager_session(manager: Any, session: boto3.session.Session | None) -> Any:
    """
    Bind a boto3 session to a manager when one is supplied.

    Args:
        manager: Generated DataSync manager instance or compatible fake.
        session: Session to bind, if any.

    Returns:
        Same manager instance with session applied when supported.

    Side Effects:
        Mutates manager session/client state when a session is supplied.

    """
    if session is None:
        return manager
    if hasattr(manager, "using"):
        manager.using(session)
        return manager
    manager.session = session
    return manager


def _model_arn(resource: Any, *attributes: str) -> str:
    """
    Resolve one ARN-like identifier from a DataSync resource.

    Args:
        resource: Resource model or wrapper.
        attributes: Candidate attribute names checked in order.

    Returns:
        First non-empty identifier found on resource.

    Raises:
        ValueError: Resource does not expose any requested identifier.

    """
    for attribute in attributes:
        value = getattr(resource, attribute, None)
        if value:
            return cast("str", value)
    msg = f"Could not determine identifier from {resource!r}."
    raise ValueError(msg)


def _bytes_progress_text(
    bytes_transferred: int | None,
    estimated_bytes_to_transfer: int | None,
) -> str | None:
    """
    Build best-effort byte progress text.

    Args:
        bytes_transferred: Completed bytes, if known.
        estimated_bytes_to_transfer: Total estimated bytes, if known.

    Returns:
        Progress text or ``None`` when no byte counters exist.

    """
    if bytes_transferred is None and estimated_bytes_to_transfer is None:
        return None
    if bytes_transferred is None:
        return f"?/{estimated_bytes_to_transfer} bytes"
    if estimated_bytes_to_transfer is None:
        return f"{bytes_transferred} bytes"
    return f"{bytes_transferred}/{estimated_bytes_to_transfer} bytes"


def _account_id_from_arn(arn: str | None) -> str | None:
    """
    Extract AWS account ID from one ARN when present.

    Args:
        arn: ARN-like string.

    Returns:
        Account ID portion of ARN, if parseable.

    """
    if not arn:
        return None
    parts = arn.split(":")
    if len(parts) < _MIN_ARN_PARTS:
        return None
    return parts[_ARN_ACCOUNT_ID_INDEX] or None


@dataclass(frozen=True)
class DataSyncAccountContext:
    """
    Named AWS account/session context for workflow routing.

    Args:
        name: Stable account alias used by workflow helpers.
        session: Boto3 session bound to this account context.
        account_id: Optional AWS account ID for documentation or validation.
        role_arn: Optional IAM role ARN used to produce this session.

    """

    #: Stable account alias used by workflow helpers.
    name: str
    #: Boto3 session bound to this account context.
    session: boto3.session.Session
    #: Optional AWS account ID for documentation or validation.
    account_id: str | None = None
    #: Optional IAM role ARN used to produce this session.
    role_arn: str | None = None


@dataclass(frozen=True)
class DataSyncCrossAccountSpec:
    """
    Explicit account mapping for one cross-account DataSync workflow.

    Args:
        task_account: Account that owns the DataSync task and executions.
        source_account: Account that owns the source location.
        destination_account: Account that owns the destination location.

    """

    #: Account that owns the DataSync task and executions.
    task_account: str
    #: Account that owns the source location.
    source_account: str
    #: Account that owns the destination location.
    destination_account: str


def assume_role_account_context(
    name: str,
    role_arn: str,
    *,
    session_name: str,
    base_session: boto3.session.Session | None = None,
) -> DataSyncAccountContext:
    """
    Create one account context from STS assumed-role credentials.

    Args:
        name: Stable account alias used by workflow helpers.
        role_arn: IAM role ARN to assume.

    Keyword Args:
        session_name: STS role-session name.
        base_session: Session used to call STS. Defaults to a fresh session.

    Returns:
        Account context backed by temporary assumed-role credentials.

    Side Effects:
        Calls AWS STS assume-role API.

    """
    caller_session = base_session or boto3.session.Session()
    sts = caller_session.client("sts")
    response = sts.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    credentials = response["Credentials"]
    session_kwargs: dict[str, Any] = {
        "aws_access_key_id": credentials["AccessKeyId"],
        "aws_secret_access_key": credentials["SecretAccessKey"],
        "aws_session_token": credentials["SessionToken"],
    }
    region_name = getattr(caller_session, "region_name", None)
    if region_name:
        session_kwargs["region_name"] = region_name
    session = boto3.session.Session(**session_kwargs)
    account_id = _account_id_from_arn(
        cast("dict[str, Any]", response.get("AssumedRoleUser", {})).get("Arn")
    )
    return DataSyncAccountContext(
        name=name,
        session=session,
        account_id=account_id,
        role_arn=role_arn,
    )


@dataclass(frozen=True)
class DataSyncJobProgress:
    """
    Immutable snapshot of DataSync job-run progress.

    Args:
        status: Current execution status.
        bytes_transferred: Bytes sent over network before compression.
        bytes_written: Logical bytes written to destination.
        estimated_bytes_to_transfer: Estimated logical bytes for transfer.
        files_transferred: Files or objects transferred so far.
        files_verified: Files or objects verified so far.
        files_skipped: Files or objects skipped so far.
        files_deleted: Files or objects deleted so far.
        estimated_files_to_transfer: Estimated files or objects to transfer.
        start_time: Time DataSync accepted execution start request.
        launch_time: Time execution actually launched.
        end_time: Time execution ended.
        error_code: AWS-reported error code, if any.
        error_detail: AWS-reported error detail, if any.

    """

    #: Current execution status.
    status: str | None
    #: Bytes sent over network before compression.
    bytes_transferred: int | None
    #: Logical bytes written to destination.
    bytes_written: int | None
    #: Estimated logical bytes for transfer.
    estimated_bytes_to_transfer: int | None
    #: Files or objects transferred so far.
    files_transferred: int | None
    #: Files or objects verified so far.
    files_verified: int | None
    #: Files or objects skipped so far.
    files_skipped: int | None
    #: Files or objects deleted so far.
    files_deleted: int | None
    #: Estimated files or objects to transfer.
    estimated_files_to_transfer: int | None
    #: Time DataSync accepted execution start request.
    start_time: datetime | None
    #: Time execution actually launched.
    launch_time: datetime | None
    #: Time execution ended.
    end_time: datetime | None
    #: AWS-reported error code, if any.
    error_code: str | None
    #: AWS-reported error detail, if any.
    error_detail: str | None


class DataSyncJobRun:
    """
    Session-aware wrapper around one DataSync task execution.

    Args:
        execution: Backing generated DataSync task execution model.
        workspace: Workspace used to refresh and cancel this run.

    """

    def __init__(
        self,
        execution: DataSyncTaskExecution,
        workspace: DataSyncWorkspace,
        *,
        account_name: str | None = None,
    ) -> None:
        """
        Initialize one run wrapper.

        Args:
            execution: Backing generated DataSync task execution model.
            workspace: Workspace used to refresh and cancel this run.

        Keyword Args:
            account_name: Optional account alias used for execution lifecycle APIs.

        """
        #: Backing generated DataSync task execution model.
        self.execution = execution
        #: Workspace used to refresh and cancel this run.
        self.workspace = workspace
        #: Optional account alias used for execution lifecycle APIs.
        self.account_name = account_name

    @property
    def arn(self) -> str | None:
        """
        Return execution ARN.

        Returns:
            Execution ARN when present.

        """
        return self.execution.TaskExecutionArn

    @property
    def status(self) -> str | None:
        """
        Return current execution status.

        Returns:
            Current execution status when present.

        """
        return self.execution.Status

    @property
    def is_terminal(self) -> bool:
        """
        Return whether execution reached terminal state.

        Returns:
            ``True`` when status is terminal.

        """
        return self.status in _TERMINAL_EXECUTION_STATUSES

    @property
    def succeeded(self) -> bool:
        """
        Return whether execution succeeded.

        Returns:
            ``True`` when status is ``SUCCESS``.

        """
        return self.status == "SUCCESS"

    @property
    def failed(self) -> bool:
        """
        Return whether execution failed.

        Returns:
            ``True`` when status is ``ERROR``.

        """
        return self.status == "ERROR"

    def refresh(self) -> DataSyncJobRun:
        """
        Refresh execution state from AWS.

        Returns:
            Freshly hydrated job run wrapper.

        Raises:
            ValueError: Execution does not have an ARN.

        """
        execution_arn = _model_arn(self.execution, "TaskExecutionArn")
        refreshed = self.workspace.executions_in(self.account_name).get(execution_arn)
        if refreshed is None:
            msg = f"Task execution {execution_arn} no longer exists."
            raise ValueError(msg)
        return refreshed

    def cancel(self) -> DataSyncJobRun:
        """
        Cancel execution and refresh once.

        Returns:
            Refreshed job run wrapper.

        Side Effects:
            Calls AWS DataSync cancel API.

        """
        execution_arn = _model_arn(self.execution, "TaskExecutionArn")
        self.workspace.executions_in(self.account_name).cancel(execution_arn)
        return self.refresh()

    def wait(
        self,
        poll_interval_seconds: float = 10.0,
        timeout_seconds: float | None = None,
    ) -> DataSyncJobRun:
        """
        Poll until execution reaches terminal state.

        Args:
            poll_interval_seconds: Delay between refresh calls.
            timeout_seconds: Optional wall-clock timeout.

        Returns:
            Terminal execution wrapper.

        Raises:
            TimeoutError: Execution does not finish before timeout.

        """
        started_at = time.monotonic()
        current: DataSyncJobRun = self
        while True:
            current = current.refresh()
            if current.is_terminal:
                return current
            if (
                timeout_seconds is not None
                and time.monotonic() - started_at >= timeout_seconds
            ):
                msg = (
                    f"Timed out waiting for DataSync task execution "
                    f"{current.arn} to finish."
                )
                raise TimeoutError(msg)
            time.sleep(poll_interval_seconds)

    def progress(self) -> DataSyncJobProgress:
        """
        Return immutable progress snapshot.

        Returns:
            Snapshot of selected execution counters and timestamps.

        """
        result = getattr(self.execution, "Result", None)
        return DataSyncJobProgress(
            status=self.execution.Status,
            bytes_transferred=self.execution.BytesTransferred,
            bytes_written=self.execution.BytesWritten,
            estimated_bytes_to_transfer=self.execution.EstimatedBytesToTransfer,
            files_transferred=self.execution.FilesTransferred,
            files_verified=self.execution.FilesVerified,
            files_skipped=self.execution.FilesSkipped,
            files_deleted=self.execution.FilesDeleted,
            estimated_files_to_transfer=self.execution.EstimatedFilesToTransfer,
            start_time=self.execution.StartTime,
            launch_time=self.execution.LaunchTime,
            end_time=self.execution.EndTime,
            error_code=getattr(result, "ErrorCode", None),
            error_detail=getattr(result, "ErrorDetail", None),
        )

    def summary(self) -> str:
        """
        Return one-line human-readable run summary.

        Returns:
            Summary string built from best-effort counters and errors.

        """
        progress = self.progress()
        parts = [progress.status or "UNKNOWN"]
        if byte_text := _bytes_progress_text(
            progress.bytes_transferred,
            progress.estimated_bytes_to_transfer,
        ):
            parts.append(byte_text)
        if progress.files_transferred is not None:
            parts.append(f"{progress.files_transferred} files transferred")
        if progress.error_code:
            parts.append(progress.error_code)
        if progress.error_detail:
            parts.append(progress.error_detail)
        return " | ".join(parts)


class DataSyncJobDefinition:
    """
    Session-aware wrapper around one DataSync task definition.

    Args:
        task: Backing generated DataSync task model.
        workspace: Workspace used to persist and run this task.

    """

    def __init__(
        self,
        task: DataSyncTask,
        workspace: DataSyncWorkspace,
        account_spec: DataSyncCrossAccountSpec | None = None,
    ) -> None:
        """
        Initialize one job-definition wrapper.

        Args:
            task: Backing generated DataSync task model.
            workspace: Workspace used to persist and run this task.
            account_spec: Optional cross-account routing definition.

        """
        #: Backing generated DataSync task model.
        self.task = task
        #: Workspace used to persist and run this task.
        self.workspace = workspace
        #: Optional cross-account routing definition.
        self.account_spec = account_spec

    def _task_facade(self) -> DataSyncTaskFacade:
        """
        Return task facade routed for this job definition.

        Returns:
            Task facade bound to task-account session when configured.

        """
        if self.account_spec is None:
            return self.workspace.tasks
        return self.workspace.tasks_in(
            self.account_spec.task_account,
            account_spec=self.account_spec,
        )

    def _execution_facade(self) -> DataSyncExecutionFacade:
        """
        Return execution facade routed for this job definition.

        Returns:
            Execution facade bound to task-account session when configured.

        """
        if self.account_spec is None:
            return self.workspace.executions
        return self.workspace.executions_in(self.account_spec.task_account)

    @property
    def arn(self) -> str | None:
        """
        Return task ARN.

        Returns:
            Task ARN when present.

        """
        return self.task.TaskArn

    @property
    def name(self) -> str | None:
        """
        Return task name.

        Returns:
            Task name when present.

        """
        return self.task.Name

    def refresh(self) -> DataSyncJobDefinition:
        """
        Refresh task definition from AWS.

        Returns:
            Freshly hydrated job definition wrapper.

        Raises:
            ValueError: Task does not have an ARN.

        """
        task_arn = _model_arn(self.task, "TaskArn")
        refreshed = self._task_facade().get(task_arn)
        if refreshed is None:
            msg = f"Task {task_arn} no longer exists."
            raise ValueError(msg)
        return refreshed

    def update(self) -> DataSyncJobDefinition:
        """
        Persist current task model and return refreshed wrapper.

        Returns:
            Updated task definition wrapper.

        Side Effects:
            Calls AWS DataSync update-task API through generated manager.

        """
        return self._task_facade().update(self.task)

    def start(
        self,
        *,
        OverrideOptions: DataSyncOptions | None = None,
        Includes: list[DataSyncFilterRule] | None = None,
        Excludes: list[DataSyncFilterRule] | None = None,
        ManifestConfig: DataSyncManifestConfig | None = None,
        TaskReportConfig: Any | None = None,
        Tags: list[TagListEntry] | None = None,
    ) -> DataSyncJobRun:
        """
        Start one execution for this task.

        Keyword Args:
            OverrideOptions: Execution-time task option overrides.
            Includes: Execution-time include filters.
            Excludes: Execution-time exclude filters.
            ManifestConfig: Execution-time manifest configuration.
            TaskReportConfig: Execution-time task report configuration.
            Tags: Execution-time tags applied to resulting execution.

        Returns:
            Started job-run wrapper.

        Side Effects:
            Calls AWS DataSync start-task-execution API.

        """
        return self._task_facade().start(
            self.task,
            OverrideOptions=OverrideOptions,
            Includes=Includes,
            Excludes=Excludes,
            ManifestConfig=ManifestConfig,
            TaskReportConfig=TaskReportConfig,
            Tags=Tags,
        )

    def latest_run(self) -> DataSyncJobRun | None:
        """
        Return most recent known execution for this task.

        Returns:
            Latest execution wrapper when found, otherwise ``None``.

        """
        if self.task.CurrentTaskExecutionArn:
            return self._execution_facade().get(self.task.CurrentTaskExecutionArn)
        runs = self.runs()
        if not runs:
            return None
        latest = max(
            runs,
            key=lambda execution: cast(
                "DataSyncTaskExecution",
                execution,
            ).StartTime
            or datetime.min.replace(tzinfo=timezone.utc),
        )
        account_name = (
            self.account_spec.task_account if self.account_spec is not None else None
        )
        return DataSyncJobRun(
            cast("DataSyncTaskExecution", latest),
            self.workspace,
            account_name=account_name,
        )

    def runs(self) -> PrimaryBoto3ModelQuerySet:
        """
        List executions for this task.

        Returns:
            Queryset of generated DataSync task execution models.

        """
        task_arn = _model_arn(self.task, "TaskArn")
        return self._execution_facade().list(task_arn)

    def delete(self) -> None:
        """
        Delete this task definition.

        Side Effects:
            Calls AWS DataSync delete-task API.

        """
        self._task_facade().delete(self.task)

    def validate_cross_account_s3(self) -> None:
        """
        Validate first-slice cross-account S3 requirements.

        Returns:
            ``None`` when validation succeeds.

        Raises:
            ValueError: Required account mappings, S3 locations, or access roles are
                missing.

        """
        if self.account_spec is None:
            return
        self.workspace.account(self.account_spec.task_account)
        self.workspace.account(self.account_spec.source_account)
        self.workspace.account(self.account_spec.destination_account)

        manifest_config = getattr(self.task, "ManifestConfig", None)
        manifest_s3 = getattr(manifest_config, "Source", None)
        manifest_bucket = getattr(manifest_s3, "S3", None)
        if manifest_bucket is not None and not getattr(
            manifest_bucket,
            "BucketAccessRoleArn",
            None,
        ):
            msg = (
                "Cross-account DataSync manifest S3 config requires "
                "BucketAccessRoleArn."
            )
            raise ValueError(msg)

        if self.account_spec.source_account == self.account_spec.destination_account:
            return

        source = self.workspace.location_in(
            self.account_spec.source_account,
            _model_arn(self.task, "SourceLocationArn"),
        )
        destination = self.workspace.location_in(
            self.account_spec.destination_account,
            _model_arn(self.task, "DestinationLocationArn"),
        )
        for label, location in (("source", source), ("destination", destination)):
            if not isinstance(location, DataSyncLocationS3):
                msg = (
                    f"Cross-account DataSync currently supports S3 locations only; "
                    f"{label} location is not S3."
                )
                raise TypeError(msg)
            s3_config = getattr(location, "S3Config", None)
            if not getattr(s3_config, "BucketAccessRoleArn", None):
                msg = (
                    f"Cross-account DataSync {label} S3 location requires "
                    f"BucketAccessRoleArn."
                )
                raise ValueError(msg)


class _CrudFacade(Generic[CrudModel]):
    """
    Shared CRUD wrapper around one generated manager.

    Args:
        manager_factory: Factory that returns generated manager instance.
        session: Session to bind to created manager.

    """

    def __init__(
        self,
        manager_factory: Callable[[], Any],
        session: boto3.session.Session | None,
    ) -> None:
        """
        Initialize one generic CRUD facade.

        Args:
            manager_factory: Factory that returns generated manager instance.
            session: Session to bind to created manager.

        """
        #: Factory that returns generated manager instance.
        self._manager_factory = manager_factory
        #: Session to bind to created manager.
        self._session = session
        #: Cached generated manager with bound session when provided.
        self.manager = _bind_manager_session(self._manager_factory(), self._session)

    def create(self, model: CrudModel) -> CrudModel:
        """
        Create one resource.

        Args:
            model: Generated DataSync model to create.

        Returns:
            Created resource model.

        Side Effects:
            Calls underlying AWS create API.

        """
        return cast("CrudModel", self.manager.create(model))

    def get(self, resource_arn: str) -> CrudModel | None:
        """
        Retrieve one resource by ARN.

        Args:
            resource_arn: Resource ARN.

        Returns:
            Hydrated resource when found.

        """
        return cast("CrudModel | None", self.manager.get(resource_arn))

    def list(self) -> PrimaryBoto3ModelQuerySet:
        """
        List resources for this manager.

        Returns:
            Queryset of generated DataSync models.

        """
        return cast("PrimaryBoto3ModelQuerySet", self.manager.list())

    def update(self, model: CrudModel) -> CrudModel:
        """
        Update one resource.

        Args:
            model: Generated DataSync model to update.

        Returns:
            Updated resource model.

        Side Effects:
            Calls underlying AWS update API.

        """
        return cast("CrudModel", self.manager.update(model))

    def delete(self, resource_or_arn: CrudModel | str) -> None:
        """
        Delete one resource by model or ARN.

        Args:
            resource_or_arn: Generated model or raw ARN.

        Side Effects:
            Calls underlying AWS delete API.

        """
        if isinstance(resource_or_arn, str):
            resource_arn = resource_or_arn
        else:
            resource_arn = _model_arn(
                resource_or_arn,
                "AgentArn",
                "LocationArn",
                "TaskArn",
            )
        self.manager.delete(resource_arn)


class DataSyncAgentFacade(_CrudFacade[DataSyncAgent]):
    """
    Session-aware CRUD wrapper for DataSync agents.

    Args:
        manager_factory: Factory that returns ``DataSyncAgentManager``.
        session: Session to bind to created manager.

    """


class _LocationFacade(_CrudFacade[LocationModel]):
    """
    Session-aware CRUD wrapper for one concrete DataSync location type.

    Args:
        manager_factory: Factory that returns concrete location manager.
        session: Session to bind to created manager.

    """


class DataSyncLocationCatalog:
    """
    Session-bound catalog of typed DataSync location facades.

    Args:
        manager_factories: Mapping of location-type names to manager factories.
        session: Session to bind to created managers.

    """

    def __init__(
        self,
        manager_factories: dict[str, Callable[[], Any]],
        session: boto3.session.Session | None,
    ) -> None:
        """
        Initialize typed location catalog.

        Args:
            manager_factories: Mapping of location-type names to manager factories.
            session: Session to bind to created managers.

        """
        #: Mapping of location-type names to manager factories.
        self._manager_factories = manager_factories
        #: Session to bind to created managers.
        self._session = session

    def _facade(self, name: str) -> _LocationFacade[Any]:
        """
        Build one typed location facade.

        Args:
            name: Location-type key in manager-factory map.

        Returns:
            Typed location facade.

        """
        return _LocationFacade(self._manager_factories[name], self._session)

    @cached_property
    def azure_blob(self) -> _LocationFacade[DataSyncLocationAzureBlob]:
        """
        Return Azure Blob location facade.

        Returns:
            Location facade for Azure Blob locations.

        """
        return self._facade("azure_blob")

    @cached_property
    def efs(self) -> _LocationFacade[DataSyncLocationEfs]:
        """
        Return EFS location facade.

        Returns:
            Location facade for EFS locations.

        """
        return self._facade("efs")

    @cached_property
    def fsx_lustre(self) -> _LocationFacade[DataSyncLocationFsxLustre]:
        """
        Return FSx Lustre location facade.

        Returns:
            Location facade for FSx Lustre locations.

        """
        return self._facade("fsx_lustre")

    @cached_property
    def fsx_ontap(self) -> _LocationFacade[DataSyncLocationFsxOntap]:
        """
        Return FSx ONTAP location facade.

        Returns:
            Location facade for FSx ONTAP locations.

        """
        return self._facade("fsx_ontap")

    @cached_property
    def fsx_openzfs(self) -> _LocationFacade[DataSyncLocationFsxOpenZfs]:
        """
        Return FSx OpenZFS location facade.

        Returns:
            Location facade for FSx OpenZFS locations.

        """
        return self._facade("fsx_openzfs")

    @cached_property
    def fsx_windows(self) -> _LocationFacade[DataSyncLocationFsxWindows]:
        """
        Return FSx Windows location facade.

        Returns:
            Location facade for FSx Windows locations.

        """
        return self._facade("fsx_windows")

    @cached_property
    def hdfs(self) -> _LocationFacade[DataSyncLocationHdfs]:
        """
        Return HDFS location facade.

        Returns:
            Location facade for HDFS locations.

        """
        return self._facade("hdfs")

    @cached_property
    def nfs(self) -> _LocationFacade[DataSyncLocationNfs]:
        """
        Return NFS location facade.

        Returns:
            Location facade for NFS locations.

        """
        return self._facade("nfs")

    @cached_property
    def object_storage(self) -> _LocationFacade[DataSyncLocationObjectStorage]:
        """
        Return object-storage location facade.

        Returns:
            Location facade for object-storage locations.

        """
        return self._facade("object_storage")

    @cached_property
    def s3(self) -> _LocationFacade[DataSyncLocationS3]:
        """
        Return S3 location facade.

        Returns:
            Location facade for S3 locations.

        """
        return self._facade("s3")

    @cached_property
    def smb(self) -> _LocationFacade[DataSyncLocationSmb]:
        """
        Return SMB location facade.

        Returns:
            Location facade for SMB locations.

        """
        return self._facade("smb")


class DataSyncExecutionFacade:
    """
    Session-aware wrapper for DataSync task executions.

    Args:
        manager_factory: Factory that returns ``DataSyncTaskExecutionManager``.
        workspace: Workspace used to wrap execution models.

    """

    def __init__(
        self,
        manager_factory: Callable[[], DataSyncTaskExecutionManager],
        workspace: DataSyncWorkspace,
        session: boto3.session.Session | None = None,
        account_name: str | None = None,
    ) -> None:
        """
        Initialize execution facade.

        Args:
            manager_factory: Factory that returns ``DataSyncTaskExecutionManager``.
            workspace: Workspace used to wrap execution models.

        Keyword Args:
            session: Session to bind to created manager.
            account_name: Optional account alias attached to wrapped runs.

        """
        #: Factory that returns ``DataSyncTaskExecutionManager``.
        self._manager_factory = manager_factory
        #: Workspace used to wrap execution models.
        self._workspace = workspace
        #: Session to bind to created manager.
        self._session = session if session is not None else self._workspace.session
        #: Optional account alias attached to wrapped runs.
        self._account_name = account_name
        #: Cached generated execution manager with bound session.
        self.manager = cast(
            "DataSyncTaskExecutionManager",
            _bind_manager_session(self._manager_factory(), self._session),
        )

    def get(self, task_execution_arn: str) -> DataSyncJobRun | None:
        """
        Retrieve one execution wrapper by ARN.

        Args:
            task_execution_arn: Execution ARN.

        Returns:
            Wrapped execution when found.

        """
        execution = self.manager.get(task_execution_arn)
        if execution is None:
            return None
        return DataSyncJobRun(
            execution,
            self._workspace,
            account_name=self._account_name,
        )

    def list(self, task_arn: str | None = None) -> PrimaryBoto3ModelQuerySet:
        """
        List generated execution models.

        Args:
            task_arn: Optional task ARN filter.

        Returns:
            Queryset of generated execution models.

        """
        return cast("PrimaryBoto3ModelQuerySet", self.manager.list(TaskArn=task_arn))

    def cancel(self, run_or_arn: DataSyncJobRun | str) -> None:
        """
        Cancel one execution by wrapper or ARN.

        Args:
            run_or_arn: Job-run wrapper or raw execution ARN.

        Side Effects:
            Calls AWS DataSync cancel-task-execution API.

        """
        execution_arn = run_or_arn if isinstance(run_or_arn, str) else _model_arn(
            run_or_arn.execution,
            "TaskExecutionArn",
        )
        self.manager.cancel(execution_arn)


class DataSyncTaskFacade:
    """
    Session-aware wrapper for DataSync task definitions and starts.

    Args:
        manager_factory: Factory that returns ``DataSyncTaskManager``.
        workspace: Workspace used to wrap task and execution models.

    """

    def __init__(
        self,
        manager_factory: Callable[[], DataSyncTaskManager],
        workspace: DataSyncWorkspace,
        session: boto3.session.Session | None = None,
        account_name: str | None = None,
        account_spec: DataSyncCrossAccountSpec | None = None,
    ) -> None:
        """
        Initialize task facade.

        Args:
            manager_factory: Factory that returns ``DataSyncTaskManager``.
            workspace: Workspace used to wrap task and execution models.

        Keyword Args:
            session: Session to bind to created manager.
            account_name: Optional account alias for execution lifecycle APIs.
            account_spec: Optional cross-account routing definition.

        """
        #: Factory that returns ``DataSyncTaskManager``.
        self._manager_factory = manager_factory
        #: Workspace used to wrap task and execution models.
        self._workspace = workspace
        #: Session to bind to created manager.
        self._session = session if session is not None else self._workspace.session
        #: Optional account alias for execution lifecycle APIs.
        self._account_name = account_name
        #: Optional cross-account routing definition.
        self._account_spec = account_spec
        #: Cached generated task manager with bound session.
        self.manager = cast(
            "DataSyncTaskManager",
            _bind_manager_session(self._manager_factory(), self._session),
        )

    def create(self, model: DataSyncTask) -> DataSyncJobDefinition:
        """
        Create one DataSync task and wrap it.

        Args:
            model: Generated DataSync task model.

        Returns:
            Wrapped task definition.

        Side Effects:
            Calls AWS DataSync create-task API.

        """
        task = cast("DataSyncTask", self.manager.create(model))
        return DataSyncJobDefinition(
            task,
            self._workspace,
            account_spec=self._account_spec,
        )

    def get(self, task_arn: str) -> DataSyncJobDefinition | None:
        """
        Retrieve one DataSync task wrapper by ARN.

        Args:
            task_arn: Task ARN.

        Returns:
            Wrapped task when found.

        """
        task = self.manager.get(task_arn)
        if task is None:
            return None
        return DataSyncJobDefinition(
            task,
            self._workspace,
            account_spec=self._account_spec,
        )

    def list(self) -> PrimaryBoto3ModelQuerySet:
        """
        List generated DataSync task models.

        Returns:
            Queryset of generated task models.

        """
        return cast("PrimaryBoto3ModelQuerySet", self.manager.list())

    def update(self, model: DataSyncTask) -> DataSyncJobDefinition:
        """
        Update one DataSync task and wrap it.

        Args:
            model: Generated DataSync task model.

        Returns:
            Wrapped updated task definition.

        Side Effects:
            Calls AWS DataSync update-task API.

        """
        task = cast("DataSyncTask", self.manager.update(model))
        return DataSyncJobDefinition(
            task,
            self._workspace,
            account_spec=self._account_spec,
        )

    def delete(self, task_or_arn: DataSyncTask | str) -> None:
        """
        Delete one DataSync task by model or ARN.

        Args:
            task_or_arn: Generated task model or raw task ARN.

        Side Effects:
            Calls AWS DataSync delete-task API.

        """
        task_arn = (
            task_or_arn
            if isinstance(task_or_arn, str)
            else _model_arn(task_or_arn, "TaskArn")
        )
        self.manager.delete(task_arn)

    def start(
        self,
        task_or_arn: DataSyncTask | str,
        **start_overrides: Any,
    ) -> DataSyncJobRun:
        """
        Start one execution for a task.

        Args:
            task_or_arn: Generated task model or raw task ARN.

        Keyword Args:
            start_overrides: Same overrides accepted by generated
                ``start_task_execution``.

        Returns:
            Wrapped started execution.

        Side Effects:
            Calls AWS DataSync start-task-execution API.

        Raises:
            ValueError: Generated manager does not return an execution model.

        """
        task_arn = (
            task_or_arn
            if isinstance(task_or_arn, str)
            else _model_arn(task_or_arn, "TaskArn")
        )
        start_overrides = {
            key: value for key, value in start_overrides.items() if value is not None
        }
        execution = self.manager.start_task_execution(task_arn, **start_overrides)
        if execution is None:
            msg = f"Task {task_arn} did not return an execution."
            raise ValueError(msg)
        return DataSyncJobRun(
            execution,
            self._workspace,
            account_name=self._account_name,
        )


class DataSyncWorkspace:
    """
    Session-bound entrypoint for DataSync workflow operations.

    Args:
        session: Optional boto3 session used by all workflow helpers.
        _agent_manager_factory: Private test hook for custom agent manager factory.
        _task_manager_factory: Private test hook for custom task manager factory.
        _execution_manager_factory: Private test hook for custom execution manager
            factory.
        _location_manager_factories: Private test hook for custom location manager
            factories.

    """

    def __init__(
        self,
        session: boto3.session.Session | None = None,
        accounts: dict[str, DataSyncAccountContext] | None = None,
        *,
        _agent_manager_factory: Callable[[], Any] | None = None,
        _task_manager_factory: Callable[[], Any] | None = None,
        _execution_manager_factory: Callable[[], Any] | None = None,
        _location_manager_factories: dict[str, Callable[[], Any]] | None = None,
    ) -> None:
        """
        Initialize workflow workspace.

        Args:
            session: Optional boto3 session used by all workflow helpers.

        Keyword Args:
            accounts: Optional named account contexts for explicit cross-account
                routing.
            _agent_manager_factory: Private test hook for custom agent manager factory.
            _task_manager_factory: Private test hook for custom task manager factory.
            _execution_manager_factory: Private test hook for custom execution
                manager factory.
            _location_manager_factories: Private test hook for custom location
                manager factories.

        """
        #: Optional boto3 session used by all workflow helpers.
        self.session = session
        #: Optional named account contexts for explicit cross-account routing.
        self.accounts = accounts or {}
        #: Private test hook for custom agent manager factory.
        self._agent_manager_factory = _agent_manager_factory or DataSyncAgentManager
        #: Private test hook for custom task manager factory.
        self._task_manager_factory = _task_manager_factory or DataSyncTaskManager
        #: Private test hook for custom execution manager factory.
        self._execution_manager_factory = (
            _execution_manager_factory or DataSyncTaskExecutionManager
        )
        #: Private test hook for custom location manager factories.
        self._location_manager_factories = _location_manager_factories or {
            "azure_blob": DataSyncLocationAzureBlobManager,
            "efs": DataSyncLocationEfsManager,
            "fsx_lustre": DataSyncLocationFsxLustreManager,
            "fsx_ontap": DataSyncLocationFsxOntapManager,
            "fsx_openzfs": DataSyncLocationFsxOpenZfsManager,
            "fsx_windows": DataSyncLocationFsxWindowsManager,
            "hdfs": DataSyncLocationHdfsManager,
            "nfs": DataSyncLocationNfsManager,
            "object_storage": DataSyncLocationObjectStorageManager,
            "s3": DataSyncLocationS3Manager,
            "smb": DataSyncLocationSmbManager,
        }

    @cached_property
    def agents(self) -> DataSyncAgentFacade:
        """
        Return agent facade.

        Returns:
            Session-aware agent facade.

        """
        return DataSyncAgentFacade(self._agent_manager_factory, self.session)

    def account(self, name: str) -> DataSyncAccountContext:
        """
        Return one configured account context by name.

        Args:
            name: Configured account alias.

        Returns:
            Matching account context.

        Raises:
            ValueError: Account alias is not configured on this workspace.

        """
        context = self.accounts.get(name)
        if context is None:
            msg = f"DataSync account context {name!r} is not configured."
            raise ValueError(msg)
        return context

    def _account_session(self, name: str | None) -> boto3.session.Session | None:
        """
        Resolve one session for default or named account routing.

        Args:
            name: Optional configured account alias.

        Returns:
            Named account session when supplied, otherwise default workspace session.

        """
        if name is None:
            return self.session
        return self.account(name).session

    def agents_in(self, name: str) -> DataSyncAgentFacade:
        """
        Return an agent facade bound to one named account session.

        Args:
            name: Configured account alias.

        Returns:
            Fresh agent facade for the selected account.

        """
        return DataSyncAgentFacade(
            self._agent_manager_factory,
            self._account_session(name),
        )

    @cached_property
    def locations(self) -> DataSyncLocationCatalog:
        """
        Return typed location catalog.

        Returns:
            Session-aware location catalog.

        """
        return DataSyncLocationCatalog(self._location_manager_factories, self.session)

    def locations_in(self, name: str) -> DataSyncLocationCatalog:
        """
        Return a location catalog bound to one named account session.

        Args:
            name: Configured account alias.

        Returns:
            Fresh location catalog for the selected account.

        """
        return DataSyncLocationCatalog(
            self._location_manager_factories,
            self._account_session(name),
        )

    @cached_property
    def tasks(self) -> DataSyncTaskFacade:
        """
        Return task facade.

        Returns:
            Session-aware task facade.

        """
        return DataSyncTaskFacade(self._task_manager_factory, self)

    def tasks_in(
        self,
        name: str | None,
        *,
        account_spec: DataSyncCrossAccountSpec | None = None,
    ) -> DataSyncTaskFacade:
        """
        Return a task facade bound to default or named account session.

        Args:
            name: Optional configured account alias.

        Keyword Args:
            account_spec: Optional cross-account routing definition preserved on job
                wrappers returned by the facade.

        Returns:
            Fresh task facade for the selected account.

        """
        return DataSyncTaskFacade(
            self._task_manager_factory,
            self,
            session=self._account_session(name),
            account_name=name,
            account_spec=account_spec,
        )

    @cached_property
    def executions(self) -> DataSyncExecutionFacade:
        """
        Return execution facade.

        Returns:
            Session-aware execution facade.

        """
        return DataSyncExecutionFacade(self._execution_manager_factory, self)

    def executions_in(self, name: str | None) -> DataSyncExecutionFacade:
        """
        Return an execution facade bound to default or named account session.

        Args:
            name: Optional configured account alias.

        Returns:
            Fresh execution facade for the selected account.

        """
        return DataSyncExecutionFacade(
            self._execution_manager_factory,
            self,
            session=self._account_session(name),
            account_name=name,
        )

    def location_in(self, account_name: str, location_arn: str) -> Any:
        """
        Resolve one DataSync location from a specific account context.

        Args:
            account_name: Configured account alias that owns the location.
            location_arn: Location ARN to resolve.

        Returns:
            Matching generated location model.

        Raises:
            ValueError: Location cannot be found in that account context.

        """
        catalog = self.locations_in(account_name)
        for location_type in self._location_manager_factories:
            facade = cast("Any", getattr(catalog, location_type))
            location = facade.get(location_arn)
            if location is not None:
                return location
        msg = (
            f"DataSync location {location_arn!r} is not available in account "
            f"{account_name!r}."
        )
        raise ValueError(msg)

    def define_job(self, task: DataSyncTask) -> DataSyncJobDefinition:
        """
        Create one DataSync task definition and wrap it.

        Args:
            task: Generated DataSync task model to create.

        Returns:
            Wrapped task definition.

        Side Effects:
            Calls AWS DataSync create-task API.

        """
        return self.tasks.create(task)

    def define_cross_account_job(
        self,
        task: DataSyncTask,
        *,
        spec: DataSyncCrossAccountSpec,
    ) -> DataSyncJobDefinition:
        """
        Create one cross-account DataSync task definition and validate it.

        Args:
            task: Generated DataSync task model to create.

        Keyword Args:
            spec: Explicit account mapping for this workflow.

        Returns:
            Wrapped cross-account task definition.

        Side Effects:
            Calls AWS DataSync create-task API in the task account.

        Raises:
            ValueError: Cross-account validation fails for the created task.

        """
        job = self.tasks_in(
            spec.task_account,
            account_spec=spec,
        ).create(task)
        job.validate_cross_account_s3()
        return job

    def job(self, task_arn: str) -> DataSyncJobDefinition | None:
        """
        Retrieve one job definition wrapper by task ARN.

        Args:
            task_arn: Task ARN.

        Returns:
            Wrapped task definition when found.

        """
        return self.tasks.get(task_arn)

    def run(
        self,
        task_execution_arn: str,
        *,
        account_name: str | None = None,
    ) -> DataSyncJobRun | None:
        """
        Retrieve one job-run wrapper by execution ARN.

        Args:
            task_execution_arn: Task execution ARN.

        Keyword Args:
            account_name: Optional configured account alias.

        Returns:
            Wrapped execution when found.

        """
        return self.executions_in(account_name).get(task_execution_arn)
