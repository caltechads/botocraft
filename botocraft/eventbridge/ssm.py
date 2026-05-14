from typing import Any, Protocol

from . import raw as raw_ssm
from .base import EventBridgeEvent


def _first_resource(resources: list[str]) -> str | None:
    """
    Return the first resource ARN from an event payload.

    Args:
        resources: Resource ARNs carried on the EventBridge event.

    Returns:
        The first resource ARN when present, otherwise ``None``.

    """
    if not resources:
        return None
    return resources[0]


class _EventSummaryProtocol(Protocol):
    """
    Structural type for the EventBridge metadata used in summary rendering.
    """

    #: AWS account that emitted the event.
    account: str
    #: Event source identifier.
    source: str
    #: Timestamp when EventBridge recorded the event.
    time: Any
    #: AWS region where the event was emitted.
    region: str
    #: Resources associated with the event.
    resources: list[str]


#: Index of the second resource in an EventBridge resources list.
SECOND_RESOURCE_INDEX = 1
#: Minimum resource count needed to safely read a second resource ARN.
SECOND_RESOURCE_COUNT = 2


def _second_resource(resources: list[str]) -> str | None:
    """
    Return the second resource ARN from an event payload.

    Args:
        resources: Resource ARNs carried on the EventBridge event.

    Returns:
        The second resource ARN when present, otherwise ``None``.

    """
    if len(resources) < SECOND_RESOURCE_COUNT:
        return None
    return resources[SECOND_RESOURCE_INDEX]


def _event_summary(
    event_name: str,
    event: _EventSummaryProtocol,
    **details: object,
) -> str:
    """
    Build a readable string representation for an SSM event wrapper.

    Args:
        event_name: Human-readable event name shown in the summary.
        event: Event instance being rendered.

    Keyword Args:
        details: Extra event-specific fields to append to the summary.

    Returns:
        Compact summary string for the event.

    """
    parts = [
        f"account={event.account}",
        f"source={event.source}",
        f"time={event.time}",
        f"region={event.region}",
        f"resources={event.resources}",
    ]
    parts.extend(
        f"{name}={value}"
        for name, value in details.items()
        if value is not None and value != ""
    )
    return f"<Event: {event_name}: " + ", ".join(parts) + ">"


class SSMCalendarStateChangeEvent(
    EventBridgeEvent,
    raw_ssm.SSMCalendarStateChangeEvent,
):
    """
    EventBridge event for Systems Manager calendar state changes.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the calendar state transition event.

        """
        return _event_summary(
            "SSM Calendar State Change",
            self,
            state=self.detail.state,
            next_transition_time=self.detail.nextTransitionTime,
        )

    @property
    def calendar_arn(self) -> str | None:
        """
        Return the calendar ARN carried by the event resources list.

        Returns:
            Calendar ARN when the event names one resource, otherwise ``None``.

        """
        return _first_resource(self.resources)

    @property
    def is_open(self) -> bool:
        """
        Check whether the calendar is currently open.

        Returns:
            ``True`` when the event reports an ``OPEN`` state.

        """
        return self.detail.state.upper() == "OPEN"

    @property
    def is_closed(self) -> bool:
        """
        Check whether the calendar is currently closed.

        Returns:
            ``True`` when the event reports a ``CLOSED`` state.

        """
        return self.detail.state.upper() == "CLOSED"


class SSMEC2AutomationStepStatusChangeNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMEC2AutomationStepStatusChangeNotificationEvent,
):
    """
    EventBridge event for an SSM Automation step status change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the automation step status event.

        """
        return _event_summary(
            "SSM EC2 Automation Step Status-change Notification",
            self,
            execution_id=self.detail.ExecutionId,
            definition=self.detail.Definition,
            step_name=self.detail.StepName,
            status=self.detail.Status,
        )

    @property
    def automation_execution_arn(self) -> str | None:
        """
        Return the Automation execution ARN named by the event.

        Returns:
            Execution ARN when the first resource is present, otherwise ``None``.

        """
        return _first_resource(self.resources)

    @property
    def automation_definition_arn(self) -> str | None:
        """
        Return the Automation definition ARN named by the event.

        Returns:
            Definition ARN when the second resource is present, otherwise ``None``.

        """
        return _second_resource(self.resources)


class SSMEC2AutomationExecutionStatusChangeNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMEC2AutomationExecutionStatusChangeNotificationEvent,
):
    """
    EventBridge event for an SSM Automation execution status change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the automation execution status event.

        """
        return _event_summary(
            "SSM EC2 Automation Execution Status-change Notification",
            self,
            execution_id=self.detail.ExecutionId,
            definition=self.detail.Definition,
            status=self.detail.Status,
            executed_by=self.detail.ExecutedBy,
        )

    @property
    def automation_execution_arn(self) -> str | None:
        """
        Return the Automation execution ARN named by the event.

        Returns:
            Execution ARN when the first resource is present, otherwise ``None``.

        """
        return _first_resource(self.resources)

    @property
    def automation_definition_arn(self) -> str | None:
        """
        Return the Automation definition ARN named by the event.

        Returns:
            Definition ARN when the second resource is present, otherwise ``None``.

        """
        return _second_resource(self.resources)


class SSMChangeRequestStatusUpdateEvent(
    EventBridgeEvent,
    raw_ssm.SSMChangeRequestStatusUpdateEvent,
):
    """
    EventBridge event for an SSM Change Manager request status update.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the change request status event.

        """
        return _event_summary(
            "SSM Change Request Status Update",
            self,
            change_request_id=self.detail.change_request_id,
            ops_item_id=self.detail.ops_item_id,
            status=self.detail.ops_item_status,
        )

    @property
    def ops_item_arn(self) -> str | None:
        """
        Return the OpsItem ARN named by the event.

        Returns:
            OpsItem ARN when the first resource is present, otherwise ``None``.

        """
        return _first_resource(self.resources)

    @property
    def runbook_document_arn(self) -> str:
        """
        Return the runbook ARN recorded in the event detail.

        Returns:
            Runbook document ARN from the event payload.

        """
        return self.detail.runbook_document_arn


class SSMConfigurationComplianceStateChangeEvent(
    EventBridgeEvent,
    raw_ssm.SSMConfigurationComplianceStateChangeEvent,
):
    """
    EventBridge event for an SSM compliance state change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the compliance state change event.

        """
        return _event_summary(
            "SSM Configuration Compliance State Change",
            self,
            compliance_type=self.detail.compliance_type,
            compliance_status=self.detail.compliance_status,
            resource_id=self.detail.resource_id,
        )

    @property
    def resource_arn(self) -> str | None:
        """
        Return the managed resource ARN named by the event.

        Returns:
            Resource ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)

    @property
    def is_compliant(self) -> bool:
        """
        Check whether the reported compliance state is compliant.

        Returns:
            ``True`` when the event status is ``compliant``.

        """
        return self.detail.compliance_status.lower() == "compliant"


class SSMMaintenanceWindowTargetRegistrationNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMMaintenanceWindowTargetRegistrationNotificationEvent,
):
    """
    EventBridge event for an SSM maintenance window target registration change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the target registration event.

        """
        return _event_summary(
            "SSM Maintenance Window Target Registration Notification",
            self,
            window_id=self.detail.window_id,
            window_target_id=self.detail.window_target_id,
            status=self.detail.status,
        )

    @property
    def maintenance_window_arn(self) -> str | None:
        """
        Return the maintenance window ARN named by the event.

        Returns:
            Maintenance window ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)

    @property
    def window_target_arn(self) -> str | None:
        """
        Return the maintenance window target ARN named by the event.

        Returns:
            Target ARN when the second resource is present, otherwise ``None``.

        """
        return _second_resource(self.resources)


