# This file is automatically generated by botocraft.  Do not edit directly.
# pylint: disable=anomalous-backslash-in-string,unsubscriptable-object,line-too-long,arguments-differ,arguments-renamed,unused-import,redefined-outer-name
# pyright: reportUnusedImport=false
# mypy: disable-error-code="index, override, assignment"
from collections import OrderedDict
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Literal, Optional, Type, cast

from botocraft.mixins.ecr import (ECRImageMixin, RepositoryMixin,
                                  image_list_images_ecr_images_only,
                                  repo_list_images_ecr_images_only)
from botocraft.mixins.tags import TagsDictMixin
from botocraft.services.common import Tag
from pydantic import Field

from .abstract import (Boto3Model, Boto3ModelManager, PrimaryBoto3Model,
                       ReadonlyBoto3Model, ReadonlyBoto3ModelManager,
                       ReadonlyPrimaryBoto3Model)

# ===============
# Managers
# ===============


class RepositoryManager(Boto3ModelManager):
    service_name: str = "ecr"

    def create(
        self, model: "Repository", tags: Optional[List[Tag]] = None
    ) -> "Repository":
        """
        Create an ECR repository.

        Args:
            model: The :py:class:`Repository` to create.

        Keyword Args:
            tags: The metadata that you apply to the repository to help you categorize
                and organize them. Each tag consists of a key and an optional value, both
                of which you define. Tag keys can have a maximum character length of 128
                characters, and tag values can have a maximum length of 256 characters.
        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        args = dict(
            repositoryName=data.get("repositoryName"),
            registryId=data.get("registryId"),
            tags=self.serialize(tags),
            imageTagMutability=data.get("imageTagMutability"),
            imageScanningConfiguration=data.get("imageScanningConfiguration"),
            encryptionConfiguration=data.get("encryptionConfiguration"),
        )
        _response = self.client.create_repository(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = CreateRepositoryResponse(**_response)

        return cast("Repository", response.repository)

    def delete(
        self,
        repositoryName: str,
        *,
        registryId: Optional[str] = None,
        force: Optional[bool] = None
    ) -> "Repository":
        """
        Delete an ECR repository.

        Args:
            repositoryName: The name of the repository to delete.

        Keyword Args:
            registryId: The Amazon Web Services account ID associated with the registry
                that contains the repository to delete. If you do not specify a registry,
                the default registry is assumed.
            force: If true, deleting the repository force deletes the contents of the
                repository. If false, the repository must be empty before attempting to
                delete it.
        """
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            registryId=self.serialize(registryId),
            force=self.serialize(force),
        )
        _response = self.client.delete_repository(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = DeleteRepositoryResponse(**_response)
        return cast(Repository, response.repository)

    def get(
        self, repositoryName: str, *, registryId: Optional[str] = None
    ) -> Optional["Repository"]:
        """
        Describes image repositories in a registry.

        Args:
            repositoryName: The name of the ECR repository to describe.

        Keyword Args:
            registryId: The Amazon Web Services account ID associated with the registry
                that contains the repositories to be described. If you do not specify a
                registry, the default registry is assumed.
        """
        args: Dict[str, Any] = dict(
            registryId=self.serialize(registryId),
            repositoryNames=self.serialize([repositoryName]),
        )
        _response = self.client.describe_repositories(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = DescribeRepositoriesResponse(**_response)

        if response.repositories:
            return response.repositories[0]
        return None

    def list(
        self,
        *,
        registryId: Optional[str] = None,
        repositoryNames: Optional[List[str]] = None
    ) -> List["Repository"]:
        """
        Describes image repositories in a registry.

        Keyword Args:
            registryId: The Amazon Web Services account ID associated with the registry
                that contains the repositories to be described. If you do not specify a
                registry, the default registry is assumed.
            repositoryNames: A list of repositories to describe. If this parameter is
                omitted, then all repositories in a registry are described.
        """
        paginator = self.client.get_paginator("describe_repositories")
        args: Dict[str, Any] = dict(
            registryId=self.serialize(registryId),
            repositoryNames=self.serialize(repositoryNames),
        )
        response_iterator = paginator.paginate(
            **{k: v for k, v in args.items() if v is not None}
        )
        results: List["Repository"] = []
        for _response in response_iterator:
            response = DescribeRepositoriesResponse(**_response)
            if response.repositories:
                results.extend(response.repositories)
            else:
                break
        return results

    @repo_list_images_ecr_images_only
    def list_images(
        self,
        repositoryName: str,
        *,
        registryId: Optional[str] = None,
        filter: Optional["ListImagesFilter"] = None
    ) -> List["ImageIdentifier"]:
        """
        Lists all the image IDs for the specified repository.

        Args:
            repositoryName: The repository with image IDs to be listed.

        Keyword Args:
            registryId: The Amazon Web Services account ID associated with the registry
                that contains the repository in which to list images. If you do not specify
                a registry, the default registry is assumed.
            filter: The filter key and value with which to filter your ``ListImages``
                results.
        """
        paginator = self.client.get_paginator("list_images")
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            registryId=self.serialize(registryId),
            filter=self.serialize(filter),
        )
        response_iterator = paginator.paginate(
            **{k: v for k, v in args.items() if v is not None}
        )
        results: List["ImageIdentifier"] = []
        for _response in response_iterator:
            response = ListImagesResponse(**_response)

            if response.imageIds:
                results.extend(response.imageIds)

            else:
                break
        return results

    def get_images(
        self,
        repositoryName: str,
        imageIds: List["ImageIdentifier"],
        *,
        acceptedMediaTypes: List[str] = [
            "application/vnd.docker.distribution.manifest.v2+json"
        ]
    ) -> Optional[List["Image"]]:
        """
        Use this method when you want to get just a few images from the
        repository. If you want to get all images, use the ````list\_images````
        method.

        Args:
            repositoryName: The repository that contains the images to describe.
            imageIds: A list of image ID references that correspond to images to
                describe. The format of the ``imageIds`` reference is ``imageTag=tag`` or
                ``imageDigest=digest``.

        Keyword Args:
            acceptedMediaTypes: The accepted media types for the request.
        """
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            imageIds=self.serialize(imageIds),
            acceptedMediaTypes=self.serialize(acceptedMediaTypes),
        )
        _response = self.client.batch_get_image(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = BatchGetImageResponse(**_response)

        return response.images

    def get_image(
        self,
        repositoryName: str,
        imageId: "ImageIdentifier",
        *,
        acceptedMediaTypes: List[str] = [
            "application/vnd.docker.distribution.manifest.v2+json"
        ]
    ) -> "Image":
        """
        Gets detailed information for an image. Images are specified with
        either an ``imageTag`` or ``imageDigest``.

        Args:
            repositoryName: The repository that contains the images to describe.
            imageId: The image ID or tag to describe. The format of the imageId
                reference is ````imageTag=tag```` or ````imageDigest=digest````

        Keyword Args:
            acceptedMediaTypes: The accepted media types for the request.
        """
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            imageIds=self.serialize([imageId]),
            acceptedMediaTypes=self.serialize(acceptedMediaTypes),
        )
        _response = self.client.batch_get_image(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = BatchGetImageResponse(**_response)

        return response.images[0]


class ImageManager(Boto3ModelManager):
    service_name: str = "ecr"

    def get(
        self,
        repositoryName: str,
        imageId: "ImageIdentifier",
        *,
        acceptedMediaTypes: List[str] = [
            "application/vnd.docker.distribution.manifest.v2+json"
        ]
    ) -> Optional["Image"]:
        """
        Gets detailed information for an image. Images are specified with
        either an ``imageTag`` or ``imageDigest``.

        Args:
            repositoryName: The repository that contains the images to describe.
            imageId: The image ID or tag to describe. The format of the imageId
                reference is ````imageTag=tag```` or ````imageDigest=digest````

        Keyword Args:
            acceptedMediaTypes: The accepted media types for the request.
        """
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            imageIds=self.serialize([imageId]),
            acceptedMediaTypes=self.serialize(acceptedMediaTypes),
        )
        _response = self.client.batch_get_image(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = BatchGetImageResponse(**_response)

        if response.images:
            return response.images[0]
        return None

    def get_many(
        self,
        repositoryName: str,
        imageIds: List["ImageIdentifier"],
        *,
        acceptedMediaTypes: List[str] = [
            "application/vnd.docker.distribution.manifest.v2+json"
        ]
    ) -> "BatchGetImageResponse":
        """
        Gets detailed information for an image. Images are specified with
        either an ``imageTag`` or ``imageDigest``.

        Args:
            repositoryName: The repository that contains the images to describe.
            imageIds: A list of image ID references that correspond to images to
                describe. The format of the ``imageIds`` reference is ``imageTag=tag`` or
                ``imageDigest=digest``.

        Keyword Args:
            acceptedMediaTypes: The accepted media types for the request.
        """
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            imageIds=self.serialize(imageIds),
            acceptedMediaTypes=self.serialize(acceptedMediaTypes),
        )
        _response = self.client.batch_get_image(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = BatchGetImageResponse(**_response)

        if response is not None:
            return response

        return []

    @image_list_images_ecr_images_only
    def list(
        self, repositoryName: str, *, filter: Optional["ListImagesFilter"] = None
    ) -> List["ImageIdentifier"]:
        """
        Lists all the image IDs for the specified repository.

        Args:
            repositoryName: The repository with image IDs to be listed.

        Keyword Args:
            filter: The filter key and value with which to filter your ``ListImages``
                results.
        """
        paginator = self.client.get_paginator("list_images")
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName), filter=self.serialize(filter)
        )
        response_iterator = paginator.paginate(
            **{k: v for k, v in args.items() if v is not None}
        )
        results: List["ImageIdentifier"] = []
        for _response in response_iterator:
            response = ListImagesResponse(**_response)
            if response.imageIds:
                results.extend(response.imageIds)
            else:
                break
        return results

    def delete(
        self, repositoryName: str, imageId: "ImageIdentifier"
    ) -> "BatchDeleteImageResponse":
        """
        Deletes a list of specified images within a repository. Images are
        specified with either an ``imageTag`` or ``imageDigest``.

        Args:
            repositoryName: The repository that contains the image to delete.
            imageId: The image ID or tag to delete. The format of the imageId reference
                is ````imageTag=tag```` or ````imageDigest=digest````
        """
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            imageIds=self.serialize([imageId]),
        )
        _response = self.client.batch_delete_image(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = BatchDeleteImageResponse(**_response)
        return response

    def replication_status(
        self, repositoryName: str, imageId: "ImageIdentifier"
    ) -> "DescribeImageReplicationStatusResponse":
        """
        Returns the replication status for a specified image.

        Args:
            repositoryName: The name of the repository that the image is in.
            imageId: An object with identifying information for an image in an Amazon
                ECR repository.
        """
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            imageId=self.serialize(imageId),
        )
        _response = self.client.describe_image_replication_status(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = DescribeImageReplicationStatusResponse(**_response)

        return response

    def scan_findings(
        self, repositoryName: str, imageId: "ImageIdentifier"
    ) -> List["DescribeImageScanFindingsResponse"]:
        """
        Returns the scan findings for the specified image.

        Args:
            repositoryName: The repository for the image for which to describe the scan
                findings.
            imageId: An object with identifying information for an image in an Amazon
                ECR repository.
        """
        paginator = self.client.get_paginator("describe_image_scan_findings")
        args: Dict[str, Any] = dict(
            repositoryName=self.serialize(repositoryName),
            imageId=self.serialize(imageId),
        )
        response_iterator = paginator.paginate(
            **{k: v for k, v in args.items() if v is not None}
        )
        results: List["DescribeImageScanFindingsResponse"] = []
        for _response in response_iterator:
            response = DescribeImageScanFindingsResponse(**_response)

            if response is not None:
                try:
                    # Test whether the response is iterable
                    iter(response)
                except TypeError:
                    # If it not, append the response to the results list
                    results.append(response)  # type: ignore[arg-type]
                else:
                    # If it is, extend the results list with the response
                    results.extend(response)  # type: ignore[arg-type]

            else:
                break
        return results


# ==============
# Service Models
# ==============


class ImageScanningConfiguration(Boto3Model):
    """
    The image scanning configuration for a repository.
    """

    scanOnPush: Optional[bool] = None
    """
    The setting that determines whether images are scanned after being pushed
    to a repository.

    If set to ``true``, images will be scanned after being pushed. If
    this parameter is not specified, it will default to ``false`` and images will
    not be scanned unless a scan is manually started with the [API\_StartImageScan]
    (https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_StartImageScan.h
    tml) API.
    """


class EncryptionConfiguration(Boto3Model):
    """
    The encryption configuration for the repository.

    This determines how the contents of your repository are encrypted at rest.
    """

    encryptionType: Literal["AES256", "KMS"]
    """
    The encryption type to use.
    """
    kmsKey: Optional[str] = None
    """
    If you use the ``KMS`` encryption type, specify the KMS key to use for
    encryption.

    The alias, key ID, or full ARN of the KMS key can be specified. The key
    must exist in the same Region as the repository. If no key is specified,
    the default Amazon Web Services managed KMS key for Amazon ECR will be
    used.
    """


class Repository(RepositoryMixin, PrimaryBoto3Model):
    """
    An object representing a repository.
    """

    objects: ClassVar[Boto3ModelManager] = RepositoryManager()

    repositoryName: str
    """
    The name of the repository.
    """
    imageTagMutability: Literal["MUTABLE", "IMMUTABLE"]
    """
    The tag mutability setting for the repository.
    """
    imageScanningConfiguration: ImageScanningConfiguration
    """
    The image scanning configuration for a repository.
    """
    repositoryArn: str = Field(default=None, frozen=True)
    """
    The Amazon Resource Name (ARN) that identifies the repository.

    The ARN contains
    the ``arn:aws:ecr`` namespace, followed by the region of the repository, Amazon
    Web Services account ID of the repository owner, repository namespace, and
    repository name. For example, ``arn:aws:ecr:region:012345678910:repository-
    namespace/repository-name``.
    """
    registryId: Optional[str] = None
    """
    The Amazon Web Services account ID associated with the registry that
    contains the repository.
    """
    repositoryUri: str = Field(default=None, frozen=True)
    """
    The URI for the repository.

    You can use this URI for container image ``push``
    and ``pull`` operations.
    """
    createdAt: datetime = Field(default=None, frozen=True)
    """
    The date and time, in JavaScript date format, when the repository was
    created.
    """
    encryptionConfiguration: Optional[EncryptionConfiguration] = None
    """
    The encryption configuration for the repository.

    This determines how the contents of your repository are encrypted at rest.
    """

    @property
    def pk(self) -> Optional[str]:
        """
        Return the primary key of the model.   This is the value of the
        :py:attr:`repositoryName` attribute.

        Returns:
            The primary key of the model instance.
        """
        return self.repositoryName

    @property
    def arn(self) -> Optional[str]:
        """
        Return the ARN of the model.   This is the value of the
        :py:attr:`repositoryArn` attribute.

        Returns:
            The ARN of the model instance.
        """
        return self.repositoryArn

    @property
    def name(self) -> Optional[str]:
        """
        Return the name of the model.   This is the value of the
        :py:attr:`repositoryName` attribute.

        Returns:
            The name of the model instance.
        """
        return self.repositoryName


class ImageIdentifier(Boto3Model):
    """
    An object containing the image tag and image digest associated with an
    image.
    """

    imageDigest: Optional[str] = None
    """
    The ``sha256`` digest of the image manifest.
    """
    imageTag: Optional[str] = None
    """
    The tag used for the image.
    """


class Image(ECRImageMixin, ReadonlyPrimaryBoto3Model):
    """
    An object representing an Amazon ECR image.
    """

    objects: ClassVar[Boto3ModelManager] = ImageManager()

    registryId: Optional[str] = None
    """
    The Amazon Web Services account ID associated with the registry containing
    the image.
    """
    repositoryName: Optional[str] = None
    """
    The name of the repository associated with the image.
    """
    imageId: ImageIdentifier = Field(default=None, frozen=True)
    """
    An object containing the image tag and image digest associated with an
    image.
    """
    imageManifest: str = Field(default=None, frozen=True)
    """
    The image manifest associated with the image.
    """
    imageManifestMediaType: str = Field(default=None, frozen=True)
    """
    The manifest media type of the image.
    """

    @property
    def pk(self) -> OrderedDict[str, Any]:
        return OrderedDict(
            {
                "repositoryName": self.repositoryName,
                "imageId": self.imageId,
            }
        )

    def replication_status(self) -> "DescribeImageReplicationStatusResponse":
        """
        Return the replication status for the image.
        """

        return cast(ImageManager, self.objects).replication_status(
            cast(str, self.repositoryName), imageId=self.imageId
        )

    def scan_findings(self) -> List["DescribeImageScanFindingsResponse"]:
        """
        Return the scan results for the image.
        """

        return cast(ImageManager, self.objects).scan_findings(
            cast(str, self.repositoryName), imageId=self.imageId
        )


# =======================
# Request/Response Models
# =======================


class CreateRepositoryResponse(Boto3Model):
    repository: Optional[Repository] = None
    """
    The repository that was created.
    """


class DeleteRepositoryResponse(Boto3Model):
    repository: Optional[Repository] = None
    """
    The repository that was deleted.
    """


class DescribeRepositoriesResponse(Boto3Model):
    repositories: Optional[List["Repository"]] = None
    """
    A list of repository objects corresponding to valid repositories.
    """
    nextToken: Optional[str] = None
    """
    The ``nextToken`` value to include in a future ``DescribeRepositories``
    request.

    When the results of a ``DescribeRepositories`` request exceed
    ``maxResults``, this value can be used to retrieve the next page of results.
    This value is ``null`` when there are no more results to return.
    """


class ListImagesFilter(Boto3Model):
    """
    The filter key and value with which to filter your ``ListImages`` results.
    """

    tagStatus: Optional[Literal["TAGGED", "UNTAGGED", "ANY"]] = None
    """
    The tag status with which to filter your ListImages results.

    You can filter
    results based on whether they are ``TAGGED`` or ``UNTAGGED``.
    """


class ListImagesResponse(Boto3Model):
    imageIds: Optional[List["ImageIdentifier"]] = None
    """
    The list of image IDs for the requested repository.
    """
    nextToken: Optional[str] = None
    """
    The ``nextToken`` value to include in a future ``ListImages`` request.

    When the
    results of a ``ListImages`` request exceed ``maxResults``, this value can be
    used to retrieve the next page of results. This value is ``null`` when there
    are no more results to return.
    """


class ImageFailure(Boto3Model):
    """
    An object representing an Amazon ECR image failure.
    """

    imageId: Optional[ImageIdentifier] = None
    """
    The image ID associated with the failure.
    """
    failureCode: Optional[
        Literal[
            "InvalidImageDigest",
            "InvalidImageTag",
            "ImageTagDoesNotMatchDigest",
            "ImageNotFound",
            "MissingDigestAndTag",
            "ImageReferencedByManifestList",
            "KmsError",
            "UpstreamAccessDenied",
            "UpstreamTooManyRequests",
            "UpstreamUnavailable",
        ]
    ] = None
    """
    The code associated with the failure.
    """
    failureReason: Optional[str] = None
    """
    The reason for the failure.
    """


class BatchGetImageResponse(Boto3Model):
    images: Optional[List["Image"]] = None
    """
    A list of image objects corresponding to the image references in the
    request.
    """
    failures: Optional[List["ImageFailure"]] = None
    """
    Any failures associated with the call.
    """


class BatchDeleteImageResponse(Boto3Model):
    imageIds: Optional[List["ImageIdentifier"]] = None
    """
    The image IDs of the deleted images.
    """
    failures: Optional[List["ImageFailure"]] = None
    """
    Any failures associated with the call.
    """


class ImageReplicationStatus(Boto3Model):
    """
    The status of the replication process for an image.
    """

    region: Optional[str] = None
    """
    The destination Region for the image replication.
    """
    registryId: Optional[str] = None
    """
    The Amazon Web Services account ID associated with the registry to which
    the image belongs.
    """
    status: Optional[Literal["IN_PROGRESS", "COMPLETE", "FAILED"]] = None
    """
    The image replication status.
    """
    failureCode: Optional[str] = None
    """
    The failure code for a replication that has failed.
    """


class DescribeImageReplicationStatusResponse(Boto3Model):
    repositoryName: Optional[str] = None
    """
    The repository name associated with the request.
    """
    imageId: Optional[ImageIdentifier] = None
    """
    An object with identifying information for an image in an Amazon ECR
    repository.
    """
    replicationStatuses: Optional[List["ImageReplicationStatus"]] = None
    """
    The replication status details for the images in the specified repository.
    """


class ImageScanStatus(Boto3Model):
    """
    The current state of the scan.
    """

    status: Optional[
        Literal[
            "IN_PROGRESS",
            "COMPLETE",
            "FAILED",
            "UNSUPPORTED_IMAGE",
            "ACTIVE",
            "PENDING",
            "SCAN_ELIGIBILITY_EXPIRED",
            "FINDINGS_UNAVAILABLE",
        ]
    ] = None
    """
    The current state of an image scan.
    """
    description: Optional[str] = None
    """
    The description of the image scan status.
    """


class ECRAttribute(Boto3Model):
    """
    This data type is used in the ImageScanFinding data type.
    """

    key: str
    """
    The attribute key.
    """
    value: Optional[str] = None
    """
    The value assigned to the attribute key.
    """


class ImageScanFinding(Boto3Model):
    """
    Contains information about an image scan finding.
    """

    name: Optional[str] = None
    """
    The name associated with the finding, usually a CVE number.
    """
    description: Optional[str] = None
    """
    The description of the finding.
    """
    uri: Optional[str] = None
    """
    A link containing additional details about the security vulnerability.
    """
    severity: Optional[
        Literal["INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL", "UNDEFINED"]
    ] = None
    """
    The finding severity.
    """
    attributes: Optional[List["ECRAttribute"]] = None
    """
    A collection of attributes of the host from which the finding is generated.
    """


class CvssScore(Boto3Model):
    """
    The CVSS score for a finding.
    """

    baseScore: Optional[float] = None
    """
    The base CVSS score used for the finding.
    """
    scoringVector: Optional[str] = None
    """
    The vector string of the CVSS score.
    """
    source: Optional[str] = None
    """
    The source of the CVSS score.
    """
    version: Optional[str] = None
    """
    The version of CVSS used for the score.
    """


class VulnerablePackage(Boto3Model):
    """
    Information on the vulnerable package identified by a finding.
    """

    arch: Optional[str] = None
    """
    The architecture of the vulnerable package.
    """
    epoch: Optional[int] = None
    """
    The epoch of the vulnerable package.
    """
    filePath: Optional[str] = None
    """
    The file path of the vulnerable package.
    """
    name: Optional[str] = None
    """
    The name of the vulnerable package.
    """
    packageManager: Optional[str] = None
    """
    The package manager of the vulnerable package.
    """
    release: Optional[str] = None
    """
    The release of the vulnerable package.
    """
    sourceLayerHash: Optional[str] = None
    """
    The source layer hash of the vulnerable package.
    """
    version: Optional[str] = None
    """
    The version of the vulnerable package.
    """


class PackageVulnerabilityDetails(Boto3Model):
    """
    An object that contains the details of a package vulnerability finding.
    """

    cvss: Optional[List["CvssScore"]] = None
    """
    An object that contains details about the CVSS score of a finding.
    """
    referenceUrls: Optional[List[str]] = None
    """
    One or more URLs that contain details about this vulnerability type.
    """
    relatedVulnerabilities: Optional[List[str]] = None
    """
    One or more vulnerabilities related to the one identified in this finding.
    """
    source: Optional[str] = None
    """
    The source of the vulnerability information.
    """
    sourceUrl: Optional[str] = None
    """
    A URL to the source of the vulnerability information.
    """
    vendorCreatedAt: Optional[datetime] = None
    """
    The date and time that this vulnerability was first added to the vendor's
    database.
    """
    vendorSeverity: Optional[str] = None
    """
    The severity the vendor has given to this vulnerability type.
    """
    vendorUpdatedAt: Optional[datetime] = None
    """
    The date and time the vendor last updated this vulnerability in their
    database.
    """
    vulnerabilityId: Optional[str] = None
    """
    The ID given to this vulnerability.
    """
    vulnerablePackages: Optional[List["VulnerablePackage"]] = None
    """
    The packages impacted by this vulnerability.
    """


class Recommendation(Boto3Model):
    """
    An object that contains information about the recommended course of action
    to remediate the finding.
    """

    url: Optional[str] = None
    """
    The URL address to the CVE remediation recommendations.
    """
    text: Optional[str] = None
    """
    The recommended course of action to remediate the finding.
    """


class Remediation(Boto3Model):
    """
    An object that contains the details about how to remediate a finding.
    """

    recommendation: Optional[Recommendation] = None
    """
    An object that contains information about the recommended course of action
    to remediate the finding.
    """


class AwsEcrContainerImageDetails(Boto3Model):
    """
    An object that contains details about the Amazon ECR container image
    involved in the finding.
    """

    architecture: Optional[str] = None
    """
    The architecture of the Amazon ECR container image.
    """
    author: Optional[str] = None
    """
    The image author of the Amazon ECR container image.
    """
    imageHash: Optional[str] = None
    """
    The image hash of the Amazon ECR container image.
    """
    imageTags: Optional[List[str]] = None
    """
    The image tags attached to the Amazon ECR container image.
    """
    platform: Optional[str] = None
    """
    The platform of the Amazon ECR container image.
    """
    pushedAt: Optional[datetime] = None
    """
    The date and time the Amazon ECR container image was pushed.
    """
    registry: Optional[str] = None
    """
    The registry the Amazon ECR container image belongs to.
    """
    repositoryName: Optional[str] = None
    """
    The name of the repository the Amazon ECR container image resides in.
    """


class ResourceDetails(Boto3Model):
    """
    An object that contains details about the resource involved in a finding.
    """

    awsEcrContainerImage: Optional[AwsEcrContainerImageDetails] = None
    """
    An object that contains details about the Amazon ECR container image
    involved in the finding.
    """


class Resource(TagsDictMixin, Boto3Model):
    """
    Details about the resource involved in a finding.
    """

    tag_class: ClassVar[Type] = Dict[str, str]
    Tags: Dict[str, str] = Field(default=None, serialization_alias="tags")
    """
    The tags attached to the resource.
    """
    details: Optional[ResourceDetails] = None
    """
    An object that contains details about the resource involved in a finding.
    """
    id: Optional[str] = None
    """
    The ID of the resource.
    """
    type: Optional[str] = None
    """
    The type of resource.
    """


class CvssScoreAdjustment(Boto3Model):
    """
    Details on adjustments Amazon Inspector made to the CVSS score for a
    finding.
    """

    metric: Optional[str] = None
    """
    The metric used to adjust the CVSS score.
    """
    reason: Optional[str] = None
    """
    The reason the CVSS score has been adjustment.
    """


class CvssScoreDetails(Boto3Model):
    """
    An object that contains details about the CVSS score given to a finding.
    """

    adjustments: Optional[List["CvssScoreAdjustment"]] = None
    """
    An object that contains details about adjustment Amazon Inspector made to
    the CVSS score.
    """
    score: Optional[float] = None
    """
    The CVSS score.
    """
    scoreSource: Optional[str] = None
    """
    The source for the CVSS score.
    """
    scoringVector: Optional[str] = None
    """
    The vector for the CVSS score.
    """
    version: Optional[str] = None
    """
    The CVSS version used in scoring.
    """


class ScoreDetails(Boto3Model):
    """
    An object that contains details of the Amazon Inspector score.
    """

    cvss: Optional[CvssScoreDetails] = None
    """
    An object that contains details about the CVSS score given to a finding.
    """


class EnhancedImageScanFinding(Boto3Model):
    """
    The details of an enhanced image scan.

    This is returned when enhanced scanning is enabled for your private
    registry.
    """

    awsAccountId: Optional[str] = None
    """
    The Amazon Web Services account ID associated with the image.
    """
    description: Optional[str] = None
    """
    The description of the finding.
    """
    findingArn: Optional[str] = None
    """
    The Amazon Resource Number (ARN) of the finding.
    """
    firstObservedAt: Optional[datetime] = None
    """
    The date and time that the finding was first observed.
    """
    lastObservedAt: Optional[datetime] = None
    """
    The date and time that the finding was last observed.
    """
    packageVulnerabilityDetails: Optional[PackageVulnerabilityDetails] = None
    """
    An object that contains the details of a package vulnerability finding.
    """
    remediation: Optional[Remediation] = None
    """
    An object that contains the details about how to remediate a finding.
    """
    resources: Optional[List["Resource"]] = None
    """
    Contains information on the resources involved in a finding.
    """
    score: Optional[float] = None
    """
    The Amazon Inspector score given to the finding.
    """
    scoreDetails: Optional[ScoreDetails] = None
    """
    An object that contains details of the Amazon Inspector score.
    """
    severity: Optional[str] = None
    """
    The severity of the finding.
    """
    status: Optional[str] = None
    """
    The status of the finding.
    """
    title: Optional[str] = None
    """
    The title of the finding.
    """
    type: Optional[str] = None
    """
    The type of the finding.
    """
    updatedAt: Optional[datetime] = None
    """
    The date and time the finding was last updated at.
    """


class ImageScanFindings(ReadonlyBoto3Model):
    """
    The information contained in the image scan findings.
    """

    findingSeverityCounts: Optional[
        Optional[
            Dict[
                Literal[
                    "INFORMATIONAL",
                    "LOW",
                    "MEDIUM",
                    "HIGH",
                    "CRITICAL",
                    "UNDEFINED",
                    "UNTRIAGED",
                ],
                int,
            ]
        ]
    ] = None
    """
    The image vulnerability counts, sorted by severity.
    """
    imageScanCompletedAt: Optional[datetime] = None
    """
    The time of the last completed image scan.
    """
    vulnerabilitySourceUpdatedAt: Optional[datetime] = None
    """
    The time when the vulnerability data was last scanned.
    """
    findings: Optional[List["ImageScanFinding"]] = None
    """
    The findings from the image scan.
    """
    enhancedFindings: Optional[List["EnhancedImageScanFinding"]] = None
    """
    Details about the enhanced scan findings from Amazon Inspector.
    """


class DescribeImageScanFindingsResponse(Boto3Model):
    registryId: Optional[str] = None
    """
    The registry ID associated with the request.
    """
    repositoryName: Optional[str] = None
    """
    The repository name associated with the request.
    """
    imageId: Optional[ImageIdentifier] = None
    """
    An object with identifying information for an image in an Amazon ECR
    repository.
    """
    imageScanStatus: Optional[ImageScanStatus] = None
    """
    The current state of the scan.
    """
    imageScanFindings: Optional[ImageScanFindings] = None
    """
    The information contained in the image scan findings.
    """
    nextToken: Optional[str] = None
    """
    The ``nextToken`` value to include in a future
    ``DescribeImageScanFindings`` request.

    When the results of a ``DescribeImageScanFindings`` request exceed
    ``maxResults``, this value can be used to retrieve the next page of results.
    This value is null when there are no more results to return.
    """
