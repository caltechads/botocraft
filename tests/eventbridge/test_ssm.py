import json

import pytest

from botocraft.eventbridge.factory import EventFactory
from botocraft.eventbridge.ssm import (
    SSMChangeRequestStatusUpdateEvent,
    SSMConfigurationComplianceStateChangeEvent,
    SSMEC2AutomationExecutionStatusChangeNotificationEvent,
    SSMEC2AutomationStepStatusChangeNotificationEvent,
    SSMEC2CommandInvocationStatusChangeNotificationEvent,
    SSMEC2CommandStatusChangeNotificationEvent,
    SSMEC2StateManagerAssociationStateChangeEvent,
    SSMEC2StateManagerInstanceAssociationStateChangeEvent,
    SSMMaintenanceWindowExecutionStateChangeNotificationEvent,
    SSMMaintenanceWindowStateChangeNotificationEvent,
    SSMMaintenanceWindowTargetRegistrationNotificationEvent,
    SSMMaintenanceWindowTaskExecutionStateChangeNotificationEvent,
    SSMMaintenanceWindowTaskTargetInvocationStateChangeNotificationEvent,
    SSMOpsItemCreateEvent,
    SSMOpsItemUpdateEvent,
    SSMParameterStoreChangeEvent,
)


def _event_payload(
    detail_type: str,
    detail: dict[str, object],
    *,
    resources: list[str] | None = None,
    region: str = "us-east-2",
) -> dict[str, object]:
    return {
        "version": "0",
        "id": "01234567-0123-0123-0123-0123456789ab",
        "detail-type": detail_type,
        "source": "aws.ssm",
        "account": "123456789012",
        "time": "2024-11-16T00:58:37Z",
        "region": region,
        "resources": resources or [],
        "detail": detail,
    }


