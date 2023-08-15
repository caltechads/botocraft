from typing import List, Literal, Optional, cast

import boto3
from botocraft.models import (
    Boto3Model,
    InferenceAccelerator,
    Volume,
    TaskDefinitionPlacementConstraint,
    ServiceRegistry,
    NetworkConfiguration,
    ClusterServiceConnectDefaultsRequest,
    DeploymentConfiguration,
    LoadBalancer,
    ContainerDefinition,
    PlacementConstraint,
    CapacityProviderStrategyItem,
    ServiceConnectConfiguration,
    RuntimePlatform,
    ClusterSetting,
    EphemeralStorage,
    PlacementStrategy,
    Service,
    DeploymentController,
    Cluster,
    ProxyConfiguration,
    ClusterConfiguration,
    TaskDefinition,
    Tag,
)


class CreateServiceResponse(Boto3Model):
    #: The full description of your service following the create call.
    service: Optional[Service] = None


class DeleteServiceResponse(Boto3Model):
    #: The full description of the deleted service.
    service: Optional[Service] = None


class Failure(Boto3Model):
    """
    A failed resource.

    For a list of common causes, see `API failure reasons <https
    ://docs.aws.amazon.com/AmazonECS/latest/developerguide/api_failures_messages.ht
    ml>`_ in the *Amazon Elastic Container Service Developer Guide*.
    """

    #: The Amazon Resource Name (ARN) of the failed resource.
    arn: Optional[str] = None
    #: The reason for the failure.
    reason: Optional[str] = None
    #: The details of the failure.
    detail: Optional[str] = None


class DescribeServicesResponse(Boto3Model):
    #: The list of services described.
    services: Optional[List[Service]] = None
    #: Any failures associated with the call.
    failures: Optional[List[Failure]] = None


class ListServicesResponse(Boto3Model):
    #: The list of full ARN entries for each service that's associated with the
    #: specified cluster.
    serviceArns: Optional[List[str]] = None
    #: The ``nextToken`` value to include in a future ``ListServices`` request. When
    #: the results of a ``ListServices`` request exceed ``maxResults``, this value can
    #: be used to retrieve the next page of results. This value is ``null`` when there
    #: are no more results to return.
    nextToken: Optional[str] = None


class UpdateServiceResponse(Boto3Model):
    #: The full description of your service following the update call.
    service: Optional[Service] = None


class CreateClusterResponse(Boto3Model):
    #: The full description of your new cluster.
    cluster: Optional[Cluster] = None


class DeleteClusterResponse(Boto3Model):
    #: The full description of the deleted cluster.
    cluster: Optional[Cluster] = None


class DescribeClustersResponse(Boto3Model):
    #: The list of clusters.
    clusters: Optional[List[Cluster]] = None
    #: Any failures associated with the call.
    failures: Optional[List[Failure]] = None


class ListClustersResponse(Boto3Model):
    #: The list of full Amazon Resource Name (ARN) entries for each cluster that's
    #: associated with your account.
    clusterArns: Optional[List[str]] = None
    #: The ``nextToken`` value to include in a future ``ListClusters`` request. When
    #: the results of a ``ListClusters`` request exceed ``maxResults``, this value can
    #: be used to retrieve the next page of results. This value is ``null`` when there
    #: are no more results to return.
    nextToken: Optional[str] = None


class UpdateClusterResponse(Boto3Model):
    #: Details about the cluster.
    cluster: Optional[Cluster] = None


class RegisterTaskDefinitionResponse(Boto3Model):
    #: The full description of the registered task definition.
    taskDefinition: Optional[TaskDefinition] = None
    #: The list of tags associated with the task definition.
    tags: Optional[List[Tag]] = None


class DeregisterTaskDefinitionResponse(Boto3Model):
    #: The full description of the deregistered task.
    taskDefinition: Optional[TaskDefinition] = None


class DescribeTaskDefinitionResponse(Boto3Model):
    #: The full task definition description.
    taskDefinition: Optional[TaskDefinition] = None
    #: The metadata that's applied to the task definition to help you categorize and
    #: organize them. Each tag consists of a key and an optional value. You define
    #: both.
    tags: Optional[List[Tag]] = None


