# mypy: disable-error-code="attr-defined"

import base64
import datetime
import re
import warnings
from functools import cached_property, wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Literal,
    Optional,
    cast,
)

import click
import docker
from pydantic import BaseModel

if TYPE_CHECKING:
    from botocraft.services import (
        ECRImage,
        ECRImageManager,
        Finding,
        ImageIdentifier,
        Repository,
        RepositoryManager,
        Service,
        TaskDefinition,
    )
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet  # noqa: TC004


class ECRDockerClient(BaseModel):
    """
    A return type suitable for the docker client.

    We need to return a docker client that is logged into our ECR registry,
    along with the username, password, and registry, because you need the
    latter 3 to do any pulling or pushing of images.
    """

    #: The docker client.
    client: Any
    #: The username to use for the remote registry.
    username: str
    #: The password to use for the remote registry.
    password: str
    #: The registry
    registry: str


class ImageInfo(BaseModel):
    """
    A class to hold information about a :py:class:`botocraft.services.ecr.Image`
    that is not available from the boto3 library.  We extract this information
    by pulling the image from the repository and inspecting it with the docker
    Python library.

    Important:
        You must have the docker daemon running to use the methods that return
        this object.

    """

    # The image name, including the registry, repository, and tag.
    name: str
    #: The OS platform of the image
    platform: str
    #: The architecture of the image
    architecture: str
    #: Size of the image in bytes
    size: int
    #: This is a dictionary of port mappings.  The key is the port
    #: and the value is i'm not sure what
    ports: Dict[str, Dict[str, Any]] = {}
    #: Docker Version used to build the image
    docker_version: str
    #: The user that the image runs as
    user: str | None = None
    #: When the image was created, as a UTC datetime object
    created: datetime.datetime


# -----------
# Decorators
# -----------


