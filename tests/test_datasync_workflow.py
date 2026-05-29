# ruff: noqa: E501,N803,PLR0913,PLW0108,SLF001,PLR2004
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, cast

import pytest

from botocraft.datasync import (
    DataSyncAccountContext,
    DataSyncCrossAccountSpec,
    DataSyncJobDefinition,
    DataSyncJobProgress,
    DataSyncJobRun,
    DataSyncWorkspace,
    assume_role_account_context,
)
from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.common import Tag
from botocraft.services.datasync import (
    DataSyncAgent,
    DataSyncLocationS3,
    DataSyncManifestConfig,
    DataSyncOptions,
    DataSyncS3Config,
    DataSyncTask,
    DataSyncTaskExecution,
    DataSyncTaskExecutionResultDetail,
    S3ManifestConfig,
    SourceManifestConfig,
)


def make_task(task_arn: str, *, current_execution_arn: str | None = None) -> DataSyncTask:
    kwargs: dict[str, Any] = {
        "TaskArn": task_arn,
        "Name": "demo-task",
        "SourceLocationArn": "arn:aws:datasync:us-west-2:123456789012:location/src",
        "DestinationLocationArn": "arn:aws:datasync:us-west-2:123456789012:location/dst",
        "Tags": [Tag(Key="Environment", Value="test")],
    }
    if current_execution_arn is not None:
        kwargs["CurrentTaskExecutionArn"] = current_execution_arn
    return DataSyncTask(**kwargs)


def make_execution(
    execution_arn: str,
    *,
    status: str = "TRANSFERRING",
    estimated_bytes: int | None = 100,
    bytes_transferred: int | None = 25,
    files_transferred: int | None = 2,
    error_code: str | None = None,
    error_detail: str | None = None,
) -> DataSyncTaskExecution:
    kwargs: dict[str, Any] = {
        "TaskExecutionArn": execution_arn,
        "Status": cast("Any", status),
        "EstimatedBytesToTransfer": estimated_bytes,
        "BytesTransferred": bytes_transferred,
        "BytesWritten": bytes_transferred,
        "EstimatedFilesToTransfer": 10,
        "FilesTransferred": files_transferred,
        "FilesVerified": 1,
        "FilesSkipped": 0,
        "FilesDeleted": 0,
        "StartTime": datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc),
        "LaunchTime": datetime(2026, 5, 29, 12, 1, tzinfo=timezone.utc),
        "Options": DataSyncOptions(BytesPerSecond=1024),
    }
    if error_code is not None:
        kwargs["Result"] = DataSyncTaskExecutionResultDetail(
            ErrorCode=error_code,
            ErrorDetail=error_detail,
        )
    return DataSyncTaskExecution(**kwargs)


class FakeTaskManager:
    def __init__(self) -> None:
        self.session: Any = None
        self.created: list[DataSyncTask] = []
        self.updated: list[DataSyncTask] = []
        self.deleted: list[str] = []
        self.started: list[tuple[str, dict[str, Any]]] = []
        self._get_results: dict[str, DataSyncTask] = {}
        self._list_result = PrimaryBoto3ModelQuerySet([])
        self._start_result: DataSyncTaskExecution | None = None

    def create(self, model: DataSyncTask) -> DataSyncTask:
        self.created.append(model)
        return model

    def get(self, task_arn: str) -> DataSyncTask | None:
        return self._get_results.get(task_arn)

    def list(self) -> PrimaryBoto3ModelQuerySet:
        return self._list_result

    def update(self, model: DataSyncTask) -> DataSyncTask:
        self.updated.append(model)
        return model

    def delete(self, task_arn: str) -> None:
        self.deleted.append(task_arn)

    def start_task_execution(
        self,
        task_arn: str,
        **kwargs: Any,
    ) -> DataSyncTaskExecution | None:
        self.started.append((task_arn, kwargs))
        return self._start_result


class FakeExecutionManager:
    def __init__(self) -> None:
        self.session: Any = None
        self.cancelled: list[str] = []
        self._get_results: dict[str, list[DataSyncTaskExecution]] = {}
        self._list_results: dict[str | None, PrimaryBoto3ModelQuerySet] = {}

    def get(self, execution_arn: str) -> DataSyncTaskExecution | None:
        queue = self._get_results.get(execution_arn, [])
        if queue:
            return queue.pop(0)
        return None

    def list(self, *, TaskArn: str | None = None) -> PrimaryBoto3ModelQuerySet:
        return self._list_results.get(TaskArn, PrimaryBoto3ModelQuerySet([]))

    def cancel(self, execution_arn: str) -> None:
        self.cancelled.append(execution_arn)


