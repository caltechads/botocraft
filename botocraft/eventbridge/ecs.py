from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, cast

from .base import EventBridgeEvent
from .raw import (
    ECSAWSAPICallViaCloudTrailEvent as RawECSAWSAPICallViaCloudTrailEvent,
)
from .raw import (
    ECSContainerInstanceStateChangeEvent as RawECSContainerInstanceStateChangeEvent,
)
from .raw import (
    ECSServiceActionEvent as RawECSServiceActionEvent,
)
from .raw import (
    ECSServiceDeploymentStateChangeEvent as RawECSServiceDeploymentStateChangeEvent,
)
from .raw import (
    ECSTaskStateChangeEvent as RawECSTaskStateChangeEvent,
)

if TYPE_CHECKING:
    from botocraft.services.ecs import (
        Cluster,
        ContainerInstance,
        Service,
        Task,
        TaskDefinition,
    )


@dataclass
class SystemResources:
    """
    A dataclass that represents the system resources of a container instance,
    container or task.
    """

    #: The CPU units available on the container instance, container or task.
    cpu: float | None = None
    #: The memory available on the container instance, container or task.
    memory: float | None = None


class ECSTaskStateChangeEvent(EventBridgeEvent, RawECSTaskStateChangeEvent):
    """
    EventBridge event for ECS task state change.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        cluster_name = self.detail.clusterArn.split("/")[-1]
        family_and_revision = self.detail.taskDefinitionArn.split("/")[-1]
        return (
            f"<Event: ECS Task State Change: [{self.account}]: "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"task_definition={family_and_revision}, "
            f"cluster={cluster_name}, "
            f"desired_status={self.detail.desiredStatus}>"
        )

    @property
    def task_definition(self) -> "TaskDefinition":
        """
        Get the :py:class:`~botocraft.services.ecs.TaskDefinition` object
        from the event.


        """
        from botocraft.services.ecs import TaskDefinition

        return TaskDefinition.objects.using(self.session).get(
            taskDefinition=self.detail.taskDefinitionArn
        )

    @property
    def cluster(self) -> "Cluster":
        """
        Get the cluster name from the event.
        """
        from botocraft.services.ecs import Cluster

        return Cluster.objects.using(self.session).get(cluster=self.detail.clusterArn)

    @property
    def container_instance(self) -> Optional["ContainerInstance"]:
        """
        Get the container instance ARN from the event.
        """
        from botocraft.services.ecs import ContainerInstance

        if not self.detail.containerInstanceArn:
            return None
        return ContainerInstance.objects.using(self.session).get(
            self.detail.containerInstanceArn, cluster=self.detail.clusterArn
        )

    @property
    def task(self) -> str:
        """
        Get the task ARN from the event.
        """
        from botocraft.services.ecs import Task

        return Task.objects.using(self.session).get(
            task=self.detail.taskArn, cluster=self.detail.clusterArn
        )

    @property
    def architecture(self) -> str:
        """
        Get the architecture of the task from the event.
        """
        for attribute in self.detail.attributes:
            if attribute.name == "ecs.architecture":
                return cast("str", attribute.value)
        return "x86_64"

    @property
    def is_fargate(self) -> bool:
        """
        Check if the task is a Fargate task.
        """
        return self.detail.launchType == "FARGATE"


class ECSServiceActionEvent(EventBridgeEvent, RawECSServiceActionEvent):
    """
    EventBridge event for ECS service action.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        cluster_name = self.detail.clusterArn.split("/")[-1]
        service_names = [resource.split("/")[-1] for resource in self.resources or []]
        return (
            f"<Event: ECS Service Action: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"services={service_names}, "
            f"cluster={cluster_name}, "
            f"event_type={self.detail.eventType}, "
            f"event_name={self.detail.eventName}>"
        )

    @property
    def cluster(self) -> "Cluster":
        """
        Get the cluster name from the event.
        """
        from botocraft.services.ecs import Cluster

        return Cluster.objects.get(cluster=self.detail.clusterArn)

    @property
    def tasks(self) -> list["Task"] | None:
        """
        Get the task ARNs from the event.
        """
        from botocraft.services.ecs import Task

        if not self.detail.taskArns:
            return None
        return [
            Task.objects.using(self.session).get(
                task=taskArn, cluster=self.detail.clusterArn
            )
            for taskArn in self.detail.taskArns
        ]

    @property
    def container_instances(self) -> list["ContainerInstance"] | None:
        """
        Get the container instance ARN from the event.
        """
        from botocraft.services.ecs import ContainerInstance

        if not self.detail.containerInstanceArns:
            return None

        return [
            ContainerInstance.objects.using(self.session).get(
                containerInstanceArn=containerInstanceArn,
                cluster=self.detail.clusterArn,
            )
            for containerInstanceArn in self.detail.containerInstanceArns
        ]

    @property
    def services(self) -> list["Service"]:
        """
        Get the service ARN from the event.
        """
        from botocraft.services.ecs import Service

        return [
            Service.objects.using(self.session).get(
                service=service_arn, cluster=self.detail.clusterArn
            )
            for service_arn in self.resources or []
        ]

    @property
    def event_type(self) -> str:
        """
        Get the event type from the event.
        """
        return self.detail.eventType