class SSMMaintenanceWindowExecutionStateChangeNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMMaintenanceWindowExecutionStateChangeNotificationEvent,
):
    """
    EventBridge event for an SSM maintenance window execution state change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the maintenance window execution event.

        """
        return _event_summary(
            "SSM Maintenance Window Execution State-change Notification",
            self,
            window_id=self.detail.window_id,
            window_execution_id=self.detail.window_execution_id,
            status=self.detail.status,
        )

    @property
    def maintenance_window_arn(self) -> str | None:
        """
        Return the maintenance window ARN named by the event.

        Returns:
            Maintenance window ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMMaintenanceWindowTaskExecutionStateChangeNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMMaintenanceWindowTaskExecutionStateChangeNotificationEvent,
):
    """
    EventBridge event for an SSM maintenance window task execution state change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the maintenance window task execution event.

        """
        return _event_summary(
            "SSM Maintenance Window Task Execution State-change Notification",
            self,
            window_id=self.detail.window_id,
            task_execution_id=self.detail.task_execution_id,
            status=self.detail.status,
        )

    @property
    def maintenance_window_arn(self) -> str | None:
        """
        Return the maintenance window ARN named by the event.

        Returns:
            Maintenance window ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMMaintenanceWindowTaskTargetInvocationStateChangeNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMMaintenanceWindowTaskTargetInvocationStateChangeNotificationEvent,
):
    """
    EventBridge event for an SSM maintenance window task target invocation state change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the maintenance window task target invocation event.

        """
        return _event_summary(
            "SSM Maintenance Window Task Target Invocation State-change Notification",
            self,
            window_id=self.detail.window_id,
            task_execution_id=self.detail.task_execution_id,
            window_target_id=self.detail.window_target_id,
            status=self.detail.status,
        )

    @property
    def maintenance_window_arn(self) -> str | None:
        """
        Return the maintenance window ARN named by the event.

        Returns:
            Maintenance window ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMMaintenanceWindowStateChangeNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMMaintenanceWindowStateChangeNotificationEvent,
):
    """
    EventBridge event for an SSM maintenance window state change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the maintenance window state change event.

        """
        return _event_summary(
            "SSM Maintenance Window State-change Notification",
            self,
            window_id=self.detail.window_id,
            status=self.detail.status,
        )

    @property
    def maintenance_window_arn(self) -> str | None:
        """
        Return the maintenance window ARN named by the event.

        Returns:
            Maintenance window ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMParameterStoreChangeEvent(
    EventBridgeEvent,
    raw_ssm.SSMParameterStoreChangeEvent,
):
    """
    EventBridge event for an SSM Parameter Store change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the parameter store change event.

        """
        return _event_summary(
            "SSM Parameter Store Change",
            self,
            operation=self.detail.operation,
            parameter_name=self.detail.name,
            parameter_type=self.detail.type,
        )

    @property
    def parameter_arn(self) -> str | None:
        """
        Return the Parameter Store ARN named by the event.

        Returns:
            Parameter ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMOpsItemCreateEvent(
    EventBridgeEvent,
    raw_ssm.SSMOpsItemCreateEvent,
):
    """
    EventBridge event for OpsCenter OpsItem creation.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the OpsItem creation event.

        """
        return _event_summary(
            "SSM OpsItem Create",
            self,
            ops_item_id=self.detail.ops_item_id,
            status=self.detail.status,
            title=self.detail.title,
        )

    @property
    def ops_item_arn(self) -> str | None:
        """
        Return the OpsItem ARN named by the event.

        Returns:
            OpsItem ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMOpsItemUpdateEvent(
    EventBridgeEvent,
    raw_ssm.SSMOpsItemUpdateEvent,
):
    """
    EventBridge event for OpsCenter OpsItem updates.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the OpsItem update event.

        """
        return _event_summary(
            "SSM OpsItem Update",
            self,
            ops_item_id=self.detail.ops_item_id,
            status=self.detail.status,
            title=self.detail.title,
        )

    @property
    def ops_item_arn(self) -> str | None:
        """
        Return the OpsItem ARN named by the event.

        Returns:
            OpsItem ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMEC2CommandStatusChangeNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMEC2CommandStatusChangeNotificationEvent,
):
    """
    EventBridge event for an SSM Run Command status change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the command status event.

        """
        return _event_summary(
            "SSM EC2 Command Status-change Notification",
            self,
            command_id=self.detail.command_id,
            document_name=self.detail.document_name,
            status=self.detail.status,
        )

    @property
    def instance_arn(self) -> str | None:
        """
        Return the instance ARN named by the event.

        Returns:
            Instance ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMEC2CommandInvocationStatusChangeNotificationEvent(
    EventBridgeEvent,
    raw_ssm.SSMEC2CommandInvocationStatusChangeNotificationEvent,
):
    """
    EventBridge event for an SSM Run Command invocation status change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the command invocation event.

        """
        return _event_summary(
            "SSM EC2 Command Invocation Status-change Notification",
            self,
            command_id=self.detail.command_id,
            document_name=self.detail.document_name,
            instance_id=self.detail.instance_id,
            status=self.detail.status,
        )

    @property
    def instance_arn(self) -> str | None:
        """
        Return the instance ARN named by the event.

        Returns:
            Instance ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMEC2StateManagerAssociationStateChangeEvent(
    EventBridgeEvent,
    raw_ssm.SSMEC2StateManagerAssociationStateChangeEvent,
):
    """
    EventBridge event for an SSM State Manager association state change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the association state change event.

        """
        return _event_summary(
            "SSM EC2 State Manager Association State Change",
            self,
            association_id=self.detail.association_id,
            document_name=self.detail.document_name,
            status=self.detail.status,
        )

    @property
    def document_arn(self) -> str | None:
        """
        Return the SSM document ARN named by the event.

        Returns:
            Document ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)