class FakeCrudManager:
    def __init__(self, model: Any | None = None) -> None:
        self.session: Any = None
        self.created: list[Any] = []
        self.updated: list[Any] = []
        self.deleted: list[str] = []
        self.model = model
        self.list_result = PrimaryBoto3ModelQuerySet([])

    def create(self, model: Any) -> Any:
        self.created.append(model)
        return model

    def get(self, arn: str) -> Any:
        return self.model if getattr(self.model, "pk", arn) == arn else None

    def list(self) -> PrimaryBoto3ModelQuerySet:
        return self.list_result

    def update(self, model: Any) -> Any:
        self.updated.append(model)
        return model

    def delete(self, arn: str) -> None:
        self.deleted.append(arn)


class RoutingS3Manager(FakeCrudManager):
    def __init__(self, models_by_session: dict[Any, DataSyncLocationS3]) -> None:
        super().__init__()
        self._models_by_session = models_by_session

    def get(self, arn: str) -> Any:
        model = self._models_by_session.get(self.session)
        if model is None:
            return None
        return model if getattr(model, "pk", arn) == arn else None


def make_workspace(
    *,
    session: Any = None,
    accounts: dict[str, DataSyncAccountContext] | None = None,
    task_manager: FakeTaskManager | None = None,
    execution_manager: FakeExecutionManager | None = None,
    agent_manager: FakeCrudManager | None = None,
    s3_manager: FakeCrudManager | None = None,
) -> DataSyncWorkspace:
    task_manager = task_manager or FakeTaskManager()
    execution_manager = execution_manager or FakeExecutionManager()
    agent_manager = agent_manager or FakeCrudManager()
    s3_manager = s3_manager or FakeCrudManager()
    location_managers = {
        "azure_blob": lambda: FakeCrudManager(),
        "efs": lambda: FakeCrudManager(),
        "fsx_lustre": lambda: FakeCrudManager(),
        "fsx_ontap": lambda: FakeCrudManager(),
        "fsx_openzfs": lambda: FakeCrudManager(),
        "fsx_windows": lambda: FakeCrudManager(),
        "hdfs": lambda: FakeCrudManager(),
        "nfs": lambda: FakeCrudManager(),
        "object_storage": lambda: FakeCrudManager(),
        "s3": lambda: s3_manager,
        "smb": lambda: FakeCrudManager(),
    }
    return DataSyncWorkspace(
        session=session,
        accounts=accounts,
        _agent_manager_factory=lambda: agent_manager,
        _task_manager_factory=lambda: task_manager,
        _execution_manager_factory=lambda: execution_manager,
        _location_manager_factories=location_managers,
    )


def make_account_context(name: str, session: Any) -> DataSyncAccountContext:
    return DataSyncAccountContext(name=name, session=cast("Any", session))


def test_workspace_define_job_wraps_created_task() -> None:
    task = make_task("arn:aws:datasync:task/demo")
    task_manager = FakeTaskManager()
    workspace = make_workspace(task_manager=task_manager)

    job = workspace.define_job(task)

    assert isinstance(job, DataSyncJobDefinition)
    assert job.task is task
    assert task_manager.created == [task]


def test_task_facade_start_returns_job_run() -> None:
    task = make_task("arn:aws:datasync:task/demo")
    execution = make_execution("arn:aws:datasync:task/demo/execution/1")
    task_manager = FakeTaskManager()
    task_manager._start_result = execution
    workspace = make_workspace(task_manager=task_manager)

    run = workspace.tasks.start(task, OverrideOptions=DataSyncOptions(BytesPerSecond=2048))

    assert isinstance(run, DataSyncJobRun)
    assert run.execution is execution
    assert task_manager.started == [
        ("arn:aws:datasync:task/demo", {"OverrideOptions": DataSyncOptions(BytesPerSecond=2048)})
    ]


