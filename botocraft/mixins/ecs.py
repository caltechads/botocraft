# mypy: disable-error-code="attr-defined"
import re
import shutil
import signal
import subprocess
import warnings
from collections.abc import Callable
from functools import cached_property, wraps
from typing import TYPE_CHECKING, Any, Literal, cast

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services import (
        Cluster,
        Daemon,
        DaemonTaskDefinition,
        DeleteTaskDefinitionsResponse,
        ECRImage,
        ExpressGatewayService,
        Failure,
        Service,
        ServiceDeploymentBrief,
        Task,
        TaskDefinition,
        TaskManager,
    )


# ---------
# Functions
# ---------


def extract_task_family_and_revision(task_definition_arn: str) -> str:
    """
    Extract the task family and revision from a task definition ARN.

    Args:
        task_definition_arn: The ARN of the task definition.

    Returns:
        The task family and revision in the format ``<family>:<revision>``.

    """
    task_definition_arn_re = r"arn:aws:ecs:[^:]+:[^:]+:task-definition/(?P<family>[^:]+):(?P<revision>[0-9]+)"  # noqa: E501
    match = re.match(task_definition_arn_re, task_definition_arn)
    assert match, (
        f"Could not extract task family and revision from {task_definition_arn}"
    )
    return f"{match.group('family')}:{match.group('revision')}"


def build_sigint_handler(
    process: subprocess.Popen[bytes],
) -> Callable[[int, Any], None]:
    """
    Build a SIGINT handler that forwards Control-C to a subprocess.

    Use when running ``aws ecs execute-command`` so SIGINT reaches the remote
    shell instead of raising :py:class:`KeyboardInterrupt` in the caller and
    leaving the ECS Exec session running.

    Args:
        process: Subprocess running the interactive ECS Exec session.

    Returns:
        A function suitable for :py:func:`signal.signal`.

    """

    def sigint_handler(_signum: int, _frame: Any) -> None:
        process.send_signal(signal.SIGINT)

    return sigint_handler


def _cluster_name_from_arn(cluster_arn: str) -> str:
    """
    Return the short cluster name from a cluster ARN when possible.

    Args:
        cluster_arn: Full cluster ARN or short cluster name.

    Returns:
        The cluster short name, or ``cluster_arn`` unchanged when it is not an ARN.

    """
    match = re.match(r"^.*:cluster/(.+)$", cluster_arn)
    if match:
        return match.group(1)
    return cluster_arn


# ----------
# Decorators
# ----------


# Service


def ecs_services_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.ecs.ServiceManager.list` to return a
    :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.ecs.Service` objects instead of only a list of
    ARNs.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        arns = func(self, *args, **kwargs)
        services = []
        # We have to do this in batches of 10 because the get_many method,
        # which uses the boto3 ``describe_services`` method, only accepts 10 ARNs
        # at a time.
        for i in range(0, len(arns), 10):
            services.extend(
                self.get_many(
                    arns[i : i + 10], cluster=kwargs["cluster"], include=["TAGS"]
                ).results
            )
        return PrimaryBoto3ModelQuerySet(services)

    return wrapper


# Cluster


def ecs_clusters_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.ecs.ClusterManager.list` to return a list
    of :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.ecs.Cluster` objects instead of only a list of
    ARNs.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        arns = func(self, *args, **kwargs)
        clusters: list[Cluster] = []
        # We have to do this in batches of 100 because the get_many method,
        # which uses the boto3 ``describe_clusters`` method, only accepts 100 ARNs
        # at a time.
        for i in range(0, len(arns), 100):
            qs = self.get_many(clusters=arns[i : i + 100], include=["TAGS"])
            clusters.extend(
                qs.results if isinstance(qs, PrimaryBoto3ModelQuerySet) else qs.clusters  # type: ignore[arg-type]
            )
        return PrimaryBoto3ModelQuerySet(clusters)  # type: ignore[arg-type]

    return wrapper


def ecs_task_definition_include_tags(
    func: Callable[..., "TaskDefinition | None"],
) -> Callable[..., "TaskDefinition | None"]:
    """
    Decorator to convert a :py:class:`botocraft.services.ecs.TaskDefinition` object
    to a :py:class:`botocraft.services.ecs.TaskDefinition` object with tags included.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "TaskDefinition | None":
        response = func(self, *args, **kwargs)
        if not response:
            return None
        # If we got a TaskDefinition object, we need to convert it to a
        # TaskDefinition with tags.
        _td = response.taskDefinition
        _td.tags = response.tags
        return cast("TaskDefinition", _td)

    return wrapper


def ecs_task_definitions_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a list of ECS task definition identifiers to a list of
    :py:class:`botocraft.services.ecs.TaskDefinition` objects.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        identifiers = func(self, *args, **kwargs)
        responses = [
            self.get(identifier, include=["TAGS"]) for identifier in identifiers
        ]
        return PrimaryBoto3ModelQuerySet(responses)

    return wrapper


# ContainerInstance


def ecs_container_instances_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a list of ECS container instance arns to a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.ecs.ContainerInstance` objects.
    """

    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        arns = func(self, *args, **kwargs)
        container_instances = []
        for i in range(0, len(arns), 100):
            _instances = self.get_many(
                cluster=kwargs["cluster"], containerInstances=arns[i : i + 100]
            )
            if isinstance(_instances, PrimaryBoto3ModelQuerySet):
                _instances = _instances.results
            # If we got a list of ContainerInstanceBrief objects, we need to convert
            if _instances:
                container_instances.extend(_instances)
        return PrimaryBoto3ModelQuerySet(container_instances)

    return wrapper


def ecs_container_instances_tasks_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a list of ECS container instance arns to a list of
    :py:class:`botocraft.services.ecs.ContainerInstance` objects.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.ecs import Task

        arns = func(self, *args, **kwargs)
        tasks: list[Task] = []
        for i in range(0, len(arns), 100):
            tasks.extend(
                cast("TaskManager", Task.objects).get_many(arns[i : i + 100]).results  # type: ignore[arg-type]
            )
        return PrimaryBoto3ModelQuerySet(tasks)  # type: ignore[arg-type]

    return wrapper


