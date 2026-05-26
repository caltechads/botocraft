import json
from unittest.mock import MagicMock, patch

import pytest

from botocraft.eventbridge.codepipeline import (
    CodePipelineActionExecutionStateChangeEvent,
    CodePipelineAWSAPICallViaCloudTrailEvent,
    CodePipelinePipelineExecutionStateChangeEvent,
    CodePipelineStageExecutionStateChangeEvent,
)
from botocraft.eventbridge.factory import EventFactory


def _event_payload(
    detail_type: str,
    detail: dict[str, object],
    *,
    resources: list[str] | None = None,
) -> dict[str, object]:
    return {
        "version": "0",
        "id": "01234567-0123-0123-0123-0123456789ab",
        "detail-type": detail_type,
        "source": "aws.codepipeline",
        "account": "123456789012",
        "time": "2024-11-16T00:58:37Z",
        "region": "us-west-2",
        "resources": resources
        or ["arn:aws:codepipeline:us-west-2:123456789012:myPipeline"],
        "detail": detail,
    }


@pytest.mark.parametrize(
    ("payload", "expected_type"),
    [
        (
            _event_payload(
                "AWS API Call via CloudTrail",
                {
                    "eventVersion": "1.11",
                    "userIdentity": {
                        "type": "AssumedRole",
                        "principalId": "EXAMPLE:session",
                        "arn": (
                            "arn:aws:sts::123456789012:assumed-role/"
                            "Admin/session"
                        ),
                    },
                    "eventTime": "2026-03-07T00:51:06Z",
                    "eventSource": "codepipeline.amazonaws.com",
                    "eventName": "StartPipelineExecution",
                    "awsRegion": "us-west-2",
                    "sourceIPAddress": "192.0.2.1",
                    "userAgent": "aws-cli/2.33.13",
                    "requestParameters": {
                        "name": "myPipeline",
                    },
                    "responseElements": {
                        "pipelineExecutionId": (
                            "11111111-2222-3333-4444-555555555555"
                        ),
                    },
                    "requestID": "a1b2c3d4-5678-90ab-cdef-EXAMPLE55555",
                    "eventID": "a1b2c3d4-5678-90ab-cdef-EXAMPLE66666",
                    "readOnly": False,
                    "resources": [
                        {
                            "type": "AWS::CodePipeline::Pipeline",
                            "ARN": (
                                "arn:aws:codepipeline:us-west-2:"
                                "123456789012:myPipeline"
                            ),
                        }
                    ],
                    "eventType": "AwsApiCall",
                    "apiVersion": "2015-07-09",
                    "managementEvent": True,
                    "recipientAccountId": "123456789012",
                    "eventCategory": "Management",
                },
            ),
            CodePipelineAWSAPICallViaCloudTrailEvent,
        ),
        (
            _event_payload(
                "CodePipeline Pipeline Execution State Change",
                {
                    "pipeline": "myPipeline",
                    "execution-id": "12345678-1234-5678-abcd-12345678abcd",
                    "execution-trigger": {
                        "trigger-type": "StartPipelineExecution",
                        "trigger-detail": (
                            "arn:aws:sts::123456789012:assumed-role/Admin/test"
                        ),
                    },
                    "start-time": "2023-10-26T13:49:39.208Z",
                    "pipeline-execution-attempt": 1.0,
                    "state": "STARTED",
                    "version": 3.0,
                },
            ),
            CodePipelinePipelineExecutionStateChangeEvent,
        ),
        (
            _event_payload(
                "CodePipeline Stage Execution State Change",
                {
                    "pipeline": "myPipeline",
                    "execution-id": "12345678-1234-5678-abcd-12345678abcd",
                    "start-time": "2023-10-26T13:51:09.981Z",
                    "pipeline-execution-attempt": 1.0,
                    "stage": "Deploy",
                    "state": "SUCCEEDED",
                    "version": 3.0,
                },
            ),
            CodePipelineStageExecutionStateChangeEvent,
        ),
        (
            _event_payload(
                "CodePipeline Action Execution State Change",
                {
                    "pipeline": "myPipeline",
                    "execution-id": "12345678-1234-5678-abcd-12345678abcd",
                    "action-execution-id": "47f821c5-a902-44b2-ae61-b878d31ecd21",
                    "start-time": "2023-10-26T13:51:09.981Z",
                    "pipeline-execution-attempt": 1.0,
                    "stage": "Deploy",
                    "action": "Deploy",
                    "state": "FAILED",
                    "region": "us-west-2",
                    "type": {
                        "owner": "AWS",
                        "provider": "CodeDeploy",
                        "category": "Deploy",
                        "version": "1",
                    },
                    "version": 4.0,
                    "input-artifacts": [
                        {
                            "name": "SourceArtifact",
                            "s3location": {
                                "bucket": "codepipeline-us-west-2-EXAMPLE",
                                "key": "myPipeline/SourceArti/EXAMPLE",
                            },
                        }
                    ],
                    "output-artifacts": [
                        {
                            "name": "BuildArtifact",
                            "s3location": {
                                "bucket": "codepipeline-us-west-2-EXAMPLE",
                                "key": "myPipeline/BuildArti/EXAMPLE",
                            },
                        }
                    ],
                    "execution-result": {
                        "external-execution-id": "deployment-123",
                        "external-execution-summary": "Deployment failed",
                        "external-execution-url": (
                            "https://console.aws.amazon.com/codedeploy/"
                        ),
                    },
                },
            ),
            CodePipelineActionExecutionStateChangeEvent,
        ),
    ],
)
def test_event_factory_builds_codepipeline_events(
    payload: dict[str, object],
    expected_type: type[object],
) -> None:
    event = EventFactory().new(json.dumps(payload))
    assert isinstance(event, expected_type)