def repo_list_images_ecr_images_only(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Convert a list of ECR image identifiers returned by
    :py:meth:`botocraft.services.ecr.RepositoryManager.list_images` into a list
    of :py:class:`botocraft.services.ecr.Image` objects.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        qs: "PrimaryBoto3ModelQuerySet" = func(self, *args, **kwargs)  # noqa: UP037
        images: List["ECRImage"] = []  # noqa: UP037
        # NOTE: to be honest i'm not sure if there is a per request limit
        # for the number of images that can be retrieved, but i'm going to
        # assume that there is a limit of 100 images per request.
        for i in range(0, len(qs.results), 100):
            _images = self.get_images(
                repositoryName=kwargs["repositoryName"],
                imageIds=qs.results[i : i + 100],
            )
            if _images:
                images.extend(_images)
        return PrimaryBoto3ModelQuerySet(images)  # type: ignore[arg-type]

    return wrapper


def repo_list_add_tags(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Add tags to all :py:class:`botocraft.services.ecr.Repository` objects returned
    by :py:meth:`botocraft.services.ecr.RepositoryManager.list`.  This has to
    be done in a separate call because the tags are not returned in the
    response from the get call.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        qs: PrimaryBoto3ModelQuerySet = func(self, *args, **kwargs)
        extras = kwargs.get("include", [])
        if "TAGS" in extras:
            for repo in qs.results:
                tags = self.get_tags(resourceArn=repo.arn)
                if tags:
                    repo.tags = tags
        return qs

    return wrapper


def repo_get_add_tags(
    func: Callable[..., Optional["Repository"]],
) -> Callable[..., Optional["Repository"]]:
    """
    Add tags to a :py:class:`botocraft.services.ecr.Repository` object returned
    by :py:meth:`botocraft.services.ecr.RepositoryManager.get`.  This has to
    be done in a separate call because the tags are not returned in the
    response from the get call.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Optional["Repository"]:
        repo = func(self, *args, **kwargs)
        if repo is None:
            return None
        extras = kwargs.get("include", [])
        if "TAGS" in extras:
            tags = self.get_tags(resourceArn=repo.arn)
            if tags:
                repo.tags = tags
        return repo

    return wrapper


def image_list_images_ecr_images_only(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Convert a list of ECR image identifiers returned by
    :py:meth:`botocraft.services.ecr.Image.list` into a list
    of :py:class:`botocraft.services.ecr.Image` objects.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        qs: PrimaryBoto3ModelQuerySet = func(self, *args, **kwargs)
        images: List["ECRImage"] = []  # noqa: UP037
        # NOTE: to be honest i'm not sure if there is a per request limit
        # for the number of images that can be retrieved, but i'm going to
        # assume that there is a limit of 100 images per request.
        for i in range(0, len(qs.results), 100):
            _images = self.get_many(
                repositoryName=args[0], imageIds=qs.results[i : i + 100]
            )
            if _images:
                images.extend(_images.images)
        return PrimaryBoto3ModelQuerySet(images)  # type: ignore[arg-type]

    return wrapper


# -------------
# Mixins
# -------------


class RepositoryMixin:
    objects: ClassVar["RepositoryManager"]

    # properties

    @property
    def images(self) -> List["ECRImage"] | None:
        """
        Get a list of images for a given repository.
        """
        return self.objects.using(self.session).list_images(
            repositoryName=self.repositoryName
        )  # type: ignore[attr-defined]

    # methods

    def get_image(self, imageId: "ImageIdentifier") -> Optional["ECRImage"]:  # noqa: N803
        """
        Get an image object for a given repository and image identifier.

        Args:
            imageId: The image ID or tag to describe. The format of the imageId
                reference is ``imageTag=tag`` or ``imageDigest=digest``

        """
        return self.objects.using(self.session).get_image(
            self.repositoryName,  # type: ignore[attr-defined]
            imageId=imageId,
        )


class ECRImageManagerMixin:
    @cached_property
    def account_id(self) -> str:
        """
        Get the account id for the current session.
        """
        from botocraft.services import CallerIdentity

        return CallerIdentity.objects.using(self.session).get().Account

    def __filter_image(
        self,
        image_id: str,
        repositoryNames: List[str] | None = None,  # noqa: N803
        repositoryPrefix: str | None = None,  # noqa: N803
        tags: Dict[str, str] | None = None,
    ) -> Optional["ECRImage"]:
        """
        Filter an image by repository name, prefix, or tags.   If no filters are
        provided, then the image is returned.

        Raises:
            LookupError: If the image is not found in this account, either because its
                from another account, it is a public-ecr image in this account,
                or it doesn't exist.

        Args:
            image_id: the image id of the image we want to examine
            repositoryNames: a list of repository names to filter by
            repositoryPrefix: a prefix to filter the repositories by
            tags: a dictionary of tags to filter the image by

        Returns:
            The :py:class:`botocraft.services.ecr.ECRImage` object if the image passes
            the filters, otherwise None.

        """
        from botocraft.services import ImageIdentifier

        if tags is None:
            tags = {}
        image: "ECRImage" | None = None  # noqa: UP037
        # See if this is even an ECR image
        if not image_id.startswith(self.account_id):
            if not re.match(r"\d{12}\.dkr\.ecr\..+\.amazonaws\.com", image_id):
                msg = f"Image {image_id} is from a different AWS account. Skipping."
                raise LookupError(msg)
            # TODO: we should also check our own public ECR repositories
            msg = f"Image {image_id} is not an ECR image. Skipping."
            raise LookupError(msg)

        # break image_id into its parts: repository_name, image_tag
        image_tag = image_id.split(":")[1]
        repository_name = image_id.split(".com/")[1].split(":")[0]
        _image = self.using(self.session).get(
            repository_name,
            imageId=ImageIdentifier(imageTag=image_tag),
        )
        if not _image:
            msg = f"Image {image_id} belongs to this AWS account, but does not exist."
            raise LookupError(msg)
        if repositoryNames or repositoryPrefix:
            if repositoryNames:
                if _image.repositoryName in repositoryNames:
                    image = _image
            if repositoryPrefix:
                if _image.repositoryName.startswith(repositoryPrefix):
                    image = _image
        elif tags:
            if tags.items() <= _image.repository.tags.items():
                image = _image
        return image

    def in_use(  # noqa: PLR0912
        self,
        repositoryNames: List[str] | None = None,  # noqa: N803
        repositoryPrefix: str | None = None,  # noqa: N803
        tags: Dict[str, str] | None = None,
        verbose: bool = False,
    ) -> List["ECRImage"]:
        """
        Return a list of :py:class:`botocraft.services.ECRImage` objects are
        currently in use by a service or periodic task.  A periodic task is a
        task that is run via a :py:class:`botocraft.services.events.EventRule`.

        Important:
            If you have tasks that are run ad-hoc, then this method will not
            return those task definitions.

        Keyword Args:
            repositoryNames: Look at only the repositories with these names.  This
                and ``repositoryPrefix`` are mutually exclusive.
            repositoryPrefix: A prefix to filter the repositories by.
            tags: A dictionary of tags to filter the task, services and periodic
                tasks by.
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

        assert not (repositoryNames and repositoryPrefix), (
            "You can't use both repositoryNames and repositoryPrefix at the same time."
        )

        if not tags:
            tags = {}

        # I'd like to use a set() here, but pydantic classes are not hashable
        # unless they are frozen, which ECRImage is not
        used_images: Dict[str, "ECRImage"] = {}  # noqa: UP037
        if verbose:
            click.secho("Getting all services ...", fg="green")
        # First get all the services in the account
        services = Service.objects.using(self.session).all()
        # Save the ClientException for later so that we don't have to use the
        # long form of the exception
        ClientException = Service.objects.using(  # noqa: N806
            self.session
        ).client.exceptions.ClientException

        if verbose:
            click.secho("Finding used images among the services ...", fg="green")
        # Now iterate through each service and get the append its task definition
        # to the list of task definitions
        for service in services:
            if verbose:
                click.secho(
                    f"   Service: {service.cluster_name}:{service.serviceName}",
                    fg="cyan",
                )
            try:
                task_definition = cast("TaskDefinition", service.task_definition)
            except ClientException:
                warnings.warn(
                    f"Task definition {service.taskDefinition} in Service "
                    f"{service.cluster_name}:{service.serviceName} does not exist",
                    UserWarning,
                    stacklevel=2,
                )
            for image_id in task_definition.container_images:
                if image_id not in used_images:
                    try:
                        image = self.__filter_image(
                            image_id,
                            repositoryNames=repositoryNames,
                            repositoryPrefix=repositoryPrefix,
                            tags=tags,
                        )
                    except LookupError:
                        service_name = f"{service.cluster_name}:{service.serviceName}"
                        warnings.warn(
                            f"Image {image_id} not found for service "
                            f"{service_name} task definition "
                            f"{task_definition.family_revision}",
                            UserWarning,
                            stacklevel=2,
                        )
                    else:
                        if image:
                            used_images[image_id] = image

        if verbose:
            click.secho("Finding images in periodic tasks...", fg="green")
        # Now deal with the periodic tasks
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
                            f"for periodic EventRule {rule.arn} does not exist",
                            UserWarning,
                            stacklevel=2,
                        )
                        continue
                    for image_id in task_definition.container_images:
                        try:
                            image = self.__filter_image(
                                image_id,
                                repositoryNames=repositoryNames,
                                repositoryPrefix=repositoryPrefix,
                                tags=tags,
                            )
                        except LookupError:  # noqa: PERF203
                            warnings.warn(
                                f"Image {image_id} not found for periodic EventRule "
                                f"{rule.arn}, task definition {task_definition.family_revision}",  # noqa: E501
                                UserWarning,
                                stacklevel=2,
                            )
                        else:
                            if image:
                                used_images[image_id] = image

        # TODO: We need to check other things that might use images, like Lambda
        # functions, when we get around to implementing the ``lambda`` service.
        return list(used_images.values())


class ECRImageMixin:
    """
    Add a bunch of support for inspecting ECR images and getting information
    from them that AWS does not provide.  This is done by using the docker
    Python library to pull the image and inspect it.

    Note:
        I don't love doing this because it is not pure AWS, which was my
        intention for botocraft, but I need these features for business
        purposes and they are not available in the boto3 library.

    """

    objects: ClassVar["ECRImageManager"]
    repositoryName: str | None
    imageId: "ImageIdentifier"

    @property
    def version(self) -> str:
        """
        Get the version of the image.
        """
        return cast("str", self.imageId.imageTag)

    @property
    def name(self) -> str:
        """
        Get the name of the image.
        """
        if self.imageId.imageTag is None:
            return f"{self.repository.repositoryUri}:{self.imageId.imageDigest}"  # type: ignore[attr-defined]
        return f"{self.repository.repositoryUri}:{self.imageId.imageTag}"  # type: ignore[attr-defined]

    @property
    def image_name(self) -> str:
        """
        Return just the image name, excluding the registry.
        """
        if self.imageId.imageTag is None:
            return f"{self.repository.repositoryName}:{self.imageId.imageDigest}"  # type: ignore[attr-defined]
        return f"{self.repository.repositoryName}:{self.imageId.imageTag}"  # type: ignore[attr-defined]

    @property
    def is_pulled(self) -> bool:
        """
        Check if the image is pulled.

        Returns:
            ``True`` if the image is pulled, ``False`` otherwise.

        """
        ecr_client = self.docker_client
        exists = False
        if ecr_client.client.images.list(self.name):
            exists = True
        ecr_client.client.close()
        return exists

    @property
    def dockerd_is_running(self) -> bool:
        """
        Check if the docker daemon is running.

        We need dockerd to be running to perform these operations:

        * :py:meth:`docker_client`
        * :py:meth:`pull`
        * :py:meth:`is_pulled`
        * :py:meth:`info`
        * :py:meth:`docker_image`
        * :py:meth:`history`
        * :py:meth:`clean`
        * :py:meth:`clean_other_versions`
        """
        try:
            docker.from_env()
        except docker.errors.DockerException:
            return False
        return True

    @property
    def docker_client(self) -> ECRDockerClient:
        """
        Return a docker client, logged into our ECR registry.

        Raises:
            RuntimeError: If the docker daemon is not running.

        Returns:
            A :py:class:`botocraft.mixins.ecr.ECRDockerClient` object, which
            has a docker client, username, password, and registry.

        """
        if not self.dockerd_is_running:
            msg = "Docker daemon is not running, so this command is not available."
            raise RuntimeError(msg)
        docker_client = docker.from_env()
        # Get our authorization token from AWS
        response = self.objects.using(self.session).client.get_authorization_token()  # type: ignore[attr-defined]
        auth_token = base64.b64decode(
            response["authorizationData"][0]["authorizationToken"]
        )
        username, password = auth_token.decode().split(":")
        registry = response["authorizationData"][0]["proxyEndpoint"]
        bare_registry = registry.split("//")[1]
        docker_client.login(username, password=password, registry=registry, reauth=True)
        return ECRDockerClient(
            client=docker_client,
            username=username,
            password=password,
            registry=bare_registry,
        )

    @property
    def info(self) -> ImageInfo:
        """
        Return information about the image.  We're doing this by pulling the
        image from the repository and inspecting it.

        Note:
            I'd love to get the base image for this image, but there is no
            direct way to do it.  You would to look up the layers for the image,
            get the sha256 hash of the first layer (which is the base image),
            then look in in various repositories to find the image that
            has the same layer, then get that image's name.  That seems stupid
            hard to do, especially if the base image is in the ECR registry of
            another AWS account.

        Raises:
            RuntimeError: If the docker daemon is not running.

        Returns:
            A :py:class:`botocraft.services.ecr.ImageInfo` object.

        """
        ecr_client = self.docker_client
        data = ecr_client.client.api.inspect_image(self.name)
        # you can't be logged into two ECR registries at the same time for some reason
        # so we need to log out of the registry we are using.
        ecr_client.client.close()
        # Strip off the nanoseconds from the created date so that strptime can
        # parse it.
        created_date = data["Created"].split(".")[0] + "Z"
        return ImageInfo(
            name=data["RepoTags"][0],
            platform=data["Os"],
            architecture=data["Architecture"],
            size=data["Size"],
            docker_version=data["DockerVersion"],
            user=data["Config"]["User"],
            ports=data["Config"]["ExposedPorts"],
            # Created date looks like: '2024-08-19T21:59:57', convert
            # that to a datetime object.
            created=datetime.datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ"),  # noqa: DTZ007
        )

    @cached_property
    def docker_image(self) -> docker.models.images.Image:
        """
        Return the :py:class:`docker.models.images.Image` object for this image.

        Raises:
            RuntimeError: If the docker daemon is not running.

        """
        ecr_client = self.docker_client
        if not self.is_pulled:
            docker_image = ecr_client.client.images.pull(
                f"{ecr_client.registry}/{self.repositoryName}",
                auth_config={
                    "username": ecr_client.username,
                    "password": ecr_client.password,
                },
                tag=self.imageId.imageTag,
            )
        else:
            docker_image = ecr_client.client.images.get(self.name)
        ecr_client.client.close()
        return docker_image

    @cached_property
    def history(self) -> List[Dict[str, Any]]:
        """
        Return the build history for this image.  You can use this to reconstruct
        **most** of the Dockerfile that was used to build the image.   You won't
        have the ``FROM`` line, but you can get most of the rest of it.

        Raises:
            RuntimeError: If the docker daemon is not running.

        """
        return self.docker_image.history()

    def clean(self) -> None:
        """
        Remove the image from our local docker storage, if it exists.

        Raises:
            RuntimeError: If the docker daemon is not running.

        """
        if self.is_pulled:
            ecr_client = self.docker_client
            ecr_client.client.images.remove(self.name)
            ecr_client.client.close()

    def clean_other_versions(self) -> None:
        """
        Remove the all images for this repository except for the one with
        our version.

        Raises:
            RuntimeError: If the docker daemon is not running.

        """
        ecr_client = self.docker_client
        prefix = f"{ecr_client.registry}/{self.repositoryName}"
        images = ecr_client.client.images.list(prefix)
        for image in images:
            if self.name not in image.tags:
                ecr_client.client.images.remove(f"{prefix}:{image.imageTag}")
        ecr_client.client.close()

    def task_definitions(
        self,
        status: Literal["ACTIVE", "INACTIVE", "ALL"] | None = "ACTIVE",
        tags: Dict[str, str] | None = None,
        verbose: bool = False,
    ) -> List["TaskDefinition"]:
        """
        Return a list of ECS task definitions that use this image.

        Warning:
            This will be quite slow if you have a lot of families and revisions,
            because the only way to deal with this is to get all the task
            definition families,  and then look at each revision to see if one
            of its containers uses this image.  There is no way to filter the
            task definitions by image.

        Args:
            status: The status of the task definition to filter by.  Valid
                values are ``ACTIVE``, ``INACTIVE``, or ``ALL``.  The default
                is ``ACTIVE``.
            tags: A dictionary of tags to filter by.  The default is an empty
                dictionary.
            verbose: If ``True``, print out the task definition family and
                revision that uses this image.  The default is ``False``.

        Returns:
            A list of ECS task definitions that use this image.

        """
        from botocraft.services import TaskDefinition

        if not tags:
            tags = {}

        # First get the families
        families = TaskDefinition.objects.using(self.session).families(status=status)

        task_definitions: List[TaskDefinition] = []

        # Now iterate through each family and revision
        for family in families:
            if verbose:
                click.secho(f"   Family: {family}", fg="cyan")
            revisions = TaskDefinition.objects.using(self.session).list(
                familyPrefix=family,
                sort="DESC",
                status=status,
            )
            task_definitions.extend(
                [
                    revision
                    for revision in revisions
                    if self.name in revision.container_images
                    if tags.items() <= revision.tags.items()
                ]
            )
        return task_definitions

    def services(
        self,
        status: Literal["ACTIVE", "INACTIVE", "ALL"] | None = "ACTIVE",
        tags: Dict[str, str] | None = None,
        verbose: bool = False,
    ) -> List["Service"]:
        """
        Return a list of ECS Services that use this image.

        Warning:
            This will be quite slow if you have a lot of families and revisions,
            because the only way to deal with this is to get all the task
            definition families,  and then look at each revision to see if one
            of its containers uses this image.  Then look through all our services
            to see if there is a service that uses that task definition.

        Args:
            status: The status of the task definition to filter by.  Valid
                values are ``ACTIVE``, ``INACTIVE``, or ``ALL``.  The default
                is ``ACTIVE``.
            tags: A dictionary of tags to filter task definitions and services
                by.  The default is an empty dictionary.
            verbose: If ``True``, print out status messages as we work.

        Returns:
            A list of ECS Services that use this image.

        """
        from botocraft.services import Cluster, Service

        if not tags:
            tags = {}

        task_definitions = self.task_definitions(
            status=status, tags=tags, verbose=verbose
        )

        # There's no way to directly list all services in an account.  We have
        # to list all clusters, then check each service in each cluster.
        services: List[Service] = []
        clusters = Cluster.objects.using(self.session).list()
        for cluster in clusters:
            services.extend(
                [
                    service
                    for service in cluster.services
                    if service.taskDefinition in task_definitions
                    if tags.items() <= service.tags.items()
                ]
            )
        return services

    @property
    def vulnerabilities(self) -> List["Finding"]:
        """
        Return a list of vulnerabilities for this image.  This is done by
        using the AWS Inspector2 service to scan the image and return the
        vulnerabilities.

        Note:
            The AWS Inspector service is not instantaneous, but runs occasionally.
            This doesn't matter much for us, because we are using the ECR immutable
            images, so we can just get the vulnerabilities for the image we are using.

        Warning:
            If this image was just pushed, then the scan may not have run yet.
            In that case, you will need to wait for the scan to run before you
            can get the vulnerabilities.

        Returns:
            A list of vulnerabilities for this image.

        """
        from botocraft.services import FilterCriteria, Finding, StringFilter

        return Finding.objects.using(self.session).list(  # type: ignore[attr-defined]
            filterCriteria=FilterCriteria(
                ecrImageHash=[
                    StringFilter(value=self.imageId.imageDigest, comparison="EQUALS")
                ],
            )
        )
