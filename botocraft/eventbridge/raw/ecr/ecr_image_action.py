from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import List

from pydantic import BaseModel, Field


class ECRImageAction(BaseModel):
    """
    Represents details about an action performed on an ECR image.
    This includes pushes, pulls, and other operations on container images.
    """

    #: The type of action performed (e.g., "PUSH", "PULL")
    action_type: str = Field(..., alias="action-type")
    #: The SHA256 digest of the image
    image_digest: str | None = Field(None, alias="image-digest")
    #: The tag associated with the image, if any
    image_tag: str | None = Field(None, alias="image-tag")
    #: The name of the ECR repository containing the image
    repository_name: str = Field(..., alias="repository-name")
    #: The result of the action (e.g., "SUCCESS")
    result: str
    #: The media type of the image manifest
    manifest_media_type: str | None = Field(None, alias="manifest-media-type")
    #: The media type of the artifact
    artifact_media_type: str | None = Field(None, alias="artifact-media-type")


class ECRImageActionEvent(BaseModel):
    """
    Represents a complete ECR Image Action event from EventBridge.
    Contains metadata about the event and the actual image action details.
    """

    #: The detailed information about the ECR image action
    detail: ECRImageAction
    #: The AWS account ID where the event occurred
    account: str
    #: The human-readable type of the event (e.g., "ECR Image Action")
    detail_type: str = Field(..., alias="detail-type")
    #: The unique identifier for this event instance
    id: str
    #: The AWS region where the event occurred
    region: str
    #: The AWS resources involved in this event, typically the repository ARN
    resources: List[str]
    #: The source of the event (typically "aws.ecr")
    source: str
    #: The timestamp when the event was generated, in UTC
    time: datetime
    #: The version of the event schema format
    version: str