@pytest.mark.parametrize(
    ("payload", "expected_type"),
    [
        (
            _event_payload(
                "EC2 Automation Step Status-change Notification",
                {
                    "ExecutionId": "333ba70b-2333-48db-b17e-a5e69c6f4d1c",
                    "Definition": "runcommand1",
                    "DefinitionVersion": 1.0,
                    "Status": "Success",
                    "EndTime": "Nov 29, 2024 7:43:25 PM",
                    "StartTime": "Nov 29, 2024 7:43:23 PM",
                    "Time": 2630.0,
                    "StepName": "runFixedCmds",
                    "Action": "aws:runCommand",
                },
                resources=[
                    (
                        "arn:aws:ssm:us-east-2:123456789012:"
                        "automation-execution/333ba70b-2333-48db-b17e-a5e69c6f4d1c"
                    ),
                    (
                        "arn:aws:ssm:us-east-2:123456789012:"
                        "automation-definition/runcommand1:1"
                    ),
                ],
            ),
            SSMEC2AutomationStepStatusChangeNotificationEvent,
        ),
        (
            _event_payload(
                "EC2 Automation Execution Status-change Notification",
                {
                    "ExecutionId": "333ba70b-2333-48db-b17e-a5e69c6f4d1c",
                    "Definition": "runcommand1",
                    "DefinitionVersion": 1.0,
                    "Status": "Success",
                    "StartTime": "Nov 29, 2024 7:43:20 PM",
                    "EndTime": "Nov 29, 2024 7:43:26 PM",
                    "Time": 5753.0,
                    "ExecutedBy": "arn:aws:iam::123456789012:user/userName",
                },
                resources=[
                    (
                        "arn:aws:ssm:us-east-2:123456789012:"
                        "automation-execution/333ba70b-2333-48db-b17e-a5e69c6f4d1c"
                    ),
                    (
                        "arn:aws:ssm:us-east-2:123456789012:"
                        "automation-definition/runcommand1:1"
                    ),
                ],
            ),
            SSMEC2AutomationExecutionStatusChangeNotificationEvent,
        ),
        (
            _event_payload(
                "Change Request Status Update",
                {
                    "change-request-id": "d0585556-80f6-4522-8dad-dada6d45b67d",
                    "change-request-title": "A change request title",
                    "ops-item-id": "oi-12345abcdef",
                    "ops-item-created-by": "arn:aws:iam::123456789012:user/JohnDoe",
                    "ops-item-created-time": "2024-10-24T10:50:33.180334Z",
                    "ops-item-modified-by": "arn:aws:iam::123456789012:user/JohnDoe",
                    "ops-item-modified-time": "2024-10-24T10:50:33.180340Z",
                    "ops-item-status": "InProgress",
                    "change-template-document-name": "MyChangeTemplate",
                    "runbook-document-arn": (
                        "arn:aws:ssm:us-west-2:123456789012:document/MyRunbook1"
                    ),
                    "runbook-document-version": "1",
                    "auto-approve": True,
                    "approvers": [
                        "arn:aws:iam::123456789012:user/JaneDoe",
                    ],
                },
                resources=[
                    "arn:aws:ssm:us-west-2:123456789012:opsitem/oi-12345abcdef",
                    "arn:aws:ssm:us-west-2:123456789012:document/MyRunbook1",
                ],
                region="us-east-1",
            ),
            SSMChangeRequestStatusUpdateEvent,
        ),
        (
            _event_payload(
                "Configuration Compliance State Change",
                {
                    "last-runtime": "2024-01-01T10:10:10Z",
                    "compliance-status": "compliant",
                    "resource-type": "managed-instance",
                    "resource-id": "i-01234567890abcdef",
                    "compliance-type": "Association",
                    "patch-baseline-id": "PB789",
                    "severity": "critical",
                },
                resources=[
                    (
                        "arn:aws:ssm:us-east-2:123456789012:"
                        "managed-instance/i-01234567890abcdef"
                    )
                ],
            ),
            SSMConfigurationComplianceStateChangeEvent,
        ),
        (
            _event_payload(
                "Maintenance Window Target Registration Notification",
                {
                    "window-target-id": "e7265f13-3cc5-4f2f-97a9-7d3ca86c32a6",
                    "window-id": "mw-0ed7251d3fcf6e0c2",
                    "status": "REGISTERED",
                },
                resources=[
                    (
                        "arn:aws:ssm:us-east-2:123456789012:"
                        "maintenancewindow/mw-0ed7251d3fcf6e0c2"
                    ),
                    (
                        "arn:aws:ssm:us-east-2:123456789012:"
                        "windowtarget/e7265f13-3cc5-4f2f-97a9-7d3ca86c32a6"
                    ),
                ],
            ),
            SSMMaintenanceWindowTargetRegistrationNotificationEvent,
        ),
        (
            _event_payload(
                "Maintenance Window Execution State-change Notification",
                {
                    "start-time": "2025-06-02T14:48:28.039273Z",
                    "end-time": "2025-06-02T14:52:18.083773Z",
                    "window-id": "mw-0ed7251d3fcf6e0c2",
                    "window-execution-id": "14bea65d-5ccc-462d-a2f3-e99c8EXAMPLE",
                    "status": "SUCCESS",
                },
                resources=[
                    "arn:aws:ssm:us-east-2:123456789012:maintenancewindow/mw-0c50858d01EXAMPLE"
                ],
            ),
            SSMMaintenanceWindowExecutionStateChangeNotificationEvent,
        ),
        (
            _event_payload(
                "Maintenance Window Task Execution State-change Notification",
                {
                    "start-time": "2025-06-02T14:48:28.039273Z",
                    "task-execution-id": "6417e808-7f35-4d1a-843f-123456789012",
                    "end-time": "2025-06-02T14:52:18.083773Z",
                    "window-id": "mw-0ed7251d3fcf6e0c2",
                    "window-execution-id": "14bea65d-5ccc-462d-a2f3-e99c8EXAMPLE",
                    "status": "SUCCESS",
                },
                resources=[
                    "arn:aws:ssm:us-east-2:123456789012:maintenancewindow/mw-0c50858d01EXAMPLE"
                ],
            ),
            SSMMaintenanceWindowTaskExecutionStateChangeNotificationEvent,
        ),
        (
            _event_payload(
                "Maintenance Window Task Target Invocation State-change Notification",
                {
                    "start-time": "2025-06-02T14:48:28.039273Z",
                    "end-time": "2025-06-02T14:52:18.083773Z",
                    "window-id": "mw-0ed7251d3fcf6e0c2",
                    "window-execution-id": "791b72e0-f0da-4021-8b35-f95dfEXAMPLE",
                    "task-execution-id": "c9b05aba-197f-4d8d-be34-e73fbEXAMPLE",
                    "window-target-id": "e32eecb2-646c-4f4b-8ed1-205fbEXAMPLE",
                    "status": "SUCCESS",
                    "owner-information": "Owner",
                },
                resources=[
                    (
                        "arn:aws:ssm:us-east-2:123456789012:"
                        "maintenancewindow/mw-123456789012345678"
                    )
                ],
            ),
            SSMMaintenanceWindowTaskTargetInvocationStateChangeNotificationEvent,
        ),
        (
            _event_payload(
                "Maintenance Window State-change Notification",
                {
                    "window-id": "mw-0c50858d01EXAMPLE",
                    "status": "DISABLED",
                },
                resources=[
                    "arn:aws:ssm:us-east-2:123456789012:maintenancewindow/mw-0c50858d01EXAMPLE"
                ],
            ),
            SSMMaintenanceWindowStateChangeNotificationEvent,
        ),
        (
            _event_payload(
                "Parameter Store Change",
                {
                    "operation": "Create",
                    "name": "MyExampleParameter",
                    "type": "String",
                    "description": "Sample Parameter",
                },
                resources=[
                    "arn:aws:ssm:us-east-2:123456789012:parameter/MyExampleParameter"
                ],
            ),
            SSMParameterStoreChangeEvent,
        ),
        (
            _event_payload(
                "OpsItem Create",
                {
                    "created-by": "arn:aws:iam::123456789012:user/JohnDoe",
                    "created-time": "2024-10-19T02:46:53.629361Z",
                    "source": "aws.ssm",
                    "status": "Open",
                    "ops-item-id": "oi-123456abcdef",
                    "title": "An issue title",
                    "ops-item-type": "/aws/issue",
                    "description": "A long description may appear here",
                },
                resources=[
                    "arn:aws:ssm:us-west-2:123456789012:opsitem/oi-123456abcdef"
                ],
                region="us-east-1",
            ),
            SSMOpsItemCreateEvent,
        ),
        (
            _event_payload(
                "OpsItem Update",
                {
                    "created-by": "arn:aws:iam::123456789012:user/JohnDoe",
                    "created-time": "2024-10-19T02:46:54.049271Z",
                    "modified-by": "arn:aws:iam::123456789012:user/JohnDoe",
                    "modified-time": "2024-10-19T02:46:54.337354Z",
                    "source": "aws.ssm",
                    "status": "Open",
                    "ops-item-id": "oi-123456abcdef",
                    "title": "An issue title",
                    "ops-item-type": "/aws/issue",
                    "description": "A long description may appear here",
                },
                resources=[
                    "arn:aws:ssm:us-west-2:123456789012:opsitem/oi-123456abcdef"
                ],
                region="us-east-1",
            ),
            SSMOpsItemUpdateEvent,
        ),
        (
            _event_payload(
                "EC2 Command Status-change Notification",
                {
                    "command-id": "e8d3c0e4-71f7-4491-898f-c9b35bee5f3b",
                    "document-name": "AWS-RunPowerShellScript",
                    "expire-after": "2024-07-14T22:01:30.049Z",
                    "parameters": {
                        "executionTimeout": ["3600"],
                        "commands": ["date"],
                    },
                    "requested-date-time": "2024-07-10T21:51:30.049Z",
                    "status": "Success",
                },
                resources=[
                    "arn:aws:ec2:us-east-2:123456789012:instance/i-02573cafcfEXAMPLE"
                ],
            ),
            SSMEC2CommandStatusChangeNotificationEvent,
        ),
        (
            _event_payload(
                "EC2 Command Invocation Status-change Notification",
                {
                    "command-id": "e8d3c0e4-71f7-4491-898f-c9b35bee5f3b",
                    "document-name": "AWS-RunPowerShellScript",
                    "instance-id": "i-02573cafcfEXAMPLE",
                    "requested-date-time": "2024-07-10T21:51:30.049Z",
                    "status": "Success",
                },
                resources=[
                    "arn:aws:ec2:us-east-2:123456789012:instance/i-02573cafcfEXAMPLE"
                ],
            ),
            SSMEC2CommandInvocationStatusChangeNotificationEvent,
        ),
        (
            _event_payload(
                "EC2 State Manager Association State Change",
                {
                    "association-id": "6e37940a-23ba-4ab0-9b96-5d0a1a05464f",
                    "document-name": "AWS-RunPowerShellScript",
                    "association-version": "1",
                    "document-version": "Optional.empty",
                    "targets": '[{"key":"InstanceIds","values":["i-12345678"]}]',
                    "creation-date": "2024-02-13T17:22:54.458Z",
                    "last-successful-execution-date": "2024-05-16T23:00:01Z",
                    "last-execution-date": "2024-05-16T23:00:01Z",
                    "last-updated-date": "2024-02-13T17:22:54.458Z",
                    "status": "Success",
                    "association-status-aggregated-count": '{"Success":1}',
                    "schedule-expression": "cron(0 */30 * * * ? *)",
                    "association-cwe-version": "1.0",
                },
                resources=[
                    "arn:aws:ssm:us-east-2::document/AWS-RunPowerShellScript"
                ],
            ),
            SSMEC2StateManagerAssociationStateChangeEvent,
        ),
        (
            _event_payload(
                "EC2 State Manager Instance Association State Change",
                {
                    "association-id": "34fcb7e0-9a14-4984-9989-0e04e3f60bd8",
                    "instance-id": "i-02573cafcfEXAMPLE",
                    "document-name": "my-custom-document",
                    "document-version": "1",
                    "targets": (
                        '[{"key":"instanceids","values":["i-02573cafcfEXAMPLE"]}]'
                    ),
                    "creation-date": "2024-02-23T15:23:48Z",
                    "last-successful-execution-date": "2024-02-23T16:23:48Z",
                    "last-execution-date": "2024-02-23T16:23:48Z",
                    "status": "Success",
                    "detailed-status": "",
                    "error-code": "testErrorCode",
                    "execution-summary": "testExecutionSummary",
                    "output-url": "sampleurl",
                    "instance-association-cwe-version": "1",
                },
                resources=[
                    "arn:aws:ec2:us-east-2:123456789012:instance/i-12345678",
                    "arn:aws:ssm:us-east-2:123456789012:document/my-custom-document",
                ],
            ),
            SSMEC2StateManagerInstanceAssociationStateChangeEvent,
        ),
    ],
)
def test_event_factory_builds_documented_ssm_example_events(
    payload: dict[str, object],
    expected_type: type[object],
) -> None:
    event = EventFactory().new(json.dumps(payload))

    assert isinstance(event, expected_type)