def test_job_definition_refresh_and_update_rehydrate() -> None:
    original = make_task("arn:aws:datasync:task/demo")
    refreshed = make_task("arn:aws:datasync:task/demo")
    refreshed.Name = "updated-name"
    task_manager = FakeTaskManager()
    task_manager._get_results[cast("str", original.TaskArn)] = refreshed
    workspace = make_workspace(task_manager=task_manager)
    job = DataSyncJobDefinition(original, workspace)

    refreshed_job = job.refresh()
    assert refreshed_job.task.Name == "updated-name"

    refreshed_job.task.Name = "second-name"
    task_manager._get_results[cast("str", original.TaskArn)] = refreshed_job.task
    updated_job = refreshed_job.update()
    assert updated_job.task.Name == "second-name"
    assert task_manager.updated == [refreshed_job.task]


def test_job_definition_latest_run_prefers_current_execution_arn() -> None:
    execution_arn = "arn:aws:datasync:task/demo/execution/1"
    task = make_task("arn:aws:datasync:task/demo", current_execution_arn=execution_arn)
    execution = make_execution(execution_arn)
    execution_manager = FakeExecutionManager()
    execution_manager._get_results[execution_arn] = [execution]
    workspace = make_workspace(execution_manager=execution_manager)
    job = DataSyncJobDefinition(task, workspace)

    latest = job.latest_run()

    assert isinstance(latest, DataSyncJobRun)
    assert latest.execution is execution


def test_job_run_cancel_calls_cancel_then_refreshes() -> None:
    execution_arn = "arn:aws:datasync:task/demo/execution/1"
    cancelling = make_execution(execution_arn, status="CANCELLING")
    execution_manager = FakeExecutionManager()
    execution_manager._get_results[execution_arn] = [cancelling]
    workspace = make_workspace(execution_manager=execution_manager)
    run = DataSyncJobRun(make_execution(execution_arn), workspace)

    cancelled = run.cancel()

    assert cancelled.execution.Status == "CANCELLING"
    assert execution_manager.cancelled == [execution_arn]


def test_job_run_wait_stops_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    execution_arn = "arn:aws:datasync:task/demo/execution/1"
    execution_manager = FakeExecutionManager()
    execution_manager._get_results[execution_arn] = [
        make_execution(execution_arn, status="TRANSFERRING"),
        make_execution(execution_arn, status="SUCCESS", bytes_transferred=100),
    ]
    workspace = make_workspace(execution_manager=execution_manager)
    run = DataSyncJobRun(make_execution(execution_arn, status="LAUNCHING"), workspace)
    sleeps: list[float] = []
    monkeypatch.setattr("botocraft.datasync.time.sleep", sleeps.append)

    finished = run.wait(poll_interval_seconds=0.25, timeout_seconds=5)

    assert finished.status == "SUCCESS"
    assert sleeps == [0.25]


def test_job_run_wait_polls_through_cancelling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution_arn = "arn:aws:datasync:task/demo/execution/1"
    execution_manager = FakeExecutionManager()
    execution_manager._get_results[execution_arn] = [
        make_execution(execution_arn, status="CANCELLING"),
        make_execution(execution_arn, status="ERROR", error_code="Cancelled"),
    ]
    workspace = make_workspace(execution_manager=execution_manager)
    run = DataSyncJobRun(make_execution(execution_arn, status="TRANSFERRING"), workspace)
    sleeps: list[float] = []
    monkeypatch.setattr("botocraft.datasync.time.sleep", sleeps.append)

    finished = run.wait(poll_interval_seconds=0.5, timeout_seconds=5)

    assert finished.status == "ERROR"
    assert sleeps == [0.5]


def test_job_run_wait_raises_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    execution_arn = "arn:aws:datasync:task/demo/execution/1"
    execution_manager = FakeExecutionManager()
    execution_manager._get_results[execution_arn] = [
        make_execution(execution_arn, status="TRANSFERRING"),
        make_execution(execution_arn, status="TRANSFERRING"),
        make_execution(execution_arn, status="TRANSFERRING"),
    ]
    workspace = make_workspace(execution_manager=execution_manager)
    run = DataSyncJobRun(make_execution(execution_arn, status="TRANSFERRING"), workspace)
    values = iter([0.0, 1.0, 2.1])
    monkeypatch.setattr("botocraft.datasync.time.monotonic", lambda: next(values))
    monkeypatch.setattr("botocraft.datasync.time.sleep", lambda _: None)

    with pytest.raises(TimeoutError):
        run.wait(poll_interval_seconds=0.1, timeout_seconds=2)