class ListTaskDefinitionsResponse(Boto3Model):
    #: The list of task definition Amazon Resource Name (ARN) entries for the
    #: ``ListTaskDefinitions`` request.
    taskDefinitionArns: Optional[List[str]] = None
    #: The ``nextToken`` value to include in a future ``ListTaskDefinitions`` request.
    #: When the results of a ``ListTaskDefinitions`` request exceed ``maxResults``,
    #: this value can be used to retrieve the next page of results. This value is
    #: ``null`` when there are no more results to return.
    nextToken: Optional[str] = None


class ServiceManager:
    service_name: str = "ecs"

    def __init__(self) -> None:
        #: The boto3 client for the AWS service
        self.client = boto3.client(self.service_name)  # type: ignore

    def create(
        self,
        model: Service,
        clientToken: str = None,
        serviceConnectConfiguration: ServiceConnectConfiguration = None,
    ) -> Service:
        """
        Runs and maintains your desired number of tasks from a specified task
        definition. If the number of tasks running in a service drops below the
        ``desiredCount``, Amazon ECS runs another copy of the task in the
        specified cluster. To update an existing service, see the UpdateService
        action.

        Starting April 15, 2023, Amazon Web Services will not onboard new customers to
        Amazon Elastic Inference (EI), and will help current customers migrate their
        workloads to options that offer better price and performance. After April 15,
        2023, new customers will not be able to launch instances with Amazon EI
        accelerators in Amazon SageMaker, Amazon ECS, or Amazon EC2. However, customers
        who have used Amazon EI at least once during the past 30-day period are
        considered current customers and will be able to continue using the service.

        In addition to maintaining the desired count of tasks in your service, you can
        optionally run your service behind one or more load balancers. The load
        balancers distribute traffic across the tasks that are associated with the
        service. For more information, see `Service load
        balancing <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-
        load-balancing.html>`_ in the *Amazon Elastic Container Service Developer Guide*.

        Tasks for services that don't use a load balancer are considered healthy if
        they're in the ``RUNNING`` state. Tasks for services that use a load balancer
        are considered healthy if they're in the ``RUNNING`` state and are reported as
        healthy by the load balancer.

        There are two service scheduler strategies available:

        * ``REPLICA`` - The replica scheduling strategy places and maintains your
          desired number of tasks across your cluster. By default, the service scheduler
          spreads tasks across Availability Zones. You can use task placement strategies
          and constraints to customize task placement decisions. For more information,
          see `Service scheduler concepts <https://docs.aws.amazon.com/AmazonECS/latest/d
        eveloperguide/ecs_services.html>`_ in the *Amazon Elastic Container Service
          Developer Guide*.
        * ``DAEMON`` - The daemon scheduling strategy deploys exactly one task on each
          active container instance that meets all of the task placement constraints that
          you specify in your cluster. The service scheduler also evaluates the task
          placement constraints for running tasks. It also stops tasks that don't meet
          the placement constraints. When using this strategy, you don't need to specify
          a desired number of tasks, a task placement strategy, or use Service Auto
          Scaling policies. For more information, see `Service scheduler concepts <https:
        //docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html>`_ in the
          *Amazon Elastic Container Service Developer Guide*.

        You can optionally specify a deployment configuration for your service. The
        deployment is initiated by changing properties. For example, the deployment
        might be initiated by the task definition or by your desired count of a
        service. This is done with an UpdateService operation. The default value for a
        replica service for ``minimumHealthyPercent`` is 100%. The default value for a
        daemon service for ``minimumHealthyPercent`` is 0%.

        If a service uses the ``ECS`` deployment controller, the minimum healthy
        percent represents a lower limit on the number of tasks in a service that must
        remain in the ``RUNNING`` state during a deployment. Specifically, it
        represents it as a percentage of your desired number of tasks (rounded up to
        the nearest integer). This happens when any of your container instances are in
        the ``DRAINING`` state if the service contains tasks using the EC2 launch type.
        Using this parameter, you can deploy without using additional cluster capacity.
        For example, if you set your service to have desired number of four tasks and a
        minimum healthy percent of 50%, the scheduler might stop two existing tasks to
        free up cluster capacity before starting two new tasks. If they're in the
        ``RUNNING`` state, tasks for services that don't use a load balancer are
        considered healthy . If they're in the ``RUNNING`` state and reported as
        healthy by the load balancer, tasks for services that *do* use a load balancer
        are considered healthy . The default value for minimum healthy percent is 100%.

        If a service uses the ``ECS`` deployment controller, the **maximum percent**
        parameter represents an upper limit on the number of tasks in a service that
        are allowed in the ``RUNNING`` or ``PENDING`` state during a deployment.
        Specifically, it represents it as a percentage of the desired number of tasks
        (rounded down to the nearest integer). This happens when any of your container
        instances are in the ``DRAINING`` state if the service contains tasks using the
        EC2 launch type. Using this parameter, you can define the deployment batch
        size. For example, if your service has a desired number of four tasks and a
        maximum percent value of 200%, the scheduler may start four new tasks before
        stopping the four older tasks (provided that the cluster resources required to
        do this are available). The default value for maximum percent is 200%.

        If a service uses either the ``CODE_DEPLOY`` or ``EXTERNAL`` deployment
        controller types and tasks that use the EC2 launch type, the **minimum healthy
        percent** and **maximum percent** values are used only to define the lower and
        upper limit on the number of the tasks in the service that remain in the
        ``RUNNING`` state. This is while the container instances are in the
        ``DRAINING`` state. If the tasks in the service use the Fargate launch type,
        the minimum healthy percent and maximum percent values aren't used. This is the
        case even if they're currently visible when describing your service.

        When creating a service that uses the ``EXTERNAL`` deployment controller, you
        can specify only parameters that aren't controlled at the task set level. The
        only required parameter is the service name. You control your services using
        the CreateTaskSet operation. For more information, see `Amazon ECS deployment
        types <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-
        types.html>`_ in the *Amazon Elastic Container Service Developer Guide*.

        When the service scheduler launches new tasks, it determines task placement.
        For information about task placement and task placement strategies, see `Amazon
        ECS task
        placement <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-
        placement.html>`_ in the *Amazon Elastic Container Service Developer Guide*.



                Args:
                    serviceName: str

                Returns:
                    Service
        """
        data = model.model_dump()
        _response = self.client.create_service(
            serviceName=data["serviceName"],
            cluster=data["clusterArn"],
            taskDefinition=data["taskDefinition"],
            loadBalancers=data["loadBalancers"],
            serviceRegistries=data["serviceRegistries"],
            desiredCount=data["desiredCount"],
            clientToken=clientToken,
            launchType=data["launchType"],
            capacityProviderStrategy=data["capacityProviderStrategy"],
            platformVersion=data["platformVersion"],
            role=data["roleArn"],
            deploymentConfiguration=data["deploymentConfiguration"],
            placementConstraints=data["placementConstraints"],
            placementStrategy=data["placementStrategy"],
            networkConfiguration=data["networkConfiguration"],
            healthCheckGracePeriodSeconds=data["healthCheckGracePeriodSeconds"],
            schedulingStrategy=data["schedulingStrategy"],
            deploymentController=data["deploymentController"],
            tags=data["tags"],
            enableECSManagedTags=data["enableECSManagedTags"],
            propagateTags=data["propagateTags"],
            enableExecuteCommand=data["enableExecuteCommand"],
            serviceConnectConfiguration=serviceConnectConfiguration,
        )
        response = CreateServiceResponse(**_response)
        return cast(Service, response.service)

    def delete(
        self, service: str, *, cluster: str = None, force: bool = None
    ) -> Service:
        """
        Deletes a specified service within a cluster. You can delete a service
        if you have no running tasks in it and the desired task count is zero.
        If the service is actively maintaining tasks, you can't delete it, and
        you must update the service to a desired task count of zero. For more
        information, see UpdateService.

        When you delete a service, if there are still running tasks that require
        cleanup, the service status moves from ``ACTIVE`` to ``DRAINING``, and the
        service is no longer visible in the console or in the ListServices API
        operation. After all tasks have transitioned to either ``STOPPING`` or
        ``STOPPED`` status, the service status moves from ``DRAINING`` to ``INACTIVE``.
        Services in the ``DRAINING`` or ``INACTIVE`` status can still be viewed with
        the DescribeServices API operation. However, in the future, ``INACTIVE``
        services may be cleaned up and purged from Amazon ECS record keeping, and
        DescribeServices calls on those services return a ``ServiceNotFoundException``
        error.

        If you attempt to create a new service with the same name as an existing
        service in either ``ACTIVE`` or ``DRAINING`` status, you receive an error.



                Args:
                    service: str

                Returns:
                    Service
        """
        _response = self.client.delete_service(
            service=service, cluster=cluster, force=force
        )
        response = DeleteServiceResponse(**_response)
        return cast(Service, response.service)

    def get(
        self,
        service: str,
        *,
        cluster: str = None,
        include: List[Literal["TAGS"]] = None
    ) -> Optional[Service]:
        """
        Describes the specified services running in your cluster.

        Args:
            service: str

        Returns:
            Optional[Service]
        """
        _response = self.client.describe_services(
            services=[service], cluster=cluster, include=include
        )
        response = DescribeServicesResponse(**_response)
        if response.services:
            return response.services[0]  # type: ignore # pylint: disable=unsubscriptable-object
        return None

    def list(
        self,
        *,
        cluster: str = None,
        nextToken: str = None,
        maxResults: int = None,
        launchType: Literal["EC2", "FARGATE", "EXTERNAL"] = None,
        schedulingStrategy: Literal["REPLICA", "DAEMON"] = None
    ) -> List[Service]:
        """
        Returns a list of services. You can filter the results by cluster,
        launch type, and scheduling strategy.

        Returns:
            List[Service]
        """
        _response = self.client.list_services(
            cluster=cluster,
            nextToken=nextToken,
            maxResults=maxResults,
            launchType=launchType,
            schedulingStrategy=schedulingStrategy,
        )
        response = ListServicesResponse(**_response)
        return response.serviceArns

    def update(
        self,
        model: Service,
        forceNewDeployment: bool = None,
        serviceConnectConfiguration: ServiceConnectConfiguration = None,
    ) -> Service:
        """
        Modifies the parameters of a service.

        For services using the rolling update (``ECS``) you can update the desired
        count, deployment configuration, network configuration, load balancers, service
        registries, enable ECS managed tags option, propagate tags option, task
        placement constraints and strategies, and task definition. When you update any
        of these parameters, Amazon ECS starts new tasks with the new configuration.

        For services using the blue/green (``CODE_DEPLOY``) deployment controller, only
        the desired count, deployment configuration, health check grace period, task
        placement constraints and strategies, enable ECS managed tags option, and
        propagate tags can be updated using this API. If the network configuration,
        platform version, task definition, or load balancer need to be updated, create
        a new CodeDeploy deployment. For more information, see `CreateDeployment <https
        ://docs.aws.amazon.com/codedeploy/latest/APIReference/API_CreateDeployment.html
        >`_ in the *CodeDeploy API Reference*.

        For services using an external deployment controller, you can update only the
        desired count, task placement constraints and strategies, health check grace
        period, enable ECS managed tags option, and propagate tags option, using this
        API. If the launch type, load balancer, network configuration, platform
        version, or task definition need to be updated, create a new task set For more
        information, see CreateTaskSet.

        You can add to or subtract from the number of instantiations of a task
        definition in a service by specifying the cluster that the service is running
        in and a new ``desiredCount`` parameter.

        If you have updated the Docker image of your application, you can create a new
        task definition with that image and deploy it to your service. The service
        scheduler uses the minimum healthy percent and maximum percent parameters (in
        the service's deployment configuration) to determine the deployment strategy.

        If your updated Docker image uses the same tag as what is in the existing task
        definition for your service (for example, ``my_image:latest``), you don't need
        to create a new revision of your task definition. You can update the service
        using the ``forceNewDeployment`` option. The new tasks launched by the
        deployment pull the current image/tag combination from your repository when
        they start.

        You can also update the deployment configuration of a service. When a
        deployment is triggered by updating the task definition of a service, the
        service scheduler uses the deployment configuration parameters,
        ``minimumHealthyPercent`` and ``maximumPercent``, to determine the deployment
        strategy.

        * If ``minimumHealthyPercent`` is below 100%, the scheduler can ignore
          ``desiredCount`` temporarily during a deployment. For example, if
          ``desiredCount`` is four tasks, a minimum of 50% allows the scheduler to stop
          two existing tasks before starting two new tasks. Tasks for services that don't
          use a load balancer are considered healthy if they're in the ``RUNNING`` state.
          Tasks for services that use a load balancer are considered healthy if they're
          in the ``RUNNING`` state and are reported as healthy by the load balancer.
        * The ``maximumPercent`` parameter represents an upper limit on the number of
          running tasks during a deployment. You can use it to define the deployment
          batch size. For example, if ``desiredCount`` is four tasks, a maximum of 200%
          starts four new tasks before stopping the four older tasks (provided that the
          cluster resources required to do this are available).

        When UpdateService stops a task during a deployment, the equivalent of ``docker
        stop`` is issued to the containers running in the task. This results in a
        ``SIGTERM`` and a 30-second timeout. After this, ``SIGKILL`` is sent and the
        containers are forcibly stopped. If the container handles the ``SIGTERM``
        gracefully and exits within 30 seconds from receiving it, no ``SIGKILL`` is
        sent.

        When the service scheduler launches new tasks, it determines task placement in
        your cluster with the following logic.

        * Determine which of the container instances in your cluster can support your
          service's task definition. For example, they have the required CPU, memory,
          ports, and container instance attributes.
        * By default, the service scheduler attempts to balance tasks across
          Availability Zones in this manner even though you can choose a different
          placement strategy.


        + Sort the valid container instances by the fewest number of running tasks for
        this service in the same Availability Zone as the instance. For example, if
        zone A has one running service task and zones B and C each have zero, valid
        container instances in either zone B or C are considered optimal for placement.
        + Place the new service task on a valid container instance in an optimal
        Availability Zone (based on the previous steps), favoring container instances
        with the fewest number of running tasks for this service.

        When the service scheduler stops running tasks, it attempts to maintain balance
        across the Availability Zones in your cluster using the following logic:

        * Sort the container instances by the largest number of running tasks for this
          service in the same Availability Zone as the instance. For example, if zone A
          has one running service task and zones B and C each have two, container
          instances in either zone B or C are considered optimal for termination.
        * Stop the task on a container instance in an optimal Availability Zone (based
          on the previous steps), favoring container instances with the largest number of
          running tasks for this service.

        You must have a service-linked role when you update any of the following
        service properties:

        * ``loadBalancers``,
        * ``serviceRegistries``

        For more information about the role see the ``CreateService`` request parameter
        ```role`` <https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Create
        Service.html#ECS-CreateService-request-role>`_ .



                Args:
                    service: str

                Returns:
                    Service
        """
        data = model.model_dump()
        _response = self.client.update_service(
            service=data["serviceName"],
            cluster=data["clusterArn"],
            desiredCount=data["desiredCount"],
            taskDefinition=data["taskDefinition"],
            capacityProviderStrategy=data["capacityProviderStrategy"],
            deploymentConfiguration=data["deploymentConfiguration"],
            networkConfiguration=data["networkConfiguration"],
            placementConstraints=data["placementConstraints"],
            placementStrategy=data["placementStrategy"],
            platformVersion=data["platformVersion"],
            forceNewDeployment=forceNewDeployment,
            healthCheckGracePeriodSeconds=data["healthCheckGracePeriodSeconds"],
            enableExecuteCommand=data["enableExecuteCommand"],
            enableECSManagedTags=data["enableECSManagedTags"],
            loadBalancers=data["loadBalancers"],
            propagateTags=data["propagateTags"],
            serviceRegistries=data["serviceRegistries"],
            serviceConnectConfiguration=serviceConnectConfiguration,
        )
        response = UpdateServiceResponse(**_response)
        return cast(Service, response.service)


