from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import List

from pydantic import BaseModel, Field


class ECRPullThroughCacheAction(BaseModel):
    """
    Represents details about an ECR pull-through cache action.  Contains
    information about the pull-through cache operation, including status,
    repository details, and any failure information if the operation was
    unsuccessful.
    """

    #: The status of the cache synchronization operation (e.g., "SUCCESS", "FAILURE")
    sync_status: str = Field(..., alias="sync-status")
    #: The ECR repository prefix used for the pull-through cache configuration
    ecr_repository_prefix: str = Field(..., alias="ecr-repository-prefix")
    #: The name of the repository being cached
    repository_name: str = Field(..., alias="repository-name")
    #: The URL of the upstream registry from which images are being pulled
    upstream_registry_url: str = Field(..., alias="upstream-registry-url")
    #: The tag of the image being pulled through the cache, if applicable
    image_tag: str | None = Field(None, alias="image-tag")
    #: The SHA256 digest of the image being pulled through the cache, if applicable
    image_digest: str | None = Field(None, alias="image-digest")
    #: A code indicating the reason for failure, if the operation failed
    failure_code: str | None = Field(None, alias="failure-code")
    #: A human-readable description of why the operation failed, if applicable
    failure_reason: str | None = Field(None, alias="failure-reason")


class ECRPullThroughCacheActionEvent(BaseModel):
    """
    Represents a complete ECR Pull Through Cache Action event from EventBridge.
    Contains metadata about the event and the actual pull-through cache action
    details.
    """

    #: The detailed information about the ECR pull-through cache action
    detail: ECRPullThroughCacheAction
    #: The AWS account ID where the event occurred
    account: str
    #: The human-readable type of the event (e.g., "ECR Pull Through Cache Action")
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