class ECSContainerInstanceStateChangeEvent(
    EventBridgeEvent, RawECSContainerInstanceStateChangeEvent
):
    """
    EventBridge event for ECS container instance state change.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        cluster_name = self.detail.clusterArn.split("/")[-1]
        return (
            f"<Event: ECS Container Instance State Change: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"cluster={cluster_name}, "
            f"ec2_instance={self.detail.ec2InstanceId}, "
            f"status={self.detail.status}, "
            f"status_reason={self.detail.statusReason}>"
        )

    @property
    def cluster(self) -> "Cluster":
        """
        Get the cluster name from the event.
        """
        from botocraft.services.ecs import Cluster

        return Cluster.objects.using(self.session).get(cluster=self.detail.clusterArn)

    @property
    def container_instance(self) -> "ContainerInstance":
        """
        Get the container instance ARN from the event.
        """
        from botocraft.services.ecs import ContainerInstance

        return ContainerInstance.objects.using(self.session).get(
            containerInstance=self.detail.containerInstanceArn,
            cluster=self.detail.clusterArn,
        )

    @property
    def remainingResources(self) -> SystemResources:
        """
        Return the remaining resources (CPU and memory) on the container
        instance.

        """
        for resource in self.detail.remainingResources:
            if resource.name == "CPU":
                cpu = resource.integerValue
            elif resource.name == "MEMORY":
                memory = resource.integerValue
        return SystemResources(cpu=cpu, memory=memory)

    @property
    def registeredResources(self) -> SystemResources:
        """
        Return the full system resources (CPU and memory) of the container
        instance.

        """
        for resource in self.detail.registeredResources:
            if resource.name == "CPU":
                cpu = resource.integerValue
            elif resource.name == "MEMORY":
                memory = resource.integerValue
        return SystemResources(cpu=cpu, memory=memory)


class ECSServiceDeploymentStateChangeEvent(
    EventBridgeEvent, RawECSServiceDeploymentStateChangeEvent
):
    """
    EventBridge event for ECS service deployment state change.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECS Service Deployment Change: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"event_type={self.detail.eventType}, "
            f"event_name={self.detail.eventName}, "
            f"reason={self.detail.reason}>"
        )

    @property
    def cluster(self) -> "Cluster":
        """
        Get the cluster name from the event.
        """
        from botocraft.services.ecs import Cluster

        return Cluster.objects.using(self.session).get(cluster=self.detail.clusterArn)  # type: ignore[attr-defined]

    @property
    def service(self) -> "Service":
        """
        Get the service ARN from the event.
        """
        from botocraft.services.ecs import Service

        service_arn = self.resources[0]
        service_name = service_arn.split("/")[-1]
        cluster_name = service_arn.split("/")[-2]
        return Service.objects.using(self.session).get(
            service=service_name, cluster=cluster_name
        )


class ECSAWSAPICallViaCloudTrailEvent(
    EventBridgeEvent, RawECSAWSAPICallViaCloudTrailEvent
):
    """
    EventBridge event for ECS API call via CloudTrail.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECS API Call via CloudTrail: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"event_type={self.detail.eventType}, "
            f"event_name={self.detail.eventName}>"
        )

    @property
    def clusters(self) -> list["Cluster"]:
        """
        Get the cluster name from the event.
        """
        from botocraft.services.ecs import Cluster

        clusters: list[Cluster] = []
        if not self.detail.responseElements.tasks:
            return clusters
        for task in self.detail.responseElements.tasks:
            clusters.append(  # noqa: PERF401
                Cluster.objects.using(self.session).get(cluster=task.clusterArn)
            )
        return clusters

    @property
    def task_definitions(self) -> list["TaskDefinition"]:
        """
        Get the task definition name from the event.
        """
        from botocraft.services.ecs import TaskDefinition

        task_definitions: list[TaskDefinition] = []
        if not self.detail.responseElements.tasks:
            return task_definitions
        for task in self.detail.responseElements.tasks:
            task_definitions.append(  # noqa: PERF401
                TaskDefinition.objects.using(self.session).get(
                    taskDefinition=task.taskDefinitionArn
                )
            )
        return task_definitions

    @property
    def tasks(self) -> list["Task"]:
        """
        Get the task ARN from the event.
        """
        from botocraft.services.ecs import Task

        tasks: list[Task] = []
        if not self.detail.responseElements.tasks:
            return tasks
        for task in self.detail.responseElements.tasks:
            tasks.append(  # noqa: PERF401
                Task.objects.using(self.session).get(
                    task=task.taskArn, cluster=task.clusterArn
                )
            )
        return tasks

    @property
    def container_instances(self) -> list["ContainerInstance"]:
        """
        Get the container instance ARN from the event.
        """
        from botocraft.services.ecs import ContainerInstance

        container_instances: list[ContainerInstance] = []
        if not self.detail.responseElements.tasks:
            return container_instances
        for task in self.detail.responseElements.tasks:
            if task.containerInstanceArn:
                container_instances.append(  # noqa: PERF401
                    ContainerInstance.objects.using(self.session).get(
                        containerInstance=task.containerInstanceArn,
                        cluster=task.clusterArn,
                    )
                )
        return container_instances
