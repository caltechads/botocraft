import re
from typing import TYPE_CHECKING, Callable, List, Optional, cast

if TYPE_CHECKING:
    from botocraft.services import (
        Cluster,
        ContainerInstance,
        Service,
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
    assert (
        match
    ), f"Could not extract task family and revision from {task_definition_arn}"
    return f'{match.group("family")}:{match.group("revision")}'


# ----------
# Decorators
# ----------


# Service


def ecs_services_only(func: Callable[..., List[str]]) -> Callable[..., List["Service"]]:
    """
    Wraps :py:meth:`botocraft.services.ecs.ServiceManager.list` to return a list of
    :py:class:`botocraft.services.ecs.Service` objects instead of only a list of
    ARNs.
    """

    def wrapper(self, *args, **kwargs) -> List["Service"]:
        arns = func(self, *args, **kwargs)
        services = []
        # We have to do this in batches of 10 because the get_many method,
        # which uses the boto3 ``describe_services`` method, only accepts 10 ARNs
        # at a time.
        for i in range(0, len(arns), 10):
            services.extend(
                self.get_many(
                    arns[i : i + 10], cluster=kwargs["cluster"], include=["TAGS"]
                )
            )
        return services

    return wrapper


# Cluster


def ecs_clusters_only(func: Callable[..., List[str]]) -> Callable[..., List["Cluster"]]:
    """
    Wraps :py:meth:`botocraft.services.ecs.ClusterManager.list` to return a list of
    :py:class:`botocraft.services.ecs.Cluster` objects instead of only a list of
    ARNs.
    """

    def wrapper(self, *args, **kwargs) -> List["Cluster"]:
        arns = func(self, *args, **kwargs)
        clusters = []
        # We have to do this in batches of 100 because the get_many method,
        # which uses the boto3 ``describe_clusters`` method, only accepts 100 ARNs
        # at a time.
        for i in range(0, len(arns), 100):
            clusters.extend(self.get_many(clusters=arns[i : i + 100]))
        return clusters

    return wrapper


# TaskDefinition


def ecs_task_definitions_only(
    func: Callable[..., List[str]],
) -> Callable[..., List["TaskDefinition"]]:
    """
    Decorator to convert a list of ECS task definition identifiers to a list of
    :py:class:`botocraft.services.ecs.TaskDefinition` objects.
    """

    def wrapper(self, *args, **kwargs) -> List["TaskDefinition"]:
        identifiers = func(self, *args, **kwargs)
        return [self.get(identifier, include=["TAGS"]) for identifier in identifiers]

    return wrapper


# ContainerInstance


def ecs_container_instances_only(
    func: Callable[..., List[str]],
) -> Callable[..., List["ContainerInstance"]]:
    """
    Decorator to convert a list of ECS container instance arns to a list of
    :py:class:`botocraft.services.ecs.ContainerInstance` objects.
    """

    def wrapper(self, *args, **kwargs) -> List["ContainerInstance"]:
        arns = func(self, *args, **kwargs)
        container_instances = []
        for i in range(0, len(arns), 100):
            container_instances.extend(
                self.get_many(
                    cluster=kwargs["cluster"], containerInstances=arns[i : i + 100]
                )
            )
        return container_instances

    return wrapper


def ecs_container_instances_tasks_only(
    func: Callable[..., List[str]],
) -> Callable[..., List["Task"]]:
    """
    Decorator to convert a list of ECS container instance arns to a list of
    :py:class:`botocraft.services.ecs.ContainerInstance` objects.
    """

    def wrapper(self, *args, **kwargs) -> List["Task"]:
        from botocraft.services.ecs import Task

        arns = func(self, *args, **kwargs)
        tasks = []
        for i in range(0, len(arns), 100):
            tasks.extend(cast("TaskManager", Task.objects).get_many(arns[i : i + 100]))
        return tasks

    return wrapper


# Task
def ecs_task_populate_taskDefinition(  # noqa: N802
    func: Callable[..., Optional["Task"]],
) -> Callable[..., Optional["Task"]]:
    """
    Wraps :py:meth:`botocraft.services.ecs.TaskManager.get` to populate the
    :py:attr:`botocraft.services.ecs.Task.taskDefinition` attribute.

    We set the ``taskDefinition`` attribute to the task family and revision in the
    format ``<family>:<revision>``.  ``taskDefinition`` is an extra field that we
    add to the :py:class:`botocraft.services.ecs.Task` object that is not in the
    original botocore shape, but is useful for our purposes.
    """

    def wrapper(self, *args, **kwargs) -> Optional["Task"]:
        task = func(self, *args, **kwargs)
        if task:
            task.taskDefinition = extract_task_family_and_revision(
                task.taskDefinitionArn
            )
        return task

    return wrapper


def ecs_task_populate_taskDefinitions(  # noqa: N802
    func: Callable[..., List["Task"]],
) -> Callable[..., List["Task"]]:
    """
    Wraps :py:meth:`botocraft.services.ecs.TaskManager.get_many` to
    populate the :py:attr:`botocraft.services.ecs.Task.taskDefinition` attribute
    on each task.

    We set the ``taskDefinition`` attribute to the task family and revision in the
    format ``<family>:<revision>``.  ``taskDefinition`` is an extra field that we
    add to the :py:class:`botocraft.services.ecs.Task` object that is not in the
    original botocore shape, but is useful for our purposes.
    """

    def wrapper(self, *args, **kwargs) -> List["Task"]:
        tasks = func(self, *args, **kwargs)
        for task in tasks:
            task.taskDefinition = extract_task_family_and_revision(
                task.taskDefinitionArn
            )
        return tasks

    return wrapper


def ecs_tasks_only(func: Callable[..., List[str]]) -> Callable[..., List["Task"]]:
    """
    Wrap :py:meth:`botocraft.services.ecs.TaskManager.list` to return a list of
    :py:class:`botocraft.services.ecs.Task` objects instead of only a list of
    ARNs.
    """

    def wrapper(self, *args, **kwargs) -> List["Task"]:
        arns = func(self, *args, **kwargs)
        tasks = []
        # We have to do this in batches of 100 because the get_many method,
        # which uses the boto3 ``describe_tasks`` method, only accepts 100 ARNs
        # at a time.
        for i in range(0, len(arns), 100):
            tasks.extend(
                self.get_many(cluster=kwargs["cluster"], tasks=arns[i : i + 100])
            )
        return tasks

    return wrapper


# Mixins


class ECSServiceModelMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.Service` that adds
    some additional methods that we can't auto generate.
    """

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
    def container_instances(self) -> List["ContainerInstance"]:
        """
        Return the :py:class:`botocraft.services.ecs.ContainerInstance` objects which
        are running our tasks for the service.
        """
        return [task.container_instance for task in self.tasks]  # type: ignore[attr-defined]

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
        waiter = self.objects.get_waiter("services_stable", WaiterConfig=waiter_config)  # type: ignore[attr-defined]
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
        self.objects.partial_update(  # type: ignore[attr-defined]
            self.serviceName,  # type: ignore[attr-defined]
            cluster=self.clusterArn,  # type: ignore[attr-defined]
            desiredCount=desired_count,
        )
        waiter = self.objects.get_waiter("services_stable")  # type: ignore[attr-defined]
        if wait:
            waiter.wait(
                cluster=self.clusterArn,  # type: ignore[attr-defined]
                services=[self.serviceName],  # type: ignore[attr-defined]
            )


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