def test_job_run_progress_maps_execution_fields() -> None:
    run = DataSyncJobRun(
        make_execution(
            "arn:aws:datasync:task/demo/execution/1",
            status="ERROR",
            bytes_transferred=40,
            error_code="ExampleError",
            error_detail="broken transfer",
        ),
        make_workspace(),
    )

    progress = run.progress()

    assert isinstance(progress, DataSyncJobProgress)
    assert progress.status == "ERROR"
    assert progress.bytes_transferred == 40
    assert progress.error_code == "ExampleError"
    assert progress.error_detail == "broken transfer"


def test_job_run_summary_uses_best_effort_progress() -> None:
    run = DataSyncJobRun(
        make_execution(
            "arn:aws:datasync:task/demo/execution/1",
            status="TRANSFERRING",
            estimated_bytes=200,
            bytes_transferred=50,
        ),
        make_workspace(),
    )

    summary = run.summary()

    assert "TRANSFERRING" in summary
    assert "50/200 bytes" in summary


def test_typed_location_facades_use_specific_manager_and_session() -> None:
    session = SimpleNamespace(name="session")
    location = DataSyncLocationS3(
        LocationArn="arn:aws:datasync:location/s3",
        LocationUri="s3://demo-bucket/path",
        S3BucketArn="arn:aws:s3:::demo-bucket",
    )
    s3_manager = FakeCrudManager(model=location)
    workspace = make_workspace(session=session, s3_manager=s3_manager)

    created = workspace.locations.s3.create(location)
    loaded = workspace.locations.s3.get(cast("str", location.LocationArn))

    assert created is location
    assert loaded is location
    assert s3_manager.created == [location]
    assert s3_manager.session is session


def test_workspace_preserves_supplied_session_on_underlying_managers() -> None:
    session = SimpleNamespace(name="session")
    task_manager = FakeTaskManager()
    execution_manager = FakeExecutionManager()
    agent_manager = FakeCrudManager(model=DataSyncAgent(AgentArn="arn:agent"))
    workspace = make_workspace(
        session=session,
        task_manager=task_manager,
        execution_manager=execution_manager,
        agent_manager=agent_manager,
    )

    _ = workspace.tasks
    _ = workspace.executions
    _ = workspace.agents

    assert task_manager.session is session
    assert execution_manager.session is session
    assert agent_manager.session is session


def test_workspace_account_returns_configured_context() -> None:
    source = make_account_context("source", SimpleNamespace(name="src"))
    workspace = make_workspace(accounts={"source": source})

    assert workspace.account("source") is source


def test_account_scoped_facades_bind_account_session() -> None:
    source_session = SimpleNamespace(name="source")
    task_session = SimpleNamespace(name="task")
    source_s3_manager = FakeCrudManager()
    task_manager = FakeTaskManager()
    execution_manager = FakeExecutionManager()
    source_accounts = {
        "source": make_account_context("source", source_session),
        "task": make_account_context("task", task_session),
    }
    workspace = make_workspace(
        session=SimpleNamespace(name="default"),
        accounts=source_accounts,
        task_manager=task_manager,
        execution_manager=execution_manager,
        s3_manager=source_s3_manager,
    )

    _ = workspace.locations_in("source").s3
    _ = workspace.tasks_in("task")
    _ = workspace.executions_in("task")

    assert source_s3_manager.session is source_session
    assert task_manager.session is task_session
    assert execution_manager.session is task_session