class ClusterManager:
    service_name: str = "ecs"

    def __init__(self) -> None:
        #: The boto3 client for the AWS service
        self.client = boto3.client(self.service_name)  # type: ignore

    def create(self, model: Cluster) -> Cluster:
        """
        Creates a new Amazon ECS cluster. By default, your account receives a
        ``default`` cluster when you launch your first container instance.
        However, you can create your own cluster with a unique name with the
        ``CreateCluster`` action.

        When you call the CreateCluster API operation, Amazon ECS attempts to create
        the Amazon ECS service-linked role for your account. This is so that it can
        manage required resources in other Amazon Web Services services on your behalf.
        However, if the user that makes the call doesn't have permissions to create the
        service-linked role, it isn't created. For more information, see `Using
        service-linked roles for Amazon
        ECS <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using-service-
        linked-roles.html>`_ in the *Amazon Elastic Container Service Developer Guide*.



                Returns:
                    Cluster
        """
        data = model.model_dump()
        _response = self.client.create_cluster(
            clusterName=data["clusterName"],
            tags=data["tags"],
            settings=data["settings"],
            configuration=data["configuration"],
            capacityProviders=data["capacityProviders"],
            defaultCapacityProviderStrategy=data["defaultCapacityProviderStrategy"],
            serviceConnectDefaults=data["serviceConnectDefaults"],
        )
        response = CreateClusterResponse(**_response)
        return cast(Cluster, response.cluster)

    def delete(self, cluster: str) -> Cluster:
        """
        Deletes the specified cluster. The cluster transitions to the
        ``INACTIVE`` state. Clusters with an ``INACTIVE`` status might remain
        discoverable in your account for a period of time. However, this
        behavior is subject to change in the future. We don't recommend that
        you rely on ``INACTIVE`` clusters persisting.

        You must deregister all container instances from this cluster before you may
        delete it. You can list the container instances in a cluster with
        ListContainerInstances and deregister them with DeregisterContainerInstance.



                Args:
                    cluster: str

                Returns:
                    Cluster
        """
        _response = self.client.delete_cluster(cluster=cluster)
        response = DeleteClusterResponse(**_response)
        return cast(Cluster, response.cluster)

    def get(
        self,
        *,
        clusters: List[str] = None,
        include: List[
            Literal["ATTACHMENTS", "CONFIGURATIONS", "SETTINGS", "STATISTICS", "TAGS"]
        ] = None
    ) -> Optional[Cluster]:
        """
        Describes one or more of your clusters.

        Returns:
            Optional[Cluster]
        """
        _response = self.client.describe_clusters(clusters=clusters, include=include)
        response = DescribeClustersResponse(**_response)
        if response.clusters:
            return response.clusters[0]  # type: ignore # pylint: disable=unsubscriptable-object
        return None

    def list(self, *, nextToken: str = None, maxResults: int = None) -> List[Cluster]:
        """
        Returns a list of existing clusters.

        Returns:
            List[Cluster]
        """
        _response = self.client.list_clusters(
            nextToken=nextToken, maxResults=maxResults
        )
        response = ListClustersResponse(**_response)
        return response.clusterArns

    def update(self, model: Cluster) -> Cluster:
        """
        Updates the cluster.

        Args:
            cluster: str

        Returns:
            Cluster
        """
        data = model.model_dump()
        _response = self.client.update_cluster(
            cluster=data["clusterName"],
            settings=data["settings"],
            configuration=data["configuration"],
            serviceConnectDefaults=data["serviceConnectDefaults"],
        )
        response = UpdateClusterResponse(**_response)
        return cast(Cluster, response.cluster)


