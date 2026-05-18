from collections import OrderedDict
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.codepipeline import (
    ActionType,
    ActionTypeManager,
    Pipeline,
    PipelineExecution,
    PipelineExecutionManager,
    PipelineManager,
)


class FakePaginator:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses

    def paginate(self, **_: object) -> list[dict[str, object]]:
        return self.responses


class TestPipelineManager:
    @patch("boto3.client")
    def test_get_pipeline_returns_pipeline_model(self, mock_boto3_client) -> None:
        mock_client = MagicMock()
        mock_client.get_pipeline.return_value = {
            "pipeline": {
                "name": "demo",
                "roleArn": "arn:aws:iam::123456789012:role/DemoPipeline",
                "stages": [{"name": "Source", "actions": []}],
                "version": 3,
                "pipelineType": "V2",
                "executionMode": "PARALLEL",
            },
            "metadata": {
                "pipelineArn": (
                    "arn:aws:codepipeline:us-west-2:123456789012:demo"
                ),
            },
        }
        mock_boto3_client.return_value = mock_client

        manager = PipelineManager()
        pipeline = manager.get("demo")

        mock_client.get_pipeline.assert_called_once_with(name="demo")
        assert isinstance(pipeline, Pipeline)
        assert pipeline.pipelineName == "demo"
        assert pipeline.roleArn == "arn:aws:iam::123456789012:role/DemoPipeline"
        assert pipeline.pipelineArn == "arn:aws:codepipeline:us-west-2:123456789012:demo"

    @patch("boto3.client")
    def test_list_pipelines_returns_queryset(self, mock_boto3_client) -> None:
        mock_client = MagicMock()
        mock_client.get_paginator.return_value = FakePaginator(
            [
                {
                    "pipelines": [
                        {
                            "name": "demo",
                            "version": 3,
                            "pipelineType": "V2",
                            "executionMode": "PARALLEL",
                        }
                    ]
                }
            ]
        )
        mock_client.get_pipeline.return_value = {
            "pipeline": {
                "name": "demo",
                "roleArn": "arn:aws:iam::123456789012:role/DemoPipeline",
                "stages": [{"name": "Source", "actions": []}],
                "version": 3,
                "pipelineType": "V2",
                "executionMode": "PARALLEL",
            },
            "metadata": {
                "pipelineArn": (
                    "arn:aws:codepipeline:us-west-2:123456789012:demo"
                ),
            },
        }
        mock_boto3_client.return_value = mock_client

        manager = PipelineManager()
        pipelines = manager.list()

        mock_client.get_paginator.assert_called_once_with("list_pipelines")
        mock_client.get_pipeline.assert_called_once_with(name="demo")
        assert isinstance(pipelines, PrimaryBoto3ModelQuerySet)
        assert len(pipelines) == 1
        assert isinstance(pipelines[0], Pipeline)
        assert pipelines[0].pipelineName == "demo"
        assert pipelines[0].version == 3
        assert pipelines[0].roleArn == "arn:aws:iam::123456789012:role/DemoPipeline"
        assert pipelines[0].pipelineArn == (
            "arn:aws:codepipeline:us-west-2:123456789012:demo"
        )

    @patch("boto3.client")
    def test_list_pipelines_version_pins_get_pipeline(
        self, mock_boto3_client
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_paginator.return_value = FakePaginator(
            [
                {
                    "pipelines": [
                        {
                            "name": "demo",
                            "version": 9,
                            "pipelineType": "V2",
                            "executionMode": "PARALLEL",
                        }
                    ]
                }
            ]
        )
        mock_client.get_pipeline.return_value = {
            "pipeline": {
                "name": "demo",
                "roleArn": "arn:aws:iam::123456789012:role/DemoPipeline",
                "stages": [{"name": "Source", "actions": []}],
                "version": 3,
                "pipelineType": "V2",
                "executionMode": "PARALLEL",
            },
            "metadata": {
                "pipelineArn": (
                    "arn:aws:codepipeline:us-west-2:123456789012:demo"
                ),
            },
        }
        mock_boto3_client.return_value = mock_client

        manager = PipelineManager()
        pipelines = manager.list(version=3)

        mock_client.get_pipeline.assert_called_once_with(name="demo", version=3)
        assert isinstance(pipelines, PrimaryBoto3ModelQuerySet)
        assert len(pipelines) == 1
        assert pipelines[0].version == 3

    @patch("boto3.client")
    def test_create_pipeline_wraps_model_payload(self, mock_boto3_client) -> None:
        mock_client = MagicMock()
        mock_client.create_pipeline.return_value = {
            "pipeline": {
                "name": "demo",
                "roleArn": "arn:aws:iam::123456789012:role/DemoPipeline",
                "stages": [{"name": "Source", "actions": []}],
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = PipelineManager()
        pipeline = Pipeline(
            name="demo",
            roleArn="arn:aws:iam::123456789012:role/DemoPipeline",
            stages=[{"name": "Source", "actions": []}],
            version=3,
            pipelineType="V2",
            executionMode="PARALLEL",
            pipelineArn="arn:aws:codepipeline:us-west-2:123456789012:demo",
        )

        created = manager.create(pipeline)

        mock_client.create_pipeline.assert_called_once_with(
            pipeline={
                "name": "demo",
                "roleArn": "arn:aws:iam::123456789012:role/DemoPipeline",
                "stages": [{"name": "Source", "blockers": [], "actions": []}],
                "version": 3,
                "executionMode": "PARALLEL",
                "pipelineType": "V2",
            }
        )
        assert isinstance(created, Pipeline)
        assert created.pipelineName == "demo"


class TestPipelineExecutionManager:
    @patch("boto3.client")
    def test_list_pipeline_executions_restores_pipeline_name(
        self,
        mock_boto3_client,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_paginator.return_value = FakePaginator(
            [
                {
                    "pipelineExecutionSummaries": [
                        {
                            "pipelineExecutionId": (
                                "11111111-2222-3333-4444-555555555555"
                            ),
                            "status": "Succeeded",
                        }
                    ]
                }
            ]
        )
        mock_boto3_client.return_value = mock_client

        manager = PipelineExecutionManager()
        executions = manager.list(pipelineName="demo")

        assert isinstance(executions, PrimaryBoto3ModelQuerySet)
        assert len(executions) == 1
        assert isinstance(executions[0], PipelineExecution)
        assert executions[0].pipelineName == "demo"
        assert executions[0].pk == OrderedDict(
            {
                "pipelineName": "demo",
                "pipelineExecutionId": "11111111-2222-3333-4444-555555555555",
            }
        )


class TestActionTypeManager:
    @patch("boto3.client")
    def test_get_action_type_returns_flattened_model(self, mock_boto3_client) -> None:
        mock_client = MagicMock()
        mock_client.get_action_type.return_value = {
            "actionType": {
                "id": {
                    "category": "Deploy",
                    "owner": "AWS",
                    "provider": "CodeDeploy",
                    "version": "1",
                },
                "executor": {
                    "type": "Lambda",
                    "configuration": {
                        "lambdaExecutorConfiguration": {
                            "lambdaFunctionArn": (
                                "arn:aws:lambda:us-west-2:123456789012:function:test"
                            )
                        }
                    },
                },
                "inputArtifactDetails": {"minimumCount": 0, "maximumCount": 1},
                "outputArtifactDetails": {"minimumCount": 0, "maximumCount": 1},
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = ActionTypeManager()
        action_type = manager.get(
            category="Deploy",
            owner="AWS",
            provider="CodeDeploy",
            version="1",
        )

        mock_client.get_action_type.assert_called_once_with(
            category="Deploy",
            owner="AWS",
            provider="CodeDeploy",
            version="1",
        )
        assert isinstance(action_type, ActionType)
        assert action_type.id.owner == "AWS"
        assert action_type.executor is not None
        assert action_type.executor["type"] == "Lambda"
        assert action_type.pk == OrderedDict(
            {
                "category": "Deploy",
                "provider": "CodeDeploy",
                "version": "1",
            }
        )
