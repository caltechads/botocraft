from __future__ import annotations

from pydantic import BaseModel, Field


class Detail(BaseModel):
    """
    Detail payload for this SSM event.
    """

    #: Event field ``approvers``.
    approvers: list[str]
    #: Event field ``auto-approve``.
    auto_approve: bool = Field(..., alias="auto-approve")
    #: Event field ``change-request-id``.
    change_request_id: str = Field(..., alias="change-request-id")
    #: Event field ``change-request-title``.
    change_request_title: str = Field(..., alias="change-request-title")
    #: Event field ``change_template_document_name``.
    change_template_document_name: str = Field(
        ..., alias="change-template-document-name"
    )
    #: Event field ``ops-item-created-by``.
    ops_item_created_by: str = Field(..., alias="ops-item-created-by")
    #: Event field ``ops-item-created-time``.
    ops_item_created_time: str = Field(..., alias="ops-item-created-time")
    #: Event field ``ops-item-id``.
    ops_item_id: str = Field(..., alias="ops-item-id")
    #: Event field ``ops-item-modified-by``.
    ops_item_modified_by: str = Field(..., alias="ops-item-modified-by")
    #: Event field ``ops-item-modified-time``.
    ops_item_modified_time: str = Field(..., alias="ops-item-modified-time")
    #: Event field ``ops-item-status``.
    ops_item_status: str = Field(..., alias="ops-item-status")
    #: Event field ``runbook-document-arn``.
    runbook_document_arn: str = Field(..., alias="runbook-document-arn")
    #: Event field ``runbook-document-version``.
    runbook_document_version: str = Field(..., alias="runbook-document-version")


class SSMChangeRequestStatusUpdateEvent(BaseModel):
    """
    Raw EventBridge payload for this SSM event.
    """

    #: AWS account that emitted the event.
    account: str
    #: Event-specific detail payload from Systems Manager.
    detail: Detail
    #: EventBridge detail type for the event.
    detail_type: str = Field(..., alias="detail-type")
    #: Unique identifier for the EventBridge event.
    id: str
    #: AWS region where the event was emitted.
    region: str
    #: Resources associated with the event.
    resources: list[str]
    #: Event source identifier.
    source: str
    #: Timestamp when EventBridge recorded the event.
    time: str
    #: EventBridge payload version.
    version: str
