from functools import cached_property
from typing import TYPE_CHECKING, Optional

from .base import EventBridgeEvent
from .raw import (
    ECRImageActionEvent as RawECRImageActionEvent,
)
from .raw import (
    ECRImageScanEvent as RawECRImageScanEvent,
)
from .raw import (
    ECRPullThroughCacheActionEvent as RawECRPullThroughCacheActionEvent,
)
from .raw import (
    ECRReferrerActionEvent as RawECRReferrerActionEvent,
)
from .raw import (
    ECRReplicationActionEvent as RawECRReplicationActionEvent,
)
from .raw import (
    ECRScanResourceChangeEvent as RawECRScanResourceChangeEvent,
)
from .raw import (
    ECSAWSAPICallViaCloudTrailEvent as RawECSAWSAPICallViaCloudTrailEvent,
)

if TYPE_CHECKING:
    from botocraft.services.ecr import ECRImage, Repository


class ECRImageActionEvent(EventBridgeEvent, RawECRImageActionEvent):
    """
    ECR Image Action Event class.

    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECR Image Action: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"repository_name={self.detail.repository_name}, "
            f"image_digest={self.detail.image_digest}, "
            f"image_tag={self.detail.image_tag}, "
            f"action_type={self.detail.action_type}, "
            f"result={self.detail.result}>"
        )

    @cached_property
    def image(self) -> Optional["ECRImage"]:
        """
        Return the ECR image object named by the event.
        """
        from botocraft.services.ecr import ECRImage, ImageIdentifier

        if not self.detail.image_digest:
            return None

        return ECRImage.objects.using(self.session).get(
            repository_name=self.detail.repository_name,
            imageIds=[ImageIdentifier(imageDigest=self.detail.image_digest)],
        )


class ECRImageScanEvent(EventBridgeEvent, RawECRImageScanEvent):
    """
    ECR Image Scan Event class.

    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECR Scan Action: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"repository_name={self.detail.repository_name}, "
            f"image_digest={self.detail.image_digest}, "
            f"image_tags={self.detail.image_tags}, "
            f"scan_status={self.detail.scan_status}>"
        )

    @cached_property
    def image(self) -> Optional["ECRImage"]:
        """
        Return the ECR image object named by the event.
        """
        from botocraft.services.ecr import ECRImage, ImageIdentifier

        if not self.detail.image_digest:
            return None

        return ECRImage.objects.using(self.session).get(
            repository_name=self.detail.repository_name,
            imageIds=[ImageIdentifier(imageDigest=self.detail.image_digest)],
        )


class ECRReferrerActionEvent(EventBridgeEvent, RawECRReferrerActionEvent):
    """
    ECR Image Scan Event class.

    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECR Referrer Action: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"repository_name={self.detail.repository_name}, "
            f"image_digest={self.detail.image_digest}, "
            f"image_tag={self.detail.image_tag}, "
            f"result={self.detail.result}>"
        )

    @cached_property
    def image(self) -> Optional["ECRImage"]:
        """
        Return the ECR image object named by the event.
        """
        from botocraft.services.ecr import ECRImage, ImageIdentifier

        if not self.detail.image_digest:
            return None

        return ECRImage.objects.using(self.session).get(
            repository_name=self.detail.repository_name,
            imageIds=[ImageIdentifier(imageDigest=self.detail.image_digest)],
        )

    @cached_property
    def repository(self) -> Optional["Repository"]:
        """
        Return the ECR repository object named by the event.
        """
        from botocraft.services.ecr import Repository

        return Repository.objects.using(self.session).get(
            repository_name=self.detail.repository_name, include=["TAGS"]
        )


class ECRPullThroughCacheActionEvent(
    EventBridgeEvent, RawECRPullThroughCacheActionEvent
):
    """
    ECR Pull Through Cache Action Event class.

    This event is triggered when a pull through cache is synchronized with an
    upstream registry. It contains details about the synchronization status,
    repository details, and any failure information if the operation was
    unsuccessful.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECR PullThroughCache Action: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"repository_name={self.detail.repository_name}, "
            f"image_digest={self.detail.image_digest}, "
            f"image_tag={self.detail.image_tag}, "
            f"sync_status={self.detail.sync_status}, "
            f"ecr_repository_prefix={self.detail.ecr_repository_prefix}, "
            f"upstream_registry_url={self.detail.upstream_registry_url}>"
        )

    @cached_property
    def image(self) -> Optional["ECRImage"]:
        """
        Return the ECR image object named by the event.
        """
        from botocraft.services.ecr import ECRImage, ImageIdentifier

        if not self.detail.image_digest:
            return None

        return ECRImage.objects.using(self.session).get(
            repository_name=self.detail.repository_name,
            imageIds=[ImageIdentifier(imageDigest=self.detail.image_digest)],
        )

    @cached_property
    def repository(self) -> Optional["Repository"]:
        """
        Return the ECR repository object named by the event.
        """
        from botocraft.services.ecr import Repository

        return Repository.objects.using(self.session).get(
            repository_name=self.detail.repository_name, include=["TAGS"]
        )


