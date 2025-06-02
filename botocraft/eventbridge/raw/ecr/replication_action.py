from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import List

from pydantic import BaseModel, Field


class ECRReplicationAction(BaseModel):
    """
    Represents details about an ECR image replication action.  Contains
    information about images being replicated between ECR repositories across
    regions or accounts, along with the result status of the operation.
    """

    #: The type of replication action performed (e.g., "PUSH", "PULL")
    action_type: str = Field(..., alias="action-type")
    #: The SHA256 digest of the image being replicated
    image_digest: str = Field(..., alias="image-digest")
    #: The tag associated with the image being replicated
    image_tag: str = Field(..., alias="image-tag")
    #: The name of the ECR repository where the image is being replicated
    repository_name: str = Field(..., alias="repository-name")
    #: The result of the replication action (e.g., "SUCCESS", "FAILURE")
    result: str
    #: The AWS account ID of the source repository
    source_account: str = Field(..., alias="source-account")
    #: The AWS region of the source repository
    source_region: str = Field(..., alias="source-region")


class ECRReplicationActionEvent(BaseModel):
    """
    Represents a complete ECR Replication Action event from EventBridge.
    Contains metadata about the event and the actual replication action details.
    """

    #: The detailed information about the ECR replication action
    detail: ECRReplicationAction
    #: The AWS account ID where the event occurred
    account: str
    #: The human-readable type of the event (e.g., "ECR Image Replication")
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