@patch("botocraft.services.codepipeline.PipelineExecution.objects")
@patch("botocraft.services.codepipeline.Pipeline.objects")
def test_codepipeline_event_loads_related_models(
    mock_pipeline_objects: MagicMock,
    mock_pipeline_execution_objects: MagicMock,
) -> None:
    session = MagicMock()
    pipeline_model = MagicMock(name="pipeline-model")
    execution_model = MagicMock(name="execution-model")
    mock_pipeline_manager = MagicMock()
    mock_pipeline_execution_manager = MagicMock()
    mock_pipeline_manager.get.return_value = pipeline_model
    mock_pipeline_execution_manager.get.return_value = execution_model
    mock_pipeline_objects.using.return_value = mock_pipeline_manager
    mock_pipeline_execution_objects.using.return_value = (
        mock_pipeline_execution_manager
    )

    event = EventFactory(session=session).new(
        json.dumps(
            _event_payload(
                "CodePipeline Stage Execution State Change",
                {
                    "pipeline": "myPipeline",
                    "execution-id": "12345678-1234-5678-abcd-12345678abcd",
                    "start-time": "2023-10-26T13:51:09.981Z",
                    "pipeline-execution-attempt": 1.0,
                    "stage": "Deploy",
                    "state": "STARTED",
                    "version": 3.0,
                },
            )
        )
    )

    assert isinstance(event, CodePipelineStageExecutionStateChangeEvent)
    assert event.pipeline_arn == (
        "arn:aws:codepipeline:us-west-2:123456789012:myPipeline"
    )
    assert event.pipeline is pipeline_model
    assert event.pipeline_execution is execution_model
    mock_pipeline_objects.using.assert_called_once_with(session)
    mock_pipeline_manager.get.assert_called_once_with("myPipeline")
    mock_pipeline_execution_objects.using.assert_called_once_with(session)
    mock_pipeline_execution_manager.get.assert_called_once_with(
        "myPipeline",
        "12345678-1234-5678-abcd-12345678abcd",
    )


@patch("botocraft.services.codepipeline.Pipeline.objects")
def test_codepipeline_cloudtrail_event_loads_pipeline(
    mock_pipeline_objects: MagicMock,
) -> None:
    session = MagicMock()
    pipeline_model = MagicMock(name="pipeline-model")
    mock_pipeline_manager = MagicMock()
    mock_pipeline_manager.get.return_value = pipeline_model
    mock_pipeline_objects.using.return_value = mock_pipeline_manager

    event = EventFactory(session=session).new(
        json.dumps(
            _event_payload(
                "AWS API Call via CloudTrail",
                {
                    "eventVersion": "1.11",
                    "eventTime": "2026-03-07T00:51:06Z",
                    "eventSource": "codepipeline.amazonaws.com",
                    "eventName": "StartPipelineExecution",
                    "awsRegion": "us-west-2",
                },
            )
        )
    )

    assert isinstance(event, CodePipelineAWSAPICallViaCloudTrailEvent)
    assert event.pipeline_arn == (
        "arn:aws:codepipeline:us-west-2:123456789012:myPipeline"
    )
    assert event.pipeline is pipeline_model
    mock_pipeline_objects.using.assert_called_once_with(session)
    mock_pipeline_manager.get.assert_called_once_with("myPipeline")