class SSMEC2StateManagerInstanceAssociationStateChangeEvent(
    EventBridgeEvent,
    raw_ssm.SSMEC2StateManagerInstanceAssociationStateChangeEvent,
):
    """
    EventBridge event for an SSM State Manager instance association state change.
    """

    def __str__(self) -> str:
        """
        Return a readable string representation of the event.

        Returns:
            Summary string for the instance association state change event.

        """
        return _event_summary(
            "SSM EC2 State Manager Instance Association State Change",
            self,
            association_id=self.detail.association_id,
            instance_id=self.detail.instance_id,
            document_name=self.detail.document_name,
            status=self.detail.status,
        )

    @property
    def instance_arn(self) -> str | None:
        """
        Return the instance ARN named by the event.

        Returns:
            Instance ARN when one is present, otherwise ``None``.

        """
        return _first_resource(self.resources)

    @property
    def document_arn(self) -> str | None:
        """
        Return the SSM document ARN named by the event.

        Returns:
            Document ARN when the second resource is present, otherwise ``None``.

        """
        return _second_resource(self.resources)


#: Declarative mapping from EventBridge source/detail-type pairs to wrappers.
EVENT_CLASS_MAP = {
    (
        "aws.ssm",
        "EC2 Automation Step Status-change Notification",
    ): SSMEC2AutomationStepStatusChangeNotificationEvent,
    (
        "aws.ssm",
        "EC2 Automation Execution Status-change Notification",
    ): SSMEC2AutomationExecutionStatusChangeNotificationEvent,
    ("aws.ssm", "Calendar State Change"): SSMCalendarStateChangeEvent,
    ("aws.ssm", "Change Request Status Update"): SSMChangeRequestStatusUpdateEvent,
    (
        "aws.ssm",
        "Configuration Compliance State Change",
    ): SSMConfigurationComplianceStateChangeEvent,
    (
        "aws.ssm",
        "Maintenance Window Target Registration Notification",
    ): SSMMaintenanceWindowTargetRegistrationNotificationEvent,
    (
        "aws.ssm",
        "Maintenance Window Execution State-change Notification",
    ): SSMMaintenanceWindowExecutionStateChangeNotificationEvent,
    (
        "aws.ssm",
        "Maintenance Window Task Execution State-change Notification",
    ): SSMMaintenanceWindowTaskExecutionStateChangeNotificationEvent,
    (
        "aws.ssm",
        "Maintenance Window Task Target Invocation State-change Notification",
    ): SSMMaintenanceWindowTaskTargetInvocationStateChangeNotificationEvent,
    (
        "aws.ssm",
        "Maintenance Window State-change Notification",
    ): SSMMaintenanceWindowStateChangeNotificationEvent,
    ("aws.ssm", "Parameter Store Change"): SSMParameterStoreChangeEvent,
    ("aws.ssm", "OpsItem Create"): SSMOpsItemCreateEvent,
    ("aws.ssm", "OpsItem Update"): SSMOpsItemUpdateEvent,
    (
        "aws.ssm",
        "EC2 Command Status-change Notification",
    ): SSMEC2CommandStatusChangeNotificationEvent,
    (
        "aws.ssm",
        "EC2 Command Invocation Status-change Notification",
    ): SSMEC2CommandInvocationStatusChangeNotificationEvent,
    (
        "aws.ssm",
        "EC2 State Manager Association State Change",
    ): SSMEC2StateManagerAssociationStateChangeEvent,
    (
        "aws.ssm",
        "EC2 State Manager Instance Association State Change",
    ): SSMEC2StateManagerInstanceAssociationStateChangeEvent,
}