def test_define_cross_account_job_stores_account_spec() -> None:
    task = make_task("arn:aws:datasync:task/demo")
    task_manager = FakeTaskManager()
    source_location = DataSyncLocationS3(
        LocationArn="arn:aws:datasync:us-west-2:123456789012:location/src",
        LocationUri="s3://source-bucket/src",
        S3BucketArn="arn:aws:s3:::source-bucket",
        S3Config=DataSyncS3Config(
            BucketAccessRoleArn="arn:aws:iam::111111111111:role/source"
        ),
    )
    destination_location = DataSyncLocationS3(
        LocationArn="arn:aws:datasync:us-west-2:123456789012:location/dst",
        LocationUri="s3://dest-bucket/dst",
        S3BucketArn="arn:aws:s3:::dest-bucket",
        S3Config=DataSyncS3Config(
            BucketAccessRoleArn="arn:aws:iam::222222222222:role/destination"
        ),
    )
    source_session = object()
    destination_session = object()
    source_s3_manager = RoutingS3Manager(
        {
            source_session: source_location,
            destination_session: destination_location,
        }
    )
    workspace = DataSyncWorkspace(
        accounts={
            "task": make_account_context("task", SimpleNamespace(name="task")),
            "source": make_account_context("source", source_session),
            "destination": make_account_context("destination", destination_session),
        },
        _task_manager_factory=lambda: task_manager,
        _execution_manager_factory=lambda: FakeExecutionManager(),
        _agent_manager_factory=lambda: FakeCrudManager(),
        _location_manager_factories={
            "azure_blob": lambda: FakeCrudManager(),
            "efs": lambda: FakeCrudManager(),
            "fsx_lustre": lambda: FakeCrudManager(),
            "fsx_ontap": lambda: FakeCrudManager(),
            "fsx_openzfs": lambda: FakeCrudManager(),
            "fsx_windows": lambda: FakeCrudManager(),
            "hdfs": lambda: FakeCrudManager(),
            "nfs": lambda: FakeCrudManager(),
            "object_storage": lambda: FakeCrudManager(),
            "s3": lambda: source_s3_manager,
            "smb": lambda: FakeCrudManager(),
        },
    )
    spec = DataSyncCrossAccountSpec(
        task_account="task",
        source_account="source",
        destination_account="destination",
    )

    job = workspace.define_cross_account_job(task, spec=spec)

    assert isinstance(job, DataSyncJobDefinition)
    assert job.account_spec == spec
    assert task_manager.created == [task]


def test_cross_account_job_start_uses_task_account_session() -> None:
    task_session = SimpleNamespace(name="task")
    task = make_task("arn:aws:datasync:task/demo")
    execution = make_execution("arn:aws:datasync:task/demo/execution/1")
    task_manager = FakeTaskManager()
    task_manager._start_result = execution
    workspace = make_workspace(
        session=SimpleNamespace(name="default"),
        accounts={"task": make_account_context("task", task_session)},
        task_manager=task_manager,
    )
    job = DataSyncJobDefinition(
        task,
        workspace,
        account_spec=DataSyncCrossAccountSpec(
            task_account="task",
            source_account="task",
            destination_account="task",
        ),
    )

    job.start()

    assert task_manager.session is task_session
    assert task_manager.started == [("arn:aws:datasync:task/demo", {})]


def test_cross_account_job_validation_requires_bucket_access_roles() -> None:
    task = make_task("arn:aws:datasync:task/demo")
    source_location = DataSyncLocationS3(
        LocationArn="arn:aws:datasync:us-west-2:123456789012:location/src",
        LocationUri="s3://source-bucket/src",
        S3BucketArn="arn:aws:s3:::source-bucket",
    )
    destination_location = DataSyncLocationS3(
        LocationArn="arn:aws:datasync:us-west-2:123456789012:location/dst",
        LocationUri="s3://dest-bucket/dst",
        S3BucketArn="arn:aws:s3:::dest-bucket",
        S3Config=DataSyncS3Config(
            BucketAccessRoleArn="arn:aws:iam::222222222222:role/destination"
        ),
    )
    source_session = object()
    destination_session = object()
    routing_manager = RoutingS3Manager(
        {
            source_session: source_location,
            destination_session: destination_location,
        }
    )
    spec = DataSyncCrossAccountSpec(
        task_account="task",
        source_account="source",
        destination_account="destination",
    )
    workspace = DataSyncWorkspace(
        accounts={
            "task": make_account_context("task", SimpleNamespace(name="task")),
            "source": make_account_context("source", source_session),
            "destination": make_account_context("destination", destination_session),
        },
        _task_manager_factory=lambda: FakeTaskManager(),
        _execution_manager_factory=lambda: FakeExecutionManager(),
        _agent_manager_factory=lambda: FakeCrudManager(),
        _location_manager_factories={
            "azure_blob": lambda: FakeCrudManager(),
            "efs": lambda: FakeCrudManager(),
            "fsx_lustre": lambda: FakeCrudManager(),
            "fsx_ontap": lambda: FakeCrudManager(),
            "fsx_openzfs": lambda: FakeCrudManager(),
            "fsx_windows": lambda: FakeCrudManager(),
            "hdfs": lambda: FakeCrudManager(),
            "nfs": lambda: FakeCrudManager(),
            "object_storage": lambda: FakeCrudManager(),
            "s3": lambda: routing_manager,
            "smb": lambda: FakeCrudManager(),
        },
    )
    job = DataSyncJobDefinition(task, workspace, account_spec=spec)

    with pytest.raises(ValueError, match="BucketAccessRoleArn"):
        job.validate_cross_account_s3()