class TaskDefinitionManager:
    service_name: str = "ecs"

    def __init__(self) -> None:
        #: The boto3 client for the AWS service
        self.client = boto3.client(self.service_name)  # type: ignore

    def create(self, model: TaskDefinition) -> TaskDefinition:
        """
                Registers a new task definition from the supplied ``family`` and
        ``containerDefinitions``. Optionally, you can add data volumes to your
        containers with the ``volumes`` parameter. For more information about task
        definition parameters and defaults, see `Amazon ECS Task Definitions <https://d
        ocs.aws.amazon.com/AmazonECS/latest/developerguide/task_defintions.html>`_ in the
        *Amazon Elastic Container Service Developer Guide*.

        You can specify a role for your task with the ``taskRoleArn`` parameter. When
        you specify a role for a task, its containers can then use the latest versions
        of the CLI or SDKs to make API requests to the Amazon Web Services services
        that are specified in the policy that's associated with the role. For more
        information, see `IAM Roles for
        Tasks <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-
        roles.html>`_ in the *Amazon Elastic Container Service Developer Guide*.

        You can specify a Docker networking mode for the containers in your task
        definition with the ``networkMode`` parameter. The available network modes
        correspond to those described in `Network
        settings <https://docs.docker.com/engine/reference/run/#/network-settings>`_ in
        the Docker run reference. If you specify the ``awsvpc`` network mode, the task
        is allocated an elastic network interface, and you must specify a
        NetworkConfiguration when you create a service or run a task with the task
        definition. For more information, see `Task
        Networking <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-
        networking.html>`_ in the *Amazon Elastic Container Service Developer Guide*.



                Args:
                    family: str
                    containerDefinitions: List[ContainerDefinition]

                Returns:
                    TaskDefinition
        """
        data = model.model_dump()
        _response = self.client.register_task_definition(
            family=data["family"],
            containerDefinitions=data["containerDefinitions"],
            taskRoleArn=data["taskRoleArn"],
            executionRoleArn=data["executionRoleArn"],
            networkMode=data["networkMode"],
            volumes=data["volumes"],
            placementConstraints=data["placementConstraints"],
            requiresCompatibilities=data["requiresCompatibilities"],
            cpu=data["cpu"],
            memory=data["memory"],
            tags=data["tags"],
            pidMode=data["pidMode"],
            ipcMode=data["ipcMode"],
            proxyConfiguration=data["proxyConfiguration"],
            inferenceAccelerators=data["inferenceAccelerators"],
            ephemeralStorage=data["ephemeralStorage"],
            runtimePlatform=data["runtimePlatform"],
        )
        response = RegisterTaskDefinitionResponse(**_response)
        return cast(TaskDefinition, response.taskdefinition)

    def delete(self, taskDefinition: str) -> TaskDefinition:
        """
        Deregisters the specified task definition by family and revision. Upon
        deregistration, the task definition is marked as ``INACTIVE``. Existing
        tasks and services that reference an ``INACTIVE`` task definition
        continue to run without disruption. Existing services that reference an
        ``INACTIVE`` task definition can still scale up or down by modifying
        the service's desired count. If you want to delete a task definition
        revision, you must first deregister the task definition revision.

        You can't use an ``INACTIVE`` task definition to run new tasks or create new
        services, and you can't update an existing service to reference an ``INACTIVE``
        task definition. However, there may be up to a 10-minute window following
        deregistration where these restrictions have not yet taken effect.

        At this time, ``INACTIVE`` task definitions remain discoverable in your account
        indefinitely. However, this behavior is subject to change in the future. We
        don't recommend that you rely on ``INACTIVE`` task definitions persisting
        beyond the lifecycle of any associated tasks and services.

        You must deregister a task definition revision before you delete it. For more
        information, see `DeleteTaskDefinitions <https://docs.aws.amazon.com/AmazonECS/
        latest/APIReference/API_DeleteTaskDefinitions.html>`_.



                Args:
                    taskDefinition: str

                Returns:
                    TaskDefinition
        """
        _response = self.client.deregister_task_definition(
            taskDefinition=taskDefinition
        )
        response = DeregisterTaskDefinitionResponse(**_response)
        return cast(TaskDefinition, response.taskdefinition)

    def get(
        self, taskDefinition: str, *, include: List[Literal["TAGS"]] = None
    ) -> Optional[TaskDefinition]:
        """
        Describes a task definition. You can specify a ``family`` and
        ``revision`` to find information about a specific task definition, or
        you can simply specify the family to find the latest ``ACTIVE``
        revision in that family.

        You can only describe ``INACTIVE`` task definitions while an active task or
        service references them.



                Args:
                    taskDefinition: str

                Returns:
                    Optional[TaskDefinition]
        """
        _response = self.client.describe_task_definition(
            taskDefinition=taskDefinition, include=include
        )
        response = DescribeTaskDefinitionResponse(**_response)
        if response.taskdefinitions:
            return response.taskdefinitions[0]  # type: ignore # pylint: disable=unsubscriptable-object
        return None

    def list(
        self,
        *,
        familyPrefix: str = None,
        status: Literal["ACTIVE", "INACTIVE", "DELETE_IN_PROGRESS"] = None,
        sort: Literal["ASC", "DESC"] = None,
        nextToken: str = None,
        maxResults: int = None
    ) -> List[TaskDefinition]:
        """
        Returns a list of task definitions that are registered to your account.
        You can filter the results by family name with the ``familyPrefix``
        parameter or by status with the ``status`` parameter.

        Returns:
            List[TaskDefinition]
        """
        _response = self.client.list_task_definitions(
            familyPrefix=familyPrefix,
            status=status,
            sort=sort,
            nextToken=nextToken,
            maxResults=maxResults,
        )
        response = ListTaskDefinitionsResponse(**_response)
        return response.taskdefinitions

    def update(self, model: TaskDefinition) -> TaskDefinition:
        """
                Registers a new task definition from the supplied ``family`` and
        ``containerDefinitions``. Optionally, you can add data volumes to your
        containers with the ``volumes`` parameter. For more information about task
        definition parameters and defaults, see `Amazon ECS Task Definitions <https://d
        ocs.aws.amazon.com/AmazonECS/latest/developerguide/task_defintions.html>`_ in the
        *Amazon Elastic Container Service Developer Guide*.

        You can specify a role for your task with the ``taskRoleArn`` parameter. When
        you specify a role for a task, its containers can then use the latest versions
        of the CLI or SDKs to make API requests to the Amazon Web Services services
        that are specified in the policy that's associated with the role. For more
        information, see `IAM Roles for
        Tasks <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-
        roles.html>`_ in the *Amazon Elastic Container Service Developer Guide*.

        You can specify a Docker networking mode for the containers in your task
        definition with the ``networkMode`` parameter. The available network modes
        correspond to those described in `Network
        settings <https://docs.docker.com/engine/reference/run/#/network-settings>`_ in
        the Docker run reference. If you specify the ``awsvpc`` network mode, the task
        is allocated an elastic network interface, and you must specify a
        NetworkConfiguration when you create a service or run a task with the task
        definition. For more information, see `Task
        Networking <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-
        networking.html>`_ in the *Amazon Elastic Container Service Developer Guide*.



                Args:
                    family: str
                    containerDefinitions: List[ContainerDefinition]

                Returns:
                    TaskDefinition
        """
        data = model.model_dump()
        _response = self.client.register_task_definition(
            family=data["family"],
            containerDefinitions=data["containerDefinitions"],
            taskRoleArn=data["taskRoleArn"],
            executionRoleArn=data["executionRoleArn"],
            networkMode=data["networkMode"],
            volumes=data["volumes"],
            placementConstraints=data["placementConstraints"],
            requiresCompatibilities=data["requiresCompatibilities"],
            cpu=data["cpu"],
            memory=data["memory"],
            tags=data["tags"],
            pidMode=data["pidMode"],
            ipcMode=data["ipcMode"],
            proxyConfiguration=data["proxyConfiguration"],
            inferenceAccelerators=data["inferenceAccelerators"],
            ephemeralStorage=data["ephemeralStorage"],
            runtimePlatform=data["runtimePlatform"],
        )
        response = RegisterTaskDefinitionResponse(**_response)
        return cast(TaskDefinition, response.taskdefinition)
