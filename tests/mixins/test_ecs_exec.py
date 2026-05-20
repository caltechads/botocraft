# ruff: noqa: I001
import signal
import subprocess
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from botocraft.services.ecs import Container, Service, Task

from botocraft.mixins.ecs import (
    ECSExecMixin,
    ECSServiceModelMixin,
    ECSTaskModelMixin,
    build_sigint_handler,
)


class TestBuildSigintHandler:
    def test_forwards_sigint_to_subprocess(self):
        process = MagicMock()
        handler = build_sigint_handler(process)
        handler(signal.SIGINT, None)
        process.send_signal.assert_called_once_with(signal.SIGINT)


class _ExecStub(ECSExecMixin):
    def __init__(
        self,
        *,
        running_tasks: list[Task],
        exec_cluster: str,
        profile_name: str | None = None,
        pk: str = "stub",
    ) -> None:
        self.session = MagicMock(profile_name=profile_name)
        self.pk = pk
        self._running_tasks = running_tasks
        self._exec_cluster = exec_cluster

    @property
    def running_tasks(self) -> list[Task]:
        return self._running_tasks

    @property
    def exec_cluster(self) -> str:
        return self._exec_cluster


class TestECSExecMixin:
    def test_no_running_tasks_raises(self):
        mixin = _ExecStub(running_tasks=[], exec_cluster="cluster")

        with pytest.raises(ECSExecMixin.NoRunningTasks):
            mixin.exec()

    @patch("botocraft.mixins.ecs.shutil.which", return_value="/usr/bin/aws")
    @patch("botocraft.mixins.ecs.subprocess.run")
    @patch("botocraft.mixins.ecs.subprocess.Popen")
    @patch("botocraft.mixins.ecs.signal.signal")
    def test_exec_uses_first_task_and_container(
        self,
        mock_signal,
        mock_popen,
        mock_run,
        mock_which,
    ):
        assert mock_which.return_value == "/usr/bin/aws"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="execute-command\n",
            stderr="",
        )
        process = MagicMock()
        mock_popen.return_value = process

        task = Task(
            taskArn="arn:aws:ecs:us-west-2:1:task/cluster/abc",
            clusterArn="arn:aws:ecs:us-west-2:1:cluster/cluster",
            containers=[Container(name="app")],
            lastStatus="RUNNING",
        )
        mixin = _ExecStub(
            running_tasks=[task],
            exec_cluster="cluster",
            profile_name="dev",
        )

        mixin.exec()

        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        assert cmd[:4] == ["aws", "--profile", "dev", "ecs"]
        assert "--cluster" in cmd
        assert "cluster" in cmd
        assert "--task=arn:aws:ecs:us-west-2:1:task/cluster/abc" in cmd
        assert "--container=app" in cmd
        assert "--interactive" in cmd
        assert "--command" in cmd
        assert cmd[-1] == "/bin/sh"
        sigint_handler = mock_signal.call_args_list[0].args[1]
        sigint_handler(signal.SIGINT, None)
        process.send_signal.assert_called_once_with(signal.SIGINT)
        assert mock_signal.call_args_list[1].args == (signal.SIGINT, signal.SIG_DFL)
        process.wait.assert_called_once()


class TestECSServiceModelMixin:
    def test_running_tasks_filters_to_running_status(self):
        service = Service(
            serviceName="api",
            clusterArn="arn:aws:ecs:us-west-2:1:cluster/prod",
            taskDefinition="arn:aws:ecs:us-west-2:1:task-definition/api:1",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
        )
        running = Task(
            taskArn="arn:aws:ecs:us-west-2:1:task/prod/running",
            clusterArn=service.clusterArn,
            lastStatus="RUNNING",
        )
        stopped = Task(
            taskArn="arn:aws:ecs:us-west-2:1:task/prod/stopped",
            clusterArn=service.clusterArn,
            lastStatus="STOPPED",
        )
        with patch.object(
            Service,
            "tasks",
            new_callable=PropertyMock,
            return_value=[running, stopped],
        ):
            assert service.running_tasks == [running]

    def test_exec_cluster_prefers_cluster_name(self):
        service = Service(
            serviceName="api",
            clusterArn="arn:aws:ecs:us-west-2:1:cluster/prod",
            taskDefinition="arn:aws:ecs:us-west-2:1:task-definition/api:1",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
        )
        assert ECSServiceModelMixin.exec_cluster.fget(service) == "prod"


class TestECSTaskModelMixin:
    def test_running_tasks_empty_when_not_running(self):
        task = Task(
            taskArn="arn:aws:ecs:us-west-2:1:task/prod/abc",
            clusterArn="arn:aws:ecs:us-west-2:1:cluster/prod",
            lastStatus="STOPPED",
        )
        assert ECSTaskModelMixin.running_tasks.fget(task) == []

    def test_exec_rejects_foreign_task_arn(self):
        task = Task(
            taskArn="arn:aws:ecs:us-west-2:1:task/prod/abc",
            clusterArn="arn:aws:ecs:us-west-2:1:cluster/prod",
            lastStatus="RUNNING",
            containers=[Container(name="app")],
        )
        with pytest.raises(ValueError, match="does not match"):
            task.exec(task_arn="arn:aws:ecs:us-west-2:1:task/prod/other")
