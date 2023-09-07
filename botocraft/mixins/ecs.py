from typing import Callable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from botocraft.services import (
        Service,
        Cluster,
        ContainerInstance,
        TaskDefinition
    )


def ecs_services_only(func: Callable[..., List[str]]) -> Callable[..., List["Service"]]:
    """
    Decorator to convert a list of ECS service ARNs to a list of
    :py:class:`botocraft.services.ecs.Service` objects.
    """
    def wrapper(self, *args, **kwargs) -> List["Service"]:
        arns = func(self, *args, **kwargs)
        services = []
        for i in range(0, len(arns), 100):
            services.extend(
                self.get_many(
                    arns[i:i + 100],
                    cluster=kwargs['cluster'],
                    include=['TAGS']
                )
            )
        return services
    return wrapper


def ecs_clusters_only(func: Callable[..., List[str]]) -> Callable[..., List["Cluster"]]:
    """
    Decorator to convert a list of ECS cluster ARNs to a list of
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