class ECRReplicationActionEvent(EventBridgeEvent, RawECRReplicationActionEvent):
    """
    ECR Replication Action Event class.

    This event is triggered when an image is replicated between ECR repositories
    across regions or accounts. It contains details about the replication action,
    including the image being replicated and the result status of the operation.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECR PullThroughCache Action: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"repository_name={self.detail.repository_name}, "
            f"image_digest={self.detail.image_digest}, "
            f"image_tag={self.detail.image_tag}, "
            f"action_type={self.detail.action_type}, "
            f"result={self.detail.result}>"
        )

    @cached_property
    def image(self) -> Optional["ECRImage"]:
        """
        Return the ECR image object named by the event.
        """
        from botocraft.services.ecr import ECRImage, ImageIdentifier

        if not self.detail.image_digest:
            return None

        return ECRImage.objects.using(self.session).get(
            repository_name=self.detail.repository_name,
            imageIds=[ImageIdentifier(imageDigest=self.detail.image_digest)],
        )

    @cached_property
    def repository(self) -> Optional["Repository"]:
        """
        Return the ECR repository object named by the event.
        """
        from botocraft.services.ecr import Repository

        return Repository.objects.using(self.session).get(
            repository_name=self.detail.repository_name, include=["TAGS"]
        )


class ECRScanResourceChangeEvent(EventBridgeEvent, RawECRScanResourceChangeEvent):
    """
    ECR Scan Resource Change Event class.

    This event is triggered when the scan status of an image in an ECR repository
    changes. It contains details about the image and the new scan status.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECR Scan Resource Change: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}, "
            f"repositories={self.detail.repositories}, "
            f"scan_type={self.detail.scan_type}, "
            f"resource_type={self.detail.resource_type}, "
            f"action_type={self.detail.action_type}> "
        )

    @cached_property
    def repositories(self) -> list["Repository"]:
        """
        Return the ECR image object named by the event.
        """
        from botocraft.services.ecr import Repository

        repository_names = [
            repository.repository_name for repository in self.detail.repositories
        ]
        repositories: list[Repository] = []
        repositories = [
            Repository.objects.using(self.session).get(
                repository_name=repository_name, include=["TAGS"]
            )
            for repository_name in repository_names
        ]
        return repositories  # noqa: RET504


class ECRAWSAPICallViaCloudTrailEvent(
    EventBridgeEvent, RawECSAWSAPICallViaCloudTrailEvent
):
    """
    ECR AWS API Call Via CloudTrail Event class.

    This event is triggered when an AWS API call is made via CloudTrail. It
    contains details about the API call, including the event name, source IP,
    and user agent.
    """

    def __str__(self) -> str:
        """
        Return a string representation of the event.
        """
        return (
            f"<Event: ECR AWS API Call Via CloudTrail: account={self.account}, "
            f"source={self.source}, "
            f"time={self.time}, "
            f"region={self.region}, "
            f"resources={self.resources}> "
        )

    @cached_property
    def images(self) -> list["ECRImage"]:
        """
        Return the ECR image object named by the event.
        """
        from botocraft.services.ecr import ECRImage, ImageIdentifier

        return ECRImage.objects.using(self.session).get_many(  # type: ignore[attr-defined]
            repository_name=self.detail.requestParameters.repositoryName,  # type: ignore[attr-defined]
            imageIds=[
                ImageIdentifier(imageTag=imageId.imageTag)
                for imageId in self.detail.requestParameters.imageIds  # type: ignore[attr-defined]
            ],
        )
