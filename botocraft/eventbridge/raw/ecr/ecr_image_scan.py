from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import List

from pydantic import BaseModel, Field


class FindingSeverityCounts(BaseModel):
    """
    Represents the counts of security findings by severity level from an ECR image scan.
    Each attribute indicates the number of findings at that severity level.
    """

    #: Number of critical severity findings detected in the scan
    CRITICAL: float | None = None
    #: Number of high severity findings detected in the scan
    HIGH: float | None = None
    #: Number of informational severity findings detected in the scan
    INFORMATIONAL: float | None = None
    #: Number of low severity findings detected in the scan
    LOW: float | None = None
    #: Number of medium severity findings detected in the scan
    MEDIUM: float | None = None
    #: Number of findings with undefined severity level
    UNDEFINED: float | None = None


class ECRImageScan(BaseModel):
    """
    Represents the details of an ECR image scan operation.
    Contains information about the scanned image and the scan results.
    """

    #: The SHA256 digest of the image that was scanned
    image_digest: str | None = Field(None, alias="image-digest")
    #: The list of tags associated with the scanned image
    image_tags: List[str] | None = Field(None, alias="image-tags")
    #: The name of the ECR repository containing the scanned image
    repository_name: str = Field(..., alias="repository-name")
    #: The status of the scan operation (e.g., "COMPLETE", "FAILED")
    scan_status: str = Field(..., alias="scan-status")
    #: The counts of findings grouped by severity level
    finding_severity_counts: FindingSeverityCounts | None = Field(
        None, alias="finding-severity-counts"
    )


class ECRImageScanEvent(BaseModel):
    """
    Represents a complete ECR Image Scan event from EventBridge.
    Contains metadata about the event and the actual scan details.
    """

    #: The detailed information about the image scan operation
    detail: ECRImageScan
    #: The AWS account ID where the scan was performed
    account: str
    #: The human-readable type of the event (e.g., "ECR Image Scan")
    detail_type: str = Field(..., alias="detail-type")
    #: The unique identifier for this event instance
    id: str
    #: The AWS region where the scan was performed
    region: str
    #: The AWS resources involved in this event, typically the repository ARN
    resources: List[str]
    #: The source of the event (typically "aws.ecr")
    source: str
    #: The timestamp when the scan was completed and event generated, in UTC
    time: datetime
    #: The version of the event schema format
    version: str