def ecs_service_deployments_only(
    func: Callable[..., list["ServiceDeploymentBrief"]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a list of service deployment arns to a list of
    :py:class:`botocraft.services.ecs.Deployment` objects.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.ecs import (
            ServiceDeployment,
            ServiceDeploymentManager,
        )

        response = func(self, *args, **kwargs)
        if response is None:
            return PrimaryBoto3ModelQuerySet([])
        arns = [
            d.serviceDeploymentArn
            for d in func(self, *args, **kwargs)
            if d.serviceDeploymentArn
        ]
        deployments: list[ServiceDeployment] = []
        for i in range(0, len(arns), 20):
            _deployments = cast(
                "ServiceDeploymentManager", ServiceDeployment.objects
            ).get_many(arns[i : i + 20])
            if isinstance(_deployments, PrimaryBoto3ModelQuerySet):
                _deployments = _deployments.results  # type: ignore[assignment]
            # If we got a list of ServiceDeploymentBrief objects, we need to convert
            if _deployments:
                deployments.extend(_deployments)  # type: ignore[arg-type]
        return PrimaryBoto3ModelQuerySet(deployments)  # type: ignore[arg-type]

    return wrapper


# Task
def ecs_task_populate_taskDefinition(
    func: Callable[..., "Task | None"],
) -> Callable[..., "Task | None"]:
    """
    Wraps :py:meth:`botocraft.services.ecs.TaskManager.get` to populate the
    :py:attr:`botocraft.services.ecs.Task.taskDefinition` attribute.

    We set the ``taskDefinition`` attribute to the task family and revision in the
    format ``<family>:<revision>``.  ``taskDefinition`` is an extra field that we
    add to the :py:class:`botocraft.services.ecs.Task` object that is not in the
    original botocore shape, but is useful for our purposes.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "Task | None":
        task = func(self, *args, **kwargs)
        if task:
            task.taskDefinition = extract_task_family_and_revision(
                task.taskDefinitionArn
            )
        return task

    return wrapper


def ecs_task_populate_taskDefinitions(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.ecs.TaskManager.get_many` to
    populate the :py:attr:`botocraft.services.ecs.Task.taskDefinition` attribute
    on each task.

    We set the ``taskDefinition`` attribute to the task family and revision in the
    format ``<family>:<revision>``.  ``taskDefinition`` is an extra field that we
    add to the :py:class:`botocraft.services.ecs.Task` object that is not in the
    original botocore shape, but is useful for our purposes.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        tasks = func(self, *args, **kwargs)
        for task in tasks:
            task.taskDefinition = extract_task_family_and_revision(
                task.taskDefinitionArn
            )
        return tasks

    return wrapper


def ecs_tasks_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wrap :py:meth:`botocraft.services.ecs.TaskManager.list` to return a list of
    :py:class:`botocraft.services.ecs.Task` objects instead of only a list of
    ARNs.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        arns = func(self, *args, **kwargs)
        tasks = []
        # We have to do this in batches of 100 because the get_many method,
        # which uses the boto3 ``describe_tasks`` method, only accepts 100 ARNs
        # at a time.
        for i in range(0, len(arns), 100):
            tasks.extend(
                self.get_many(cluster=kwargs["cluster"], tasks=arns[i : i + 100])
            )
        return PrimaryBoto3ModelQuerySet(tasks)  # type: ignore[arg-type]

    return wrapper


def ecs_task_definition_delete_all(
    func: Callable[..., "DeleteTaskDefinitionsResponse"],
) -> Callable[..., "DeleteTaskDefinitionsResponse"]:
    """
    Decorator to delete all task definitions.  This is because the
    :py:meth:`botocraft.services.ecs.TaskDefinitionManager.delete` method only
    accepts up to 10 task definitions at a time, so we need to delete them in
    batches of 10 if the user passes in more than 10 task definitions.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "DeleteTaskDefinitionsResponse":
        # delete_task_definitions only accepts up to 10 task definitions at a time
        # So we need to delete them in batches
        from botocraft.services import DeleteTaskDefinitionsResponse

        if len(args[0]) > 10:  # noqa: PLR2004
            response: DeleteTaskDefinitionsResponse = DeleteTaskDefinitionsResponse(
                taskDefinitions=[],
                failures=[],
            )
            for i in range(0, len(args[0]), 10):
                _response = func(self, args[0][i : i + 10], **kwargs)
                if _response.taskDefinitions:
                    cast("list[TaskDefinition]", response.taskDefinitions).extend(
                        _response.taskDefinitions
                    )
                if _response.failures:
                    cast("list[Failure]", response.failures).extend(_response.failures)  # type: ignore[attr-defined]
        else:
            response = func(self, *args, **kwargs)
        return response

    return wrapper


# Mixins


class ECSExecMixin:
    """
    Mixin that opens interactive ECS Exec sessions via the AWS CLI.

    Models that include this mixin must implement :py:attr:`running_tasks` and
    :py:attr:`exec_cluster`.
    """

    class NoRunningTasks(Exception):
        """Raised when there are no running tasks to exec into."""

    @property
    def running_tasks(self) -> "list[Task]":
        """
        Return tasks that are currently running for this object.

        Returns:
            Running :py:class:`~botocraft.services.ecs.Task` instances.

        """
        raise NotImplementedError

    @property
    def exec_cluster(self) -> str:
        """
        Return the cluster name or ARN passed to ``aws ecs execute-command``.

        Returns:
            Cluster identifier for the exec target.

        """
        raise NotImplementedError

    def exec(
        self,
        *,
        task_arn: str | None = None,
        container_name: str | None = None,
        command: str = "/bin/sh",
    ) -> None:
        """
        Exec into a container using `ECS Exec <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-exec.html>`_.

        Side Effects:
            Runs ``aws ecs execute-command`` in the foreground until the remote
            session ends.

        Keyword Args:
            task_arn: Task ARN to use. When omitted, the first running task is
                used. On :py:class:`~botocraft.services.ecs.Task`, this must refer
                to the task itself when provided.
            container_name: Container name to use. When omitted, the first
                container on the chosen task is used.
            command: Shell command passed to ``--command``.

        Raises:
            ECSExecMixin.NoRunningTasks: No running tasks are available.
            RuntimeError: The AWS CLI is missing or ``execute-command`` is unavailable.
            ValueError: The requested task or container could not be resolved.

        """
        running = self.running_tasks
        if not running:
            msg = f"{self.__class__.__name__}(pk={self.pk}) has no running tasks."
            raise self.NoRunningTasks(msg)

        task = self.__resolve_exec_task(task_arn=task_arn, running=running)
        container = self.__resolve_exec_container(
            task=task,
            container_name=container_name,
        )
        profile = getattr(self.session, "profile_name", None)  # type: ignore[attr-defined]
        cmd = [
            "aws",
            "ecs",
            "execute-command",
            "--cluster",
            self.exec_cluster,
            f"--task={task.taskArn}",
            f"--container={container}",
            "--interactive",
            "--command",
            command,
        ]
        if profile:
            cmd[1:1] = ["--profile", profile]

        self.__ensure_aws_cli_supports_ecs_execute_command()
        process = subprocess.Popen(cmd)
        signal.signal(signal.SIGINT, build_sigint_handler(process))
        process.wait()
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def __resolve_exec_task(
        self,
        *,
        task_arn: str | None,
        running: "list[Task]",
    ) -> "Task":
        """
        Choose the task to exec into.

        Keyword Args:
            task_arn: Requested task ARN or task ID suffix.
            running: Running tasks available on this object.

        Returns:
            The resolved task.

        Raises:
            ValueError: ``task_arn`` does not match a running task.

        """
        if task_arn is None:
            return running[0]
        for task in running:
            if task.taskArn == task_arn or task.taskArn.endswith(f"/{task_arn}"):
                return task
        msg = f"Task {task_arn!r} not found among running tasks."
        raise ValueError(msg)

    def __resolve_exec_container(
        self,
        *,
        task: "Task",
        container_name: str | None,
    ) -> str:
        """
        Choose the container name to exec into.

        Keyword Args:
            task: Task that owns the container.
            container_name: Requested container name.

        Returns:
            The resolved container name.

        Raises:
            ValueError: The task has no containers or the name is unknown.

        """
        if not task.containers:
            msg = f"Task {task.taskArn!r} has no containers."
            raise ValueError(msg)
        if container_name is None:
            name = task.containers[0].name
            if not name:
                msg = f"Task {task.taskArn!r} has no named containers."
                raise ValueError(msg)
            return name
        names = [container.name for container in task.containers if container.name]
        if container_name not in names:
            msg = (
                f"Container {container_name!r} not found on task {task.taskArn!r}; "
                f"available: {', '.join(names)}"
            )
            raise ValueError(msg)
        return container_name

    def __ensure_aws_cli_supports_ecs_execute_command(self) -> None:
        """
        Ensure the local AWS CLI exposes ``ecs execute-command``.

        Raises:
            RuntimeError: The AWS CLI is missing or does not support ECS Exec.

        """
        aws_path = shutil.which("aws")
        if aws_path is None:
            msg = "AWS CLI is not installed or not in PATH."
            raise RuntimeError(msg)
        result = subprocess.run(
            [aws_path, "ecs", "help"],
            check=False,
            capture_output=True,
            text=True,
        )
        help_text = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0 or "execute-command" not in help_text:
            msg = (
                "Local AWS CLI does not expose `aws ecs execute-command`. "
                "Install a current AWS CLI v2 and the Session Manager plugin."
            )
            raise RuntimeError(msg)


class ECSServiceModelMixin(ECSExecMixin):
    """
    A mixin for :py:class:`botocraft.services.ecs.Service` that adds
    some additional methods that we can't auto generate.
    """

    @property
    def running_tasks(self) -> "list[Task]":
        """
        Return running tasks for this service.

        Returns:
            Tasks in ``RUNNING`` status for the service.

        """
        tasks = self.tasks or []  # type: ignore[attr-defined]
        return [task for task in tasks if task.lastStatus == "RUNNING"]

    @property
    def exec_cluster(self) -> str:
        """
        Return the cluster identifier for ECS Exec on this service.

        Returns:
            Cluster short name when available, otherwise the cluster ARN.

        """
        cluster_name = self.cluster_name  # type: ignore[attr-defined]
        if cluster_name:
            return cluster_name
        return self.clusterArn  # type: ignore[attr-defined]

    @property
    def required_cpu(self) -> int:
        """
        The required CPU for the service in CPU shares.  One full CPU is
        equivalent to 1024 CPU shares.
        """
        cpu: int = 0
        td = self.task_definition  # type: ignore[attr-defined]
        if td.cpu:
            cpu = int(td.cpu)
        else:
            for container in td.containerDefinitions:
                if container.cpu:
                    cpu += container.cpu
        return cpu

    @property
    def required_memory(self) -> int:
        """
        Return the required memory for the service in MiB.
        """
        memory: int = 0
        td = self.task_definition  # type: ignore[attr-defined]
        if td.memory:
            memory = int(td.memory)
        else:
            for container in td.containerDefinitions:
                if container.memory:
                    memory += container.memory
        return int(memory)

    @property
    def container_instances(self) -> "PrimaryBoto3ModelQuerySet":
        """
        Return the :py:class:`botocraft.services.ecs.ContainerInstance` objects which
        are running our tasks for the service.
        """
        return PrimaryBoto3ModelQuerySet(
            [task.container_instance for task in self.tasks]  # type: ignore[attr-defined]
        )

    @property
    def is_stable(self) -> bool:
        """
        Return whether the service is stable or not.
        """
        # this is the same test that the `services_stable` waiter uses
        return len(self.deployments) == 1 and (self.runningCount == self.desiredCount)  # type: ignore[attr-defined]

    def wait_until_stable(self, max_attempts: int = 40, delay: int = 15) -> None:
        """
        Wait until the service is stable.

        Raises:
            botocore.exceptions.WaiterError: if the service is not stable after
                ``max_attempts``, or some other error occurred.

        Keyword Args:
            max_attempts: The maximum number of attempts to make before giving
                up.
            delay: The number of seconds to wait between attempts.

        """
        waiter_config = {}
        if max_attempts:
            waiter_config["maxAttempts"] = max_attempts
        if delay:
            waiter_config["delay"] = delay
        if waiter_config:
            waiter_config["operation"] = "DescribeServices"  # type: ignore[assignment]
        waiter = self.objects.using(self.session).get_waiter(
            "services_stable", WaiterConfig=waiter_config
        )  # type: ignore[attr-defined]
        waiter.wait(cluster=self.clusterArn, services=[self.serviceName])  # type: ignore[attr-defined]

    def scale(
        self,
        desired_count: int,
        wait: bool = False,
    ) -> None:
        """
        Scale the service to the desired count.  If ``wait`` is True, this will
        wait for the service to reach the desired count using the ``services_stable``
        boto3 waiter.

        Args:
            desired_count: The number of tasks to run.

        Keyword Args:
            wait: If True, wait for the service to reach the desired count.

        """
        self.objects.using(self.session).partial_update(  # type: ignore[attr-defined]
            self.serviceName,  # type: ignore[attr-defined]
            cluster=self.clusterArn,  # type: ignore[attr-defined]
            desiredCount=desired_count,
        )
        waiter = self.objects.using(self.session).get_waiter("services_stable")  # type: ignore[attr-defined]
        if wait:
            waiter.wait(
                cluster=self.clusterArn,  # type: ignore[attr-defined]
                services=[self.serviceName],  # type: ignore[attr-defined]
            )

    @property
    def load_balancers(self) -> "PrimaryBoto3ModelQuerySet":
        """
        Return the :py:class:`LoadBalancer` objects that are associated with the
        service.
        """
        from botocraft.services import LoadBalancer

        arns: set[str] = set()
        for tg in self.target_groups:  # type: ignore[attr-defined]
            for arn in tg.LoadBalancerArns:
                arns.add(arn)
        if arns:
            return LoadBalancer.objects.using(self.session).list(
                LoadBalancerArns=list(arns)
            )
        return PrimaryBoto3ModelQuerySet([])  # type: ignore[arg-type]


class ECSTaskModelMixin(ECSExecMixin):
    """
    A mixin for :py:class:`botocraft.services.ecs.Task` that adds convenience
    methods that we can't auto generate.
    """

    @property
    def running_tasks(self) -> "list[Task]":
        """
        Return this task when it is running.

        Returns:
            A single-element list when
            :py:attr:`~botocraft.services.ecs.Task.lastStatus` is ``RUNNING``;
            otherwise an empty list.

        """
        if self.lastStatus == "RUNNING":  # type: ignore[attr-defined]
            return [self]  # type: ignore[list-item]
        return []

    @property
    def exec_cluster(self) -> str:
        """
        Return the cluster identifier for ECS Exec on this task.

        Returns:
            Cluster short name when :py:attr:`~botocraft.services.ecs.Task.clusterArn`
            is an ARN; otherwise the raw cluster value.

        """
        return _cluster_name_from_arn(self.clusterArn)  # type: ignore[attr-defined]

    def exec(
        self,
        *,
        task_arn: str | None = None,
        container_name: str | None = None,
        command: str = "/bin/sh",
    ) -> None:
        """
        Exec into a container on this task using ECS Exec.

        Side Effects:
            Runs ``aws ecs execute-command`` in the foreground until the remote
            session ends.

        Keyword Args:
            task_arn: Must be omitted or match this task's ARN.
            container_name: Container name to use. When omitted, the first
                container on the task is used.
            command: Shell command passed to ``--command``.

        Raises:
            ECSExecMixin.NoRunningTasks: This task is not in ``RUNNING`` status.
            RuntimeError: The AWS CLI is missing or ``execute-command`` is unavailable.
            ValueError: ``task_arn`` does not match this task, or the container
                name is unknown.

        """
        if task_arn is not None and task_arn not in {
            self.taskArn,  # type: ignore[attr-defined]
            self.taskArn.split("/")[-1],  # type: ignore[attr-defined, union-attr]
        }:
            msg = (
                f"task_arn {task_arn!r} does not match task {self.taskArn!r}."
            )
            raise ValueError(msg)
        super().exec(
            task_arn=self.taskArn,  # type: ignore[attr-defined]
            container_name=container_name,
            command=command,
        )


class ECSServiceManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.ServiceManager` that adds
    some additional methods that we can't auto generate.
    """

    def all(
        self,
        launchType: Literal["EC2", "FARGATE", "EXTERNAL"] | None = None,  # noqa: N803
        schedulingStrategy: Literal["REPLICA", "DAEMON"] | None = None,  # noqa: N803
        tags: dict[str, str] | None = None,
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return all the services in the account.  This differs from
        :py:meth:`botocraft.services.ServiceManager.list` in that it iterates
        through all the clusters in the account and gets the services for each
        cluster.

        Normally you would expect to use
        :py:meth:`botocraft.services.ServiceManager.list` to get all the
        services, but ``describe_services``, on which our method is based, only
        returns services for a single cluster, so we need to roll our own
        method.

        Args:
            launchType: The launch type of the services to return.
            schedulingStrategy: The scheduling strategy of the services to return.
            tags: A dictionary of tags to filter the services

        Returns:
            A list of :py:class:`Service` objects.

        """
        from botocraft.services import Cluster, Service

        if not tags:
            tags = {}

        clusters = Cluster.objects.using(self.session).list()
        services: list["Service"] = []  # noqa: UP037
        for cluster in clusters:
            if tags.items() <= cluster.tags.items():
                services.extend(
                    Service.objects.using(self.session).list(
                        cluster=cluster.clusterArn,
                        launchType=launchType,
                        schedulingStrategy=schedulingStrategy,
                    )
                )
        return PrimaryBoto3ModelQuerySet(services)  # type: ignore[arg-type]


class CapacityProviderManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.CapacityProviderManager`.

    This mixin provides list behavior for capacity providers because
    ``describe_capacity_providers`` is both the detail endpoint and the only
    API that can enumerate all capacity providers, including paginated
    unfiltered results.
    """

    def list(
        self,
        *,
        capacityProviders: list[str] | None = None,  # noqa: N803
        cluster: str | None = None,
        include: list[Literal["TAGS"]] | None = None,
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return capacity providers for the given scope.

        Keyword Args:
            capacityProviders: Optional capacity provider names or ARNs to
                resolve directly.
            cluster: Optional cluster name or ARN to scope the describe call.
            include: Optional extra fields to include in the response.

        Returns:
            A list of :py:class:`botocraft.services.ecs.CapacityProvider`
            objects.

        """
        from botocraft.services import CapacityProvider

        if capacityProviders:
            return self.get_many(  # type: ignore[attr-defined]
                capacityProviders=capacityProviders,
                cluster=cluster,
                include=include,
            )

        providers: list[CapacityProvider] = []
        next_token: str | None = None
        while True:
            args = {
                "cluster": cluster,
                "include": include,
                "maxResults": 100,
                "nextToken": next_token,
            }
            response = self.client.describe_capacity_providers(
                **{key: value for key, value in args.items() if value is not None}
            )
            page = [
                CapacityProvider(**provider)
                for provider in response.get("capacityProviders", [])
            ]
            self.sessionize(page)  # type: ignore[attr-defined]
            providers.extend(page)
            next_token = response.get("nextToken")
            if not next_token:
                break
        return PrimaryBoto3ModelQuerySet(providers)  # type: ignore[arg-type]


class TaskSetManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.TaskSetManager`.

    This mixin provides a scoped list operation because
    ``describe_task_sets`` requires service and cluster context, requires a
    non-empty ``taskSets`` argument at runtime, and does not have a standalone
    paginator-backed list API.

    .. note::

        Task sets apply only to services that use the ``EXTERNAL`` deployment
        controller. Services that use the default ``ECS`` deployment controller
        (including rolling and blue/green deployments managed by ECS) do not
        expose task sets on
        :py:meth:`~botocraft.services.ecs.ServiceManager.get_many` or
        :py:attr:`~botocraft.services.ecs.Service.taskSets`, so
        :py:meth:`list` and :py:attr:`~botocraft.services.ecs.Service.task_sets`
        typically return empty results for those services.
    """

    def list(
        self,
        *,
        service: str,
        cluster: str,
        include: list[Literal["TAGS"]] | None = None,
        taskSets: list[str] | None = None,  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return task sets for a service and cluster.

        Task sets exist only for ``EXTERNAL`` deployment-controller services.
        For ``ECS`` deployment-controller services, omitting ``taskSets`` is
        expected and returns an empty queryset without calling AWS.

        Keyword Args:
            service: The service name or ARN that owns the task sets.
            cluster: The cluster name or ARN that owns the task sets.
            include: Optional extra fields to include in the response.
            taskSets: Task set names or ARNs to describe. Although botocore marks
                this argument optional, ECS rejects omitted, ``None``, and empty
                values with ``InvalidParameterException``.

        Returns:
            A list of :py:class:`botocraft.services.ecs.TaskSet` objects.

        """
        if not taskSets:
            return PrimaryBoto3ModelQuerySet([])  # type: ignore[arg-type]

        return self.get_many(  # type: ignore[attr-defined]
            cluster=cluster,
            service=service,
            include=include,
            taskSets=taskSets,
        )


class ServiceRevisionManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.ServiceRevisionManager`.

    This mixin preserves relation ergonomics for service revisions by exposing a
    list method that delegates to ``get_many`` with ARN batches.
    """

    def list(
        self,
        *,
        serviceRevisionArns: list[str] | None = None,  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return service revisions for the given ARNs.

        Keyword Args:
            serviceRevisionArns: The service revision ARNs to describe.

        Returns:
            A list of :py:class:`botocraft.services.ecs.ServiceRevision`
            objects.

        """
        if not serviceRevisionArns:
            return PrimaryBoto3ModelQuerySet([])  # type: ignore[arg-type]
        return self.get_many(  # type: ignore[attr-defined]
            serviceRevisionArns=serviceRevisionArns
        )


class DaemonManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.DaemonManager`.

    This mixin preserves a model-centric daemon contract even though the ECS
    daemon APIs return partial objects for create, update, delete, and list.
    """

    def _create_args(self, model: "Daemon") -> dict[str, Any]:
        """
        Build create-daemon request arguments from a daemon model.

        Args:
            model: The daemon model to serialize.

        Returns:
            The request arguments for ``create_daemon``.

        """
        args: dict[str, Any] = {
            "daemonName": model.daemonName,
            "clusterArn": model.clusterArn,
            "daemonTaskDefinitionArn": model.daemonTaskDefinitionArn,
            "capacityProviderArns": model.capacityProviderArns,
            "propagateTags": model.propagateTags,
            "enableECSManagedTags": model.enableECSManagedTags,
            "enableExecuteCommand": model.enableExecuteCommand,
        }
        if model.deploymentConfiguration:
            args["deploymentConfiguration"] = self.serialize(
                model.deploymentConfiguration
            )
        if model.Tags:
            args["tags"] = self.serialize(model.Tags)
        return {key: value for key, value in args.items() if value is not None}

    def _update_args(self, model: "Daemon") -> dict[str, Any]:
        """
        Build update-daemon request arguments from a daemon model.

        Args:
            model: The daemon model to serialize.

        Returns:
            The request arguments for ``update_daemon``.

        """
        args: dict[str, Any] = {
            "daemonArn": model.daemonArn,
            "daemonTaskDefinitionArn": model.daemonTaskDefinitionArn,
            "capacityProviderArns": model.capacityProviderArns,
            "propagateTags": model.propagateTags,
            "enableECSManagedTags": model.enableECSManagedTags,
            "enableExecuteCommand": model.enableExecuteCommand,
        }
        if model.deploymentConfiguration:
            args["deploymentConfiguration"] = self.serialize(
                model.deploymentConfiguration
            )
        return {key: value for key, value in args.items() if value is not None}

    def get_many(
        self,
        daemonArns: list[str],  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return daemons for the given ARNs.

        Args:
            daemonArns: The daemon ARNs to hydrate.

        Returns:
            A list of :py:class:`botocraft.services.ecs.Daemon` objects.

        """
        daemons = [self.get(daemonArn=daemon_arn) for daemon_arn in daemonArns]  # type: ignore[attr-defined]
        return PrimaryBoto3ModelQuerySet([daemon for daemon in daemons if daemon])

    def list(
        self,
        *,
        clusterArn: str | None = None,  # noqa: N803
        capacityProviderArns: list[str] | None = None,  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return daemons for the given ECS scope.

        Keyword Args:
            clusterArn: Optional cluster ARN to scope the daemon listing.
            capacityProviderArns: Optional capacity provider ARNs to filter by.

        Returns:
            A list of :py:class:`botocraft.services.ecs.Daemon` objects.

        """
        daemon_arns: list[str] = []
        next_token: str | None = None
        while True:
            args = {
                "clusterArn": clusterArn,
                "capacityProviderArns": capacityProviderArns,
                "maxResults": 100,
                "nextToken": next_token,
            }
            response = self.client.list_daemons(
                **{key: value for key, value in args.items() if value is not None}
            )
            daemon_arns.extend(
                summary["daemonArn"]
                for summary in response.get("daemonSummariesList", [])
                if summary.get("daemonArn")
            )
            next_token = response.get("nextToken")
            if not next_token:
                break
        daemons = [self.get(daemonArn=daemon_arn) for daemon_arn in daemon_arns]  # type: ignore[attr-defined]
        return PrimaryBoto3ModelQuerySet(
            [cast("Daemon", daemon) for daemon in daemons if daemon]
        )

    def create(self, model: "Daemon") -> "Daemon":
        """
        Create a daemon and return hydrated model.

        Args:
            model: The daemon to create.

        Side Effects:
            Calls ``create_daemon`` against AWS.

        Returns:
            The created :py:class:`botocraft.services.ecs.Daemon`.

        """
        response = self.client.create_daemon(**self._create_args(model))
        return self.get(daemonArn=response["daemonArn"])  # type: ignore[attr-defined]

    def update(self, model: "Daemon") -> "Daemon":
        """
        Update a daemon and return hydrated model.

        Args:
            model: The daemon to update.

        Side Effects:
            Calls ``update_daemon`` against AWS.

        Returns:
            The updated :py:class:`botocraft.services.ecs.Daemon`.

        """
        response = self.client.update_daemon(**self._update_args(model))
        return self.get(daemonArn=response["daemonArn"])  # type: ignore[attr-defined]

    def delete(self, model: "Daemon") -> "Daemon":
        """
        Delete a daemon and return pre-delete snapshot.

        Args:
            model: The daemon to delete.

        Side Effects:
            Calls ``delete_daemon`` against AWS.

        Returns:
            The prefetched :py:class:`botocraft.services.ecs.Daemon`.

        """
        daemon = self.get(daemonArn=model.daemonArn)  # type: ignore[attr-defined]
        self.client.delete_daemon(daemonArn=model.daemonArn)
        return cast("Daemon", daemon)


class DaemonTaskDefinitionManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.DaemonTaskDefinitionManager`.

    This mixin hydrates identifier-centric daemon task definition workflows into
    full Botocraft models.
    """

    def _create_args(self, model: "DaemonTaskDefinition") -> dict[str, Any]:
        """
        Build register-daemon-task-definition request arguments.

        Args:
            model: The daemon task definition model to serialize.

        Returns:
            The request arguments for ``register_daemon_task_definition``.

        """
        args: dict[str, Any] = {
            "family": model.family,
            "taskRoleArn": model.taskRoleArn,
            "executionRoleArn": model.executionRoleArn,
            "containerDefinitions": self.serialize(model.containerDefinitions),
            "cpu": model.cpu,
            "memory": model.memory,
        }
        if model.volumes:
            args["volumes"] = self.serialize(model.volumes)
        if model.Tags:
            args["tags"] = self.serialize(model.Tags)
        return {key: value for key, value in args.items() if value is not None}

    def get_many(
        self,
        daemonTaskDefinitions: list[str],  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return daemon task definitions for the given identifiers.

        Args:
            daemonTaskDefinitions: The daemon task definition identifiers to
                hydrate.

        Returns:
            A list of :py:class:`botocraft.services.ecs.DaemonTaskDefinition`
            objects.

        """
        task_definitions = [
            self.get(daemonTaskDefinition=identifier)  # type: ignore[attr-defined]
            for identifier in daemonTaskDefinitions
        ]
        return PrimaryBoto3ModelQuerySet(
            [task_definition for task_definition in task_definitions if task_definition]
        )

    def list(
        self,
        *,
        familyPrefix: str | None = None,  # noqa: N803
        family: str | None = None,
        revision: str | None = None,
        status: str | None = None,
        sort: str | None = None,
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return daemon task definitions for the given ECS scope.

        Keyword Args:
            familyPrefix: Optional family prefix filter.
            family: Optional exact family filter.
            revision: Optional revision filter.
            status: Optional status filter.
            sort: Optional sort order.

        Returns:
            A list of :py:class:`botocraft.services.ecs.DaemonTaskDefinition`
            objects.

        """
        identifiers: list[str] = []
        next_token: str | None = None
        while True:
            args = {
                "familyPrefix": familyPrefix,
                "family": family,
                "revision": revision,
                "status": status,
                "sort": sort,
                "maxResults": 100,
                "nextToken": next_token,
            }
            response = self.client.list_daemon_task_definitions(
                **{key: value for key, value in args.items() if value is not None}
            )
            identifiers.extend(
                summary["daemonTaskDefinitionArn"]
                for summary in response.get("daemonTaskDefinitions", [])
                if summary.get("daemonTaskDefinitionArn")
            )
            next_token = response.get("nextToken")
            if not next_token:
                break
        return self.get_many(identifiers)

    def create(self, model: "DaemonTaskDefinition") -> "DaemonTaskDefinition":
        """
        Register daemon task definition and return hydrated model.

        Args:
            model: The daemon task definition to register.

        Side Effects:
            Calls ``register_daemon_task_definition`` against AWS.

        Returns:
            The created :py:class:`botocraft.services.ecs.DaemonTaskDefinition`.

        """
        response = self.client.register_daemon_task_definition(
            **self._create_args(model)
        )
        return self.get(  # type: ignore[attr-defined]
            daemonTaskDefinition=response["daemonTaskDefinitionArn"]
        )

    def delete(self, model: "DaemonTaskDefinition") -> "DaemonTaskDefinition":
        """
        Delete daemon task definition and return pre-delete snapshot.

        Args:
            model: The daemon task definition to delete.

        Side Effects:
            Calls ``delete_daemon_task_definition`` against AWS.

        Returns:
            The prefetched
            :py:class:`botocraft.services.ecs.DaemonTaskDefinition`.

        """
        task_definition = self.get(  # type: ignore[attr-defined]
            daemonTaskDefinition=model.daemonTaskDefinitionArn
        )
        self.client.delete_daemon_task_definition(
            daemonTaskDefinition=model.daemonTaskDefinitionArn
        )
        return cast("DaemonTaskDefinition", task_definition)


class DaemonDeploymentManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.DaemonDeploymentManager`.

    This mixin models daemon deployments as a scoped read-only list surface.
    """

    def list(
        self,
        *,
        daemonArn: str,  # noqa: N803
        status: list[str] | None = None,
        createdAt: dict[str, Any] | None = None,  # noqa: N803
        nextToken: str | None = None,  # noqa: N803
        maxResults: int | None = None,  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return daemon deployments for a daemon scope.

        Keyword Args:
            daemonArn: The daemon ARN that owns the deployments.
            status: Optional deployment status filters.
            createdAt: Optional created-at filter object accepted by AWS.
            nextToken: Optional pagination token.
            maxResults: Optional page size.

        Returns:
            A list of :py:class:`botocraft.services.ecs.DaemonDeployment`
            objects.

        """
        from botocraft.services import DaemonDeployment

        args = {
            "daemonArn": daemonArn,
            "status": status,
            "createdAt": createdAt,
            "nextToken": nextToken,
            "maxResults": maxResults,
        }
        response = self.client.list_daemon_deployments(
            **{key: value for key, value in args.items() if value is not None}
        )
        deployments = [
            DaemonDeployment(**deployment)
            for deployment in response.get("daemonDeployments", [])
        ]
        self.sessionize(deployments)  # type: ignore[attr-defined]
        return PrimaryBoto3ModelQuerySet(deployments)  # type: ignore[arg-type]


class ExpressGatewayServiceManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.ExpressGatewayServiceManager`.

    This mixin preserves scoped list semantics and hydrates partial update
    responses into full Botocraft models.
    """

    def _update_args(self, model: "ExpressGatewayService") -> dict[str, Any]:
        """
        Build update-express-gateway-service request arguments.

        Args:
            model: The Express gateway service model to serialize.

        Returns:
            The request arguments for ``update_express_gateway_service``.

        """
        args = {
            "serviceArn": model.serviceArn,
            "executionRoleArn": model.executionRoleArn,
            "healthCheckPath": model.healthCheckPath,
            "primaryContainer": self.serialize(model.primaryContainer),
            "taskRoleArn": model.taskRoleArn,
            "networkConfiguration": self.serialize(model.networkConfiguration),
            "cpu": model.cpu,
            "memory": model.memory,
            "scalingTarget": self.serialize(model.scalingTarget),
        }
        return {key: value for key, value in args.items() if value is not None}

    def list(
        self,
        *,
        namespace: str,
        nextToken: str | None = None,  # noqa: N803
        maxResults: int | None = None,  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return Express gateway services for a namespace scope.

        Keyword Args:
            namespace: The namespace that scopes the service list.
            nextToken: Optional pagination token.
            maxResults: Optional page size.

        Returns:
            A list of :py:class:`botocraft.services.ecs.ExpressGatewayService`
            objects.

        """
        services = []
        args = {
            "namespace": namespace,
            "nextToken": nextToken,
            "maxResults": maxResults,
        }
        response = self.client.list_services_by_namespace(
            **{key: value for key, value in args.items() if value is not None}
        )
        for service_arn in response.get("serviceArns", []):
            service = self.get(serviceArn=service_arn)  # type: ignore[attr-defined]
            if service:
                services.append(service)
        return PrimaryBoto3ModelQuerySet(services)

    def update(self, model: "ExpressGatewayService") -> "ExpressGatewayService":
        """
        Update Express gateway service and return hydrated model.

        Args:
            model: The Express gateway service to update.

        Side Effects:
            Calls ``update_express_gateway_service`` against AWS.

        Returns:
            The updated :py:class:`botocraft.services.ecs.ExpressGatewayService`.

        """
        response = self.client.update_express_gateway_service(
            **self._update_args(model)
        )
        service_arn = response["service"]["serviceArn"]
        return self.get(serviceArn=service_arn)  # type: ignore[attr-defined]


class ECSContainerInstanceModelMixin:
    @property
    def free_cpu(self) -> int:
        """
        Return the free CPU shares on the container instance.  One full CPU is
        equivalent to 1024 CPU shares.
        """
        value: int = 0
        for resource in self.remainingResources:  # type: ignore[attr-defined]
            if resource.name == "CPU":
                value = int(resource.integerValue)
        return value

    @property
    def free_ram(self) -> int:
        """
        Return the free RAM in MiB on the container instance.
        """
        value: int = 0
        for resource in self.remainingResources:  # type: ignore[attr-defined]
            if resource.name == "MEMORY":
                value = int(resource.integerValue)
        return value


class TaskDefinitionManagerMixin:
    def in_use(
        self,
        tags: dict[str, str] | None = None,
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return a list of task definitions that are currently in use by a service
        or periodic task.  A periodic task is a task that is run via a
        :py:class:`botocraft.services.events.EventRule`.

        Important:
            If you have tasks that are run ad-hoc, then this method will not
            return those task definitions.

        Keyword Args:
            tags: A dictionary of tags to filter the task, services and periodic
                tasks by.  Default: None
            verbose: If True, print out some information about what is happening.

        Returns:
            A list of :py:class:`botocraft.services.ecs.TaskDefinition` objects that
            are currently in use.

        """
        from botocraft.services import (
            EventRule,
            Service,
            TaskDefinition,
        )

        if not tags:
            tags = {}

        task_definitions: dict[str, TaskDefinition] = {}

        # First get all the services in the account
        services: list[Service] = Service.objects.using(self.session).all()
        ClientException = self.session.client("ecs").exceptions.ClientException  # noqa: N806

        # Now iterate through each service and get the append its task definition
        # to the list of task definitions if we have not already seen it
        for service in services:
            try:
                task_definition = cast("TaskDefinition", service.task_definition)
            except ClientException:
                warnings.warn(
                    f"Task definition {service.taskDefinition} used by "
                    f"{service.cluster_name}:{service.serviceName} does not exist",
                    UserWarning,
                    stacklevel=2,
                )
                continue
            family_revision = task_definition.family_revision
            if family_revision not in task_definitions:
                task_definitions[family_revision] = task_definition

        # Now deal with the periodc tasks
        rules = EventRule.objects.using(self.session).list()
        for rule in rules:
            for target in rule.targets:
                if target.EcsParameters is not None:
                    try:
                        task_definition = TaskDefinition.objects.using(
                            self.session
                        ).get(target.EcsParameters.TaskDefinitionArn)
                    except ClientException:
                        warnings.warn(
                            f"Task definition {target.EcsParameters.TaskDefinitionArn} "
                            f"used by {rule.name} does not exist",
                            UserWarning,
                            stacklevel=2,
                        )
                        continue
                    family_revision = task_definition.family_revision
                    if family_revision not in task_definitions:
                        task_definitions[family_revision] = task_definition
        return PrimaryBoto3ModelQuerySet(list(task_definitions.values()))  # type: ignore[arg-type]


class TaskDefinitionModelMixin:
    @property
    def family_revision(self) -> str:
        """
        Return the family and revision of the task definition in the format
        ``<family>:<revision>``.
        """
        return f"{self.family}:{self.revision}"

    @property
    def image_objects(self) -> list["ECRImage"]:
        """
        Return the :class:`~botocraft.services.ecr.ECRImage` objects that this
        task definition uses across all its container definitions.

        Returns:
            A list of :class:`~botocraft.services.ecr.ECRImage` objects.

        """
        return [container.image_object for container in self.containerDefinitions]

    @property
    def images(self) -> list[str]:
        """
        Return the container images as a list of strings.

        Returns:
            A list of container images.

        """
        return [container.image for container in self.containerDefinitions]  # type: ignore[attr-defined]

    @property
    def container_images(self) -> list[str]:
        """
        Return the container images as a list of strings.

        Returns:
            A list of container images.

        """
        return [container.image for container in self.containerDefinitions]  # type: ignore[attr-defined]

    @cached_property
    def services(self) -> list["Service"]:
        """
        Return the services that use this task definition revision.

        Warning:
            This will be quite slow because we need to all our services
            to see if there is a service that uses that task definition.  There's
            no way to get all the services in an account, so we have to list
            all the clusters, then check each cluster for services, and see
            if the service uses this task definition.

        Returns:
            A list of :py:class:`botocraft.services.ecs.Service` objects that use
            this task definition.

        """
        from botocraft.services import Cluster, Service

        clusters = Cluster.objects.using(self.session).list()
        services: list[Service] = []
        for cluster in clusters:
            services.extend(
                service
                for service in cluster.services
                if service.taskDefinition == self.family_revision
            )
        return services

    def delete(self) -> None:
        """
        Delete the task definition.   We're overriding the default delete method
        because in this case, the manager method accepts a list of task definitions
        to delete, so we need to pass in the task definition ARN as a list.
        """
        self.objects.using(self.session).delete([self.taskDefinitionArn])


class ServiceDeploymentModelMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.ServiceDeployment` that adds
    some additional methods that we can't auto generate.
    """

    @property
    def source_task_definitions(self) -> "PrimaryBoto3ModelQuerySet":
        """
        Return the task definition for the deployment.
        """
        from botocraft.services import TaskDefinition

        arns = [source.arn for source in self.sourceServiceRevisions]

        return PrimaryBoto3ModelQuerySet(
            [TaskDefinition.objects.using(self.session).get(arn) for arn in arns]
        )  # type: ignore[arg-type]
