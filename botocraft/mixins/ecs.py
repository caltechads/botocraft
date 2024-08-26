import re
from typing import ClassVar, Callable, List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from botocraft.services import (
        Service,
        ServiceManager,
        Cluster,
        ContainerInstance,
        Task,
        TaskDefinition
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
    task_definition_arn_re = r"arn:aws:ecs:[^:]+:[^:]+:task-definition/(?P<family>[^:]+):(?P<revision>[0-9]+)"
    match = re.match(task_definition_arn_re, task_definition_arn)
    assert match, f'Could not extract task family and revision from {task_definition_arn}'
    return f'{match.group("family")}:{match.group("revision")}'


# ----------
# Decorators
# ----------


# Service

def ecs_services_only(func: Callable[..., List[str]]) -> Callable[..., List["Service"]]:
    """
    Convert a list of ECS service ARNs to a list of
    :py:class:`botocraft.services.ecs.Service` objects.
    """
    def wrapper(self, *args, **kwargs) -> List["Service"]:
        arns = func(self, *args, **kwargs)
        services = []
        for i in range(0, len(arns), 10):
            services.extend(
                self.get_many(
                    arns[i:i + 10],
                    cluster=kwargs['cluster'],
                    include=['TAGS']
                )
            )
        return services
    return wrapper


# Cluster

def ecs_clusters_only(func: Callable[..., List[str]]) -> Callable[..., List["Cluster"]]:
    """
    Convert a list of ECS cluster ARNs to a list of
    :py:class:`botocraft.services.ecs.Cluster` objects.
    """
    def wrapper(self, *args, **kwargs) -> List["Cluster"]:
        arns = func(self, *args, **kwargs)
        clusters = []
        for i in range(0, len(arns), 100):
            clusters.extend(
                self.get_many(clusters=arns[i:i + 100])
            )
        return clusters
    return wrapper


# TaskDefinition

def ecs_task_definitions_only(
    func: Callable[..., List[str]]
) -> Callable[..., List["TaskDefinition"]]:
    """
    Decorator to convert a list of ECS task definition identifiers to a list of
    :py:class:`botocraft.services.ecs.TaskDefinition` objects.
    """
    def wrapper(self, *args, **kwargs) -> List["TaskDefinition"]:
        identifiers = func(self, *args, **kwargs)
        task_definitions = []
        for identifier in identifiers:
            task_definitions.append(
                self.get(identifier, include=['TAGS'])
            )
        return task_definitions
    return wrapper


# ContainerInstance

def ecs_container_instances_only(
    func: Callable[..., List[str]]
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
                    cluster=kwargs['cluster'],
                    containerInstances=arns[i:i + 100]
                )
            )
        return container_instances
    return wrapper


# Task
def ecs_task_populate_taskDefinition(
    func: Callable[..., Optional["Task"]]
) -> Callable[..., Optional["Task"]]:
    """
    When getting a single task, populate the
    :py:attr:`botocraft.services.ecs.Task.taskDefinition` attribute.
    """
    def wrapper(self, *args, **kwargs) -> Optional["Task"]:
        task = func(self, *args, **kwargs)
        if task:
            task.taskDefinition = extract_task_family_and_revision(task.taskDefinitionArn)
        return task
    return wrapper


def ecs_task_populate_taskDefinitions(
    func: Callable[..., List["Task"]]
) -> Callable[..., List["Task"]]:
    """
    When getting a list of tasks, populate the
    :py:attr:`botocraft.services.ecs.Task.taskDefinition` attribute on each task.
    """
    def wrapper(self, *args, **kwargs) -> List["Task"]:
        tasks = func(self, *args, **kwargs)
        for task in tasks:
            task.taskDefinition = extract_task_family_and_revision(task.taskDefinitionArn)
        return tasks
    return wrapper


def ecs_tasks_only(
    func: Callable[..., List[str]]
) -> Callable[..., List["Task"]]:
    """
    Decorator to convert a list of ECS task arns to a list of
    :py:class:`botocraft.services.ecs.Task` objects.
    """
    def wrapper(self, *args, **kwargs) -> List["Task"]:
        arns = func(self, *args, **kwargs)
        tasks = []
        for i in range(0, len(arns), 100):
            tasks.extend(
                self.get_many(
                    cluster=kwargs['cluster'],
                    tasks=arns[i:i + 100]
                )
            )
        return tasks
    return wrapper


# Mixins

class ECSServiceModelMixin:

    def scale(
        self,
        desired_count: int,
        wait: bool = False,
    ) -> None:
        """
        Scale the service to the desired count.

        Args:
            desired_count: The number of tasks to run.

        Keyword Args:
            wait: If True, wait for the service to reach the desired count.
        """
        self.objects.partial_update(  # type: ignore[attr-defined]
            self.serviceName,  # type: ignore[attr-defined]
            cluster=self.cluster,  # type: ignore[attr-defined]
            desiredCount=desired_count
        )
        waiter = self.objects.get_waiter('services_stable')  # type: ignore[attr-defined]
        if wait:
            waiter.wait(
                cluster=self.cluster,  # type: ignore[attr-defined]
                services=[self.serviceName]  # type: ignore[attr-defined]
            )
