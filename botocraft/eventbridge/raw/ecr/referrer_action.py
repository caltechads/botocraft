from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import List

from pydantic import BaseModel, Field


class ECRReferrerAction(BaseModel):
    """
    Represents details about an action performed on an ECR referrer.  This
    includes pulls and other operations on container images referenced by an
    upstream image or repository.
    """

    #: The type of action performed on the referrer (e.g., "PULL")
    action_type: str = Field(..., alias="action-type")
    #: The SHA256 digest of the image being referenced
    image_digest: str | None = Field(None, alias="image-digest")
    #: The tag associated with the referenced image, if any
    image_tag: str | None = Field(None, alias="image-tag")
    #: The name of the ECR repository containing the referenced image
    repository_name: str = Field(..., alias="repository-name")
    #: The result of the action (e.g., "SUCCESS")
    result: str
    #: The media type of the image manifest
    manifest_media_type: str | None = Field(None, alias="manifest-media-type")
    #: The media type of the artifact
    artifact_media_type: str | None = Field(None, alias="artifact-media-type")


class ECRReferrerActionEvent(BaseModel):
    """
    Represents a complete ECR Referrer Action event from EventBridge.
    Contains metadata about the event and the actual referrer action details.
    """

    #: The detailed information about the ECR referrer action
    detail: ECRReferrerAction
    #: The AWS account ID where the event occurred
    account: str
    #: The human-readable type of the event (e.g., "ECR Referrer Action")
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
