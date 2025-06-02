from __future__ import annotations

from datetime import datetime  # noqa: TC003
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ScanFrequency(Enum):
    """
    Enumeration of possible ECR image scan frequency settings.
    Defines how often AWS ECR will scan container images for vulnerabilities.
    """

    #: Scan images only when they are first pushed to the repository
    SCAN_ON_PUSH = "SCAN_ON_PUSH"
    #: Continuously scan images in the repository
    CONTINUOUS_SCAN = "CONTINUOUS_SCAN"
    #: Only scan images when manually requested
    MANUAL = "MANUAL"


class Repository(BaseModel):
    """
    Represents an ECR repository affected by a scan resource change.  Contains
    details about the repository and how its scan configuration has changed.
    """

    #: The name of the ECR repository
    repository_name: str = Field(..., alias="repository-name")
    #: The ARN (Amazon Resource Name) of the ECR repository
    repository_arn: str = Field(..., alias="repository-arn")
    #: The new scan frequency setting for the repository
    scan_frequency: ScanFrequency = Field(..., alias="scan-frequency")
    #: The previous scan frequency setting before this change
    previous_scan_frequency: ScanFrequency = Field(
        ...,
        alias="previous-scan-frequency",
    )


class ScanType(Enum):
    """
    Enumeration of ECR scan types.
    Defines the type of vulnerability scanning being performed on ECR images.
    """

    #: Enhanced scanning uses Amazon Inspector and provides more comprehensive results
    ENHANCED = "ENHANCED"
    #: Basic scanning provides fundamental vulnerability detection
    BASIC = "BASIC"


class ScanResourceChange(BaseModel):
    """
    Represents details about a change to ECR scan resource configuration.
    Contains information about what type of change occurred and which
    repositories were affected.
    """

    #: The type of scan resource change action (e.g., "SCAN_FREQUENCY_CHANGE")
    action_type: str = Field(..., alias="action-type")
    #: List of repositories affected by the scan resource change
    repositories: List[Repository] = Field(default_factory=list)
    #: The type of resource affected by the scan change (typically "REPOSITORY")
    resource_type: str = Field(..., alias="resource-type")
    #: The type of scan configured (ENHANCED or BASIC)
    scan_type: ScanType = Field(..., alias="scan-type")


class ECRScanResourceChangeEvent(BaseModel):
    """
    Represents a complete ECR Scan Resource Change event from EventBridge.
    Contains metadata about the event and the actual scan resource change details.
    """

    #: The detailed information about the scan resource change
    detail: ScanResourceChange
    #: The version of the event schema format
    version: str
    #: The unique identifier for this event instance
    id: str
    #: The human-readable type of the event (e.g., "ECR Scan Resource Change")
    detail_type: str = Field(..., alias="detail-type")
    #: The source of the event (typically "aws.ecr")
    source: str
    #: The AWS account ID where the event occurred
    account: str
    #: The timestamp when the event was generated, in UTC
    time: datetime
    #: The AWS region where the event occurred
    region: str
    #: The AWS resources involved in this event, typically repository ARNs
    resources: List[str]