def test_cross_account_job_validation_requires_manifest_bucket_access_role() -> None:
    task = make_task("arn:aws:datasync:task/demo")
    task.ManifestConfig = DataSyncManifestConfig(
        Source=SourceManifestConfig(
            S3=S3ManifestConfig(
                ManifestObjectPath="manifests/demo.csv",
                S3BucketArn="arn:aws:s3:::manifest-bucket",
                BucketAccessRoleArn="",
            )
        )
    )
    location = DataSyncLocationS3(
        LocationArn="arn:aws:datasync:us-west-2:123456789012:location/src",
        LocationUri="s3://source-bucket/src",
        S3BucketArn="arn:aws:s3:::source-bucket",
        S3Config=DataSyncS3Config(
            BucketAccessRoleArn="arn:aws:iam::111111111111:role/source"
        ),
    )
    destination = DataSyncLocationS3(
        LocationArn="arn:aws:datasync:us-west-2:123456789012:location/dst",
        LocationUri="s3://dest-bucket/dst",
        S3BucketArn="arn:aws:s3:::dest-bucket",
        S3Config=DataSyncS3Config(
            BucketAccessRoleArn="arn:aws:iam::222222222222:role/destination"
        ),
    )
    spec = DataSyncCrossAccountSpec(
        task_account="task",
        source_account="source",
        destination_account="destination",
    )
    source_session = object()
    destination_session = object()
    workspace = DataSyncWorkspace(
        accounts={
            "task": make_account_context("task", SimpleNamespace(name="task")),
            "source": make_account_context("source", source_session),
            "destination": make_account_context("destination", destination_session),
        },
        _agent_manager_factory=lambda: FakeCrudManager(),
        _task_manager_factory=lambda: FakeTaskManager(),
        _execution_manager_factory=lambda: FakeExecutionManager(),
        _location_manager_factories={
            "azure_blob": lambda: FakeCrudManager(),
            "efs": lambda: FakeCrudManager(),
            "fsx_lustre": lambda: FakeCrudManager(),
            "fsx_ontap": lambda: FakeCrudManager(),
            "fsx_openzfs": lambda: FakeCrudManager(),
            "fsx_windows": lambda: FakeCrudManager(),
            "hdfs": lambda: FakeCrudManager(),
            "nfs": lambda: FakeCrudManager(),
            "object_storage": lambda: FakeCrudManager(),
            "s3": lambda: RoutingS3Manager(
                {
                    source_session: location,
                    destination_session: destination,
                }
            ),
            "smb": lambda: FakeCrudManager(),
        },
    )
    job = DataSyncJobDefinition(task, workspace, account_spec=spec)

    with pytest.raises(ValueError, match="manifest"):
        job.validate_cross_account_s3()


def test_assume_role_account_context_builds_session_from_sts_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeSTSClient:
        def assume_role(self, **kwargs: Any) -> dict[str, Any]:
            captured["assume_role_kwargs"] = kwargs
            return {
                "Credentials": {
                    "AccessKeyId": "AKIA123",
                    "SecretAccessKey": "secret",
                    "SessionToken": "token",
                },
                "AssumedRoleUser": {
                    "Arn": "arn:aws:sts::123456789012:assumed-role/demo/session"
                },
            }

    class FakeBaseSession:
        def client(self, service_name: str) -> FakeSTSClient:
            captured["service_name"] = service_name
            return FakeSTSClient()

    class FakeSession:
        def __init__(self, **kwargs: Any) -> None:
            captured["session_kwargs"] = kwargs

    monkeypatch.setattr("botocraft.datasync.boto3.session.Session", FakeSession)

    context = assume_role_account_context(
        "source",
        "arn:aws:iam::123456789012:role/demo",
        session_name="botocraft-test",
        base_session=cast("Any", FakeBaseSession()),
    )

    assert context.name == "source"
    assert context.role_arn == "arn:aws:iam::123456789012:role/demo"
    assert captured["service_name"] == "sts"
    assert captured["assume_role_kwargs"] == {
        "RoleArn": "arn:aws:iam::123456789012:role/demo",
        "RoleSessionName": "botocraft-test",
    }
    assert captured["session_kwargs"] == {
        "aws_access_key_id": "AKIA123",
        "aws_secret_access_key": "secret",
        "aws_session_token": "token",
    }
