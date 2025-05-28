# mypy: disable-error-code="attr-defined"
import re
import warnings
from functools import cached_property, wraps
from typing import TYPE_CHECKING, Callable, Dict, List, Literal, Optional, Set, cast

import click

if TYPE_CHECKING:
    from botocraft.services import (
        Cluster,
        ContainerInstance,
        LoadBalancer,
        Service,
        ServiceDeploymentBrief,
        Task,
        TaskDefinition,
        TaskManager,
    )
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet  # noqa: TC004


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
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

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
    func: Callable[..., List[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.ecs.ClusterManager.list` to return a list
    of :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.ecs.Cluster` objects instead of only a list of
    ARNs.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

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


def ecs_task_definitions_only(
    func: Callable[..., List[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a list of ECS task definition identifiers to a list of
    :py:class:`botocraft.services.ecs.TaskDefinition` objects.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        identifiers = func(self, *args, **kwargs)
        tds = [self.get(identifier, include=["TAGS"]) for identifier in identifiers]
        return PrimaryBoto3ModelQuerySet(tds)

    return wrapper


# ContainerInstance


def ecs_container_instances_only(
    func: Callable[..., List[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a list of ECS container instance arns to a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.ecs.ContainerInstance` objects.
    """

    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

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
    func: Callable[..., List[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a list of ECS container instance arns to a list of
    :py:class:`botocraft.services.ecs.ContainerInstance` objects.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
        from botocraft.services.ecs import Task

        arns = func(self, *args, **kwargs)
        tasks = []
        for i in range(0, len(arns), 100):
            tasks.extend(cast("TaskManager", Task.objects).get_many(arns[i : i + 100]))
        return PrimaryBoto3ModelQuerySet(tasks)  # type: ignore[arg-type]

    return wrapper


def ecs_service_deployments_only(
    func: Callable[..., List["ServiceDeploymentBrief"]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a list of service deployment arns to a list of
    :py:class:`botocraft.services.ecs.Deployment` objects.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.ecs import ServiceDeployment, ServiceDeploymentManager

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

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Optional["Task"]:
        task = func(self, *args, **kwargs)
        if task:
            task.taskDefinition = extract_task_family_and_revision(
                task.taskDefinitionArn
            )
        return task

    return wrapper


def ecs_task_populate_taskDefinitions(
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

    @wraps(func)
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

    @wraps(func)
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
    def load_balancers(self) -> List["LoadBalancer"]:
        """
        Return the :py:class:`LoadBalancer` objects that are associated with the
        service.
        """
        from botocraft.services import LoadBalancer

        arns: Set[str] = set()
        for tg in self.target_groups:  # type: ignore[attr-defined]
            for arn in tg.LoadBalancerArns:
                arns.add(arn)
        if arns:
            return LoadBalancer.objects.using(self.session).list(
                LoadBalancerArns=list(arns)
            )
        return []


class ECSServiceManagerMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.ServiceManager` that adds
    some additional methods that we can't auto generate.
    """

    def all(
        self,
        launchType: Literal["EC2", "FARGATE", "EXTERNAL"] | None = None,  # noqa: N803
        schedulingStrategy: Literal["REPLICA", "DAEMON"] | None = None,  # noqa: N803
        tags: Dict[str, str] | None = None,
    ) -> List["Service"]:
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
        services: List["Service"] = []  # noqa: UP037
        for cluster in clusters:
            if tags.items() <= cluster.tags.items():
                services.extend(
                    Service.objects.using(self.session).list(
                        cluster=cluster.clusterArn,
                        launchType=launchType,
                        schedulingStrategy=schedulingStrategy,
                    )
                )
        return services


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
        tags: Dict[str, str] | None = None,
        verbose: bool = False,
    ) -> List["TaskDefinition"]:
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
        from botocraft.services import EventRule, Service, TaskDefinition

        if not tags:
            tags = {}

        task_definitions: Dict[str, TaskDefinition] = {}

        click.secho("Getting all services ...", fg="green")
        # First get all the services in the account
        services: List[Service] = Service.objects.using(self.session).all()
        ClientException = self.session.client("ecs").exceptions.ClientException  # noqa: N806

        if verbose:
            click.secho("Finding active Service task definitions ...", fg="green")
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

        if verbose:
            click.secho("Finding active periodic task definitions ...", fg="green")
        # Now deal with the periodc tasks
        rules = EventRule.objects.using(self.session).list()
        for rule in rules:
            for target in rule.targets:
                if target.EcsParameters is not None:
                    try:
                        task_definition = TaskDefinition.objects.using(
                            self.session
                        ).get(target.EcsParameters.taskDefinitionArn)
                    except ClientException:
                        warnings.warn(
                            f"Task definition {target.EcsParameters.taskDefinitionArn} "
                            f"used by {rule.name} does not exist",
                            UserWarning,
                            stacklevel=2,
                        )
                        continue
                    family_revision = task_definition.family_revision
                    if family_revision not in task_definitions:
                        task_definitions[family_revision] = task_definition
        return list(task_definitions.values())


class TaskDefinitionModelMixin:
    @property
    def family_revision(self) -> str:
        """
        Return the family and revision of the task definition in the format
        ``<family>:<revision>``.
        """
        return f"{self.family}:{self.revision}"

    @property
    def container_images(self) -> List[str]:
        """
        Return the container images as a list of strings.

        Returns:
            A list of container images.

        """
        return [container.image for container in self.containerDefinitions]  # type: ignore[attr-defined]

    @cached_property
    def services(self) -> List["Service"]:
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
        services: List[Service] = []
        for cluster in clusters:
            services.extend(
                service
                for service in cluster.services
                if service.taskDefinition == self.family_revision
            )
        return services


class ServiceDeploymentModelMixin:
    """
    A mixin for :py:class:`botocraft.services.ecs.ServiceDeployment` that adds
    some additional methods that we can't auto generate.
    """

    @property
    def source_task_definitions(self) -> List["TaskDefinition"]:
        """
        Return the task definition for the deployment.
        """
        from botocraft.services import TaskDefinition

        arns = [source.arn for source in self.sourceServiceRevisions]

        return [TaskDefinition.objects.using(self.session).get(arn) for arn in arns]
