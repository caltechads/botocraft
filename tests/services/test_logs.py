from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import WaiterError

from botocraft.services.logs import (
    GetQueryResultsResponse,
    LogGroup,
    LogGroupManager,
    QueryDefinition,
    QueryDefinitionManager,
    StartQueryResponse,
)


class TestLogGroupInsightsManager:
    @patch("boto3.client")
    def test_start_query(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.start_query.return_value = {"queryId": "query-123"}
        mock_boto3_client.return_value = mock_client

        manager = LogGroupManager()
        response = manager.start_query(
            startTime=1_700_000_000,
            endTime=1_700_003_600,
            queryString="fields @message | limit 20",
            logGroupNames=["/aws/lambda/my-function"],
        )

        mock_client.start_query.assert_called_once_with(
            startTime=1_700_000_000,
            endTime=1_700_003_600,
            queryString="fields @message | limit 20",
            logGroupNames=["/aws/lambda/my-function"],
        )
        assert isinstance(response, StartQueryResponse)
        assert response.queryId == "query-123"

    @patch("boto3.client")
    def test_get_query_results(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.get_query_results.return_value = {
            "status": "Complete",
            "results": [[{"field": "@message", "value": "error"}]],
            "statistics": {"recordsMatched": 1.0, "recordsScanned": 10.0},
        }
        mock_boto3_client.return_value = mock_client

        manager = LogGroupManager()
        response = manager.get_query_results(queryId="query-123")

        mock_client.get_query_results.assert_called_once_with(queryId="query-123")
        assert isinstance(response, GetQueryResultsResponse)
        assert response.status == "Complete"
        assert response.results is not None
        assert response.results[0][0].field == "@message"

    @patch("boto3.client")
    def test_wait_for_query_results(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.get_query_results.side_effect = [
            {"status": "Running", "results": []},
            {
                "status": "Complete",
                "results": [[{"field": "@message", "value": "done"}]],
            },
        ]
        mock_boto3_client.return_value = mock_client

        manager = LogGroupManager()
        with patch("botocraft.mixins.logs.time.sleep"):
            response = manager.wait_for_query_results(
                "query-123",
                poll_interval=0.01,
                max_attempts=5,
            )

        assert response.status == "Complete"
        assert mock_client.get_query_results.call_count == 2

    @patch("boto3.client")
    def test_wait_for_query_results_times_out(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.get_query_results.return_value = {
            "status": "Running",
            "results": [],
        }
        mock_boto3_client.return_value = mock_client

        manager = LogGroupManager()
        with (
            patch("botocraft.mixins.logs.time.sleep"),
            pytest.raises(WaiterError),
        ):
            manager.wait_for_query_results(
                "query-123",
                poll_interval=0.01,
                max_attempts=2,
            )

    @patch("boto3.client")
    def test_run_query(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.start_query.return_value = {"queryId": "query-456"}
        mock_client.get_query_results.side_effect = [
            {"status": "Running", "results": []},
            {
                "status": "Complete",
                "results": [[{"field": "@message", "value": "one"}]],
                "statistics": {"recordsMatched": 1.0, "bytesScanned": 100.0},
                "nextToken": "page-2",
            },
            {
                "status": "Complete",
                "results": [[{"field": "@message", "value": "two"}]],
                "statistics": {"recordsMatched": 2.0, "bytesScanned": 200.0},
            },
        ]
        mock_boto3_client.return_value = mock_client

        manager = LogGroupManager()
        with patch("botocraft.mixins.logs.time.sleep"):
            rows, stats = manager.run_query(
                queryString="fields @message",
                logGroupNames=["/ecs/my-service"],
                startTime=1_700_000_000,
                endTime=1_700_003_600,
                poll_interval=0.01,
            )

        mock_client.start_query.assert_called_once()
        assert len(rows) == 2
        assert rows[0][0].value == "one"
        assert rows[1][0].value == "two"
        assert stats is not None
        assert stats.bytesScanned == 200.0


class TestLogGroupInstanceMethods:
    @patch.object(LogGroupManager, "get_fields")
    def test_get_fields_delegates_to_manager_with_log_group_name(
        self,
        mock_get_fields: MagicMock,
    ) -> None:
        log_group = LogGroup(
            Arn="arn:aws:logs:us-east-1:123456789012:log-group:/ecs/my-service:*",
            logGroupName="/ecs/my-service",
        )
        mock_get_fields.return_value = []

        log_group.get_fields(time=1_700_000_000)

        mock_get_fields.assert_called_once_with(
            logGroupName="/ecs/my-service",
            time=1_700_000_000,
        )

    @patch.object(LogGroupManager, "start_query")
    def test_start_query_delegates_to_manager_with_log_group_name(
        self,
        mock_start_query: MagicMock,
    ) -> None:
        log_group = LogGroup(
            Arn="arn:aws:logs:us-east-1:123456789012:log-group:/ecs/my-service:*",
            logGroupName="/ecs/my-service",
        )
        mock_start_query.return_value = StartQueryResponse(queryId="query-abc")

        response = log_group.start_query(
            1_700_000_000,
            1_700_003_600,
            "fields @message | limit 20",
            queryLanguage="CWLI",
            limit=20,
        )

        mock_start_query.assert_called_once_with(
            1_700_000_000,
            1_700_003_600,
            "fields @message | limit 20",
            logGroupName="/ecs/my-service",
            queryLanguage="CWLI",
            limit=20,
        )
        assert response.queryId == "query-abc"

    @patch.object(LogGroupManager, "get_query_results")
    def test_get_query_results_delegates_to_manager(
        self,
        mock_get_query_results: MagicMock,
    ) -> None:
        log_group = LogGroup(
            Arn="arn:aws:logs:us-east-1:123456789012:log-group:/ecs/my-service:*",
            logGroupName="/ecs/my-service",
        )
        mock_get_query_results.return_value = GetQueryResultsResponse(
            status="Complete",
            results=[],
        )

        response = log_group.get_query_results(
            "query-abc",
            nextToken="page-2",
            maxItems=100,
        )

        mock_get_query_results.assert_called_once_with(
            "query-abc",
            nextToken="page-2",
            maxItems=100,
        )
        assert response.status == "Complete"


class TestQueryDefinitionManager:
    @patch("boto3.client")
    def test_create_hydrates_definition(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.put_query_definition.return_value = {
            "queryDefinitionId": "qd-1",
        }
        mock_client.describe_query_definitions.return_value = {
            "queryDefinitions": [
                {
                    "queryDefinitionId": "qd-1",
                    "name": "errors",
                    "queryString": "fields @message | filter @message like /ERROR/",
                    "logGroupNames": ["/ecs/my-service"],
                }
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = QueryDefinitionManager()
        model = QueryDefinition(
            name="errors",
            queryString="fields @message | filter @message like /ERROR/",
            logGroupNames=["/ecs/my-service"],
        )
        created = manager.create(model)

        mock_client.put_query_definition.assert_called_once()
        assert isinstance(created, QueryDefinition)
        assert created.queryDefinitionId == "qd-1"
        assert created.name == "errors"

    @patch("boto3.client")
    def test_list_paginates_all_definitions(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.describe_query_definitions.side_effect = [
            {
                "queryDefinitions": [
                    {
                        "queryDefinitionId": "qd-1",
                        "name": "one",
                        "queryString": "fields @timestamp",
                    }
                ],
                "nextToken": "token-2",
            },
            {
                "queryDefinitions": [
                    {
                        "queryDefinitionId": "qd-2",
                        "name": "two",
                        "queryString": "stats count()",
                    }
                ],
            },
        ]
        mock_boto3_client.return_value = mock_client

        manager = QueryDefinitionManager()
        results = manager.list()

        assert mock_client.describe_query_definitions.call_count == 2
        assert len(results) == 2
        assert results[0].queryDefinitionId == "qd-1"
        assert results[1].queryDefinitionId == "qd-2"

    @patch("boto3.client")
    def test_get_finds_definition_across_pages(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.describe_query_definitions.side_effect = [
            {
                "queryDefinitions": [
                    {
                        "queryDefinitionId": "qd-1",
                        "name": "one",
                        "queryString": "fields @timestamp",
                    }
                ],
                "nextToken": "token-2",
            },
            {
                "queryDefinitions": [
                    {
                        "queryDefinitionId": "qd-2",
                        "name": "two",
                        "queryString": "stats count()",
                    }
                ],
            },
        ]
        mock_boto3_client.return_value = mock_client

        manager = QueryDefinitionManager()
        found = manager.get("qd-2")

        assert found is not None
        assert found.queryDefinitionId == "qd-2"
        assert found.name == "two"

    @patch("boto3.client")
    def test_delete(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = QueryDefinitionManager()
        manager.delete(queryDefinitionId="qd-9")

        mock_client.delete_query_definition.assert_called_once_with(
            queryDefinitionId="qd-9"
        )

    @patch("boto3.client")
    def test_start_query_from_definition(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.start_query.return_value = {"queryId": "query-789"}
        mock_boto3_client.return_value = mock_client

        manager = QueryDefinitionManager()
        definition = QueryDefinition(
            queryDefinitionId="qd-1",
            name="errors",
            queryString="fields @message | filter @message like /ERROR/",
            logGroupNames=["/ecs/my-service"],
            queryLanguage="CWLI",
        )
        response = manager.start_query(
            definition,
            startTime=1_700_000_000,
            endTime=1_700_003_600,
            limit=50,
        )

        mock_client.start_query.assert_called_once_with(
            queryString="fields @message | filter @message like /ERROR/",
            startTime=1_700_000_000,
            endTime=1_700_003_600,
            logGroupNames=["/ecs/my-service"],
            queryLanguage="CWLI",
            limit=50,
        )
        assert isinstance(response, StartQueryResponse)
        assert response.queryId == "query-789"
