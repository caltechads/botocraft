import base64
import datetime
from functools import cached_property
from typing import (
    cast,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
)

import docker
from pydantic import BaseModel

if TYPE_CHECKING:
    from botocraft.services import (
        Image,
        ImageManager,
        ImageIdentifier,
        RepositoryManager,
    )


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
    that is not available from the boto3 library.
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
    user: Optional[str] = None
    #: When the image was created, as a UTC datetime object
    created: datetime.datetime


# decorators

# Repository

def repo_list_images_ecr_images_only(func: Callable[..., List["ImageIdentifier"]]) -> Callable[..., List["Image"]]:
    """
    Convert a list of ECR image identifiers returned by ``list_images`` to a
    list of :py:class:`botocraft.services.ecr.Image` objects.
    """
    def wrapper(self, *args, **kwargs) -> List["Image"]:
        identifiers: List["ImageIdentifier"] = func(self, *args, **kwargs)
        images: List["Image"] = []
        # NOTE: to be honest i'm not sure if there is a per request limit
        # for the number of images that can be retrieved, but i'm going to
        # assume that there is a limit of 100 images per request.
        for i in range(0, len(identifiers), 100):
            _images = self.get_images(
                repositoryName=args[0],
                imageIds=identifiers[i:i + 100]
            )
            if _images:
                images.extend(_images)
        return images
    return wrapper


# Image

def image_list_images_ecr_images_only(func: Callable[..., List["ImageIdentifier"]]) -> Callable[..., List["Image"]]:
    """
    Convert a list of ECR image identifiers returned by ``list_images`` to a
    list of :py:class:`botocraft.services.ecr.Image` objects.
    """
    def wrapper(self, *args, **kwargs) -> List["Image"]:
        identifiers: List["ImageIdentifier"] = func(self, *args, **kwargs)
        images: List["Image"] = []
        # NOTE: to be honest i'm not sure if there is a per request limit
        # for the number of images that can be retrieved, but i'm going to
        # assume that there is a limit of 100 images per request.
        for i in range(0, len(identifiers), 100):
            _images = self.get_many(
                repositoryName=args[0],
                imageIds=identifiers[i:i + 100]
            )
            if _images:
                images.extend(_images.images)
        return images
    return wrapper


# Mixins

class RepositoryMixin:

    objects: ClassVar["RepositoryManager"]

    # properties

    @property
    def images(self) -> Optional[List["Image"]]:
        """
        Get a list of images for a given repository.
        """
        return self.objects.list_images(
            repositoryName=self.repositoryName  # type: ignore
        )

    # methods

    def get_image(self, imageId: "ImageIdentifier") -> Optional["Image"]:
        """
        Get an image object for a given repository and image identifier.

        Args:
            imageId: The image ID or tag to describe. The format of the imageId
                reference is ``imageTag=tag`` or ``imageDigest=digest``
        """
        return self.objects.get_image(
            self.repositoryName,  # type: ignore
            imageId=imageId
        )


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

    objects: ClassVar["ImageManager"]
    repositoryName: Optional[str]
    imageId: "ImageIdentifier"

    @property
    def version(self) -> str:
        """
        Get the version of the image.
        """
        return cast(str, self.imageId.imageTag)

    @property
    def name(self) -> str:
        """
        Get the name of the image.
        """
        return f'{self.docker_client.registry}/{self.repositoryName}:{self.imageId.imageTag}'

    @property
    def is_pulled(self) -> bool:
        """
        Check if the image is pulled.

        Returns:
            ``True`` if the image is pulled, ``False`` otherwise.
        """
        if self.docker_client.client.images.list(self.name):
            return True
        return False

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

    @cached_property
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
            raise RuntimeError(
                'Docker daemon is not running, so this command is not available.'
            )
        docker_client = docker.from_env()
        # Get our authorization token from AWS
        response = self.objects.client.get_authorization_token()
        auth_token = base64.b64decode(response['authorizationData'][0]['authorizationToken'])
        username, password = auth_token.decode().split(':')
        registry = response['authorizationData'][0]['proxyEndpoint']
        bare_registry = registry.split('//')[1]
        docker_client.login(username, password=password, registry=registry)
        return ECRDockerClient(
            client=docker_client,
            username=username,
            password=password,
            registry=bare_registry
        )

    @cached_property
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
            hard to do.

        Raises:
            RuntimeError: If the docker daemon is not running.

        Returns:
            A :py:class:`botocraft.services.ecr.ImageInfo` object.
        """
        ecr_client = self.docker_client
        data  = ecr_client.client.api.inspect_image(self.name)
        # Strip off the nanoseconds from the created date so that strptime can
        # parse it.
        created_date = data['Created'].split('.')[0] + 'Z'
        return ImageInfo(
            name=data['RepoTags'][0],
            platform=data['Os'],
            architecture=data['Architecture'],
            size=data['Size'],
            docker_version=data['DockerVersion'],
            user=data['Config']['User'],
            ports=data['Config']['ExposedPorts'],
            # Created date looks like: '2024-08-19T21:59:57', convert
            # that to a datetime object.
            created=datetime.datetime.strptime(created_date, '%Y-%m-%dT%H:%M:%SZ')
        )

    @cached_property
    def docker_image(self) -> docker.models.images.Image:
        """
        Get the build history for this image.
        """
        ecr_client = self.docker_client
        if not self.is_pulled:
            docker_image = ecr_client.client.images.pull(
                f'{ecr_client.registry}/{self.repositoryName}',
                auth_config={
                    'username': ecr_client.username,
                    'password': ecr_client.password
                },
                tag=self.imageId.imageTag
            )
        else:
            docker_image = ecr_client.client.images.get(self.name)
        return docker_image

    @cached_property
    def history(self) -> List[Dict[str, Any]]:
        """
        Return the build history for this image.

        Raises:
            RuntimeError: If the docker daemon is not running.
        """
        return self.docker_image.history()

    # method
    def clean(self) -> None:
        """
        Remove the image from our local docker storage, if it exists.

        Raises:
            RuntimeError: If the docker daemon is not running.
        """
        if self.is_pulled:
            self.docker_client.client.images.remove(self.name)

    # method
    def clean_other_versions(self) -> None:
        """
        Remove the all images for this repository except for the one with
        our version.

        Raises:
            RuntimeError: If the docker daemon is not running.
        """
        ecr_client = self.docker_client
        prefix = f'{ecr_client.registry}/{self.repositoryName}'
        images = ecr_client.client.images.list(prefix)
        for image in images:
            if self.name not in image.tags:
                ecr_client.client.images.remove(f'{prefix}:{image.imageTag}')
