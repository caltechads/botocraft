from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, Field


class Detail(BaseModel):
    """
    Detail payload for this SSM event.
    """

    #: Event field ``association-id``.
    association_id: str = Field(..., alias="association-id")
    #: Event field ``document-name``.
    document_name: str = Field(..., alias="document-name")
    #: Event field ``association-version``.
    association_version: str = Field(..., alias="association-version")
    #: Event field ``document-version``.
    document_version: str = Field(..., alias="document-version")
    #: Event field ``targets``.
    targets: str
    #: Event field ``creation-date``.
    creation_date: AwareDatetime = Field(..., alias="creation-date")
    #: Event field ``last_successful_execution_date``.
    last_successful_execution_date: AwareDatetime = Field(
        ..., alias="last-successful-execution-date"
    )
    #: Event field ``last-execution-date``.
    last_execution_date: AwareDatetime = Field(..., alias="last-execution-date")
    #: Event field ``last-updated-date``.
    last_updated_date: AwareDatetime = Field(..., alias="last-updated-date")
    #: Event field ``status``.
    status: str
    #: Event field ``association_status_aggregated_count``.
    association_status_aggregated_count: str = Field(
        ..., alias="association-status-aggregated-count"
    )
    #: Event field ``schedule-expression``.
    schedule_expression: str = Field(..., alias="schedule-expression")
    #: Event field ``association-cwe-version``.
    association_cwe_version: str = Field(..., alias="association-cwe-version")


class SSMEC2StateManagerAssociationStateChangeEvent(BaseModel):
    """
    Raw EventBridge payload for this SSM event.
    """

    #: EventBridge payload version.
    version: str
    #: Unique identifier for the EventBridge event.
    id: str
    #: EventBridge detail type for the event.
    detail_type: str = Field(..., alias="detail-type")
    #: Event source identifier.
    source: str
    #: AWS account that emitted the event.
    account: str
    #: Timestamp when EventBridge recorded the event.
    time: AwareDatetime
    #: AWS region where the event was emitted.
    region: str
    #: Resources associated with the event.
    resources: list[str]
    #: Event-specific detail payload from Systems Manager.
    detail: Detail
