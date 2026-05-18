from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.codebuild import (
    Build,
    BuildManager,
    Project,
    ProjectManager,
    Webhook,
    WebhookManager,
)


class FakePaginator:
    """Minimal paginator stub matching boto3 paginator protocol."""

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses

    def paginate(self, **_: object) -> list[dict[str, object]]:
        return self.responses


def _minimal_project_payload(name: str) -> dict[str, object]:
    """Return a minimal project payload suitable for :class:`Project` construction."""
    return {
        "name": name,
        "arn": f"arn:aws:codebuild:us-west-2:123456789012:project/{name}",
        "source": {"type": "NO_SOURCE"},
        "artifacts": {"type": "NO_ARTIFACTS"},
        "environment": {
            "type": "LINUX_CONTAINER",
            "image": "aws/codebuild/standard:7.0",
            "computeType": "BUILD_GENERAL1_SMALL",
        },
        "serviceRole": "arn:aws:iam::123456789012:role/CodeBuildServiceRole",
    }


def _minimal_build_payload(build_id: str, project_name: str) -> dict[str, object]:
    """Return a minimal build payload suitable for :class:`Build` construction."""
    return {
        "id": build_id,
        "arn": f"arn:aws:codebuild:us-west-2:123456789012:build/{build_id}",
        "projectName": project_name,
        "buildStatus": "SUCCEEDED",
    }


class TestProjectManager:
    @patch("boto3.client")
    def test_get_project_returns_model(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.batch_get_projects.return_value = {
            "projects": [_minimal_project_payload("demo")],
        }
        mock_boto3_client.return_value = mock_client

        manager = ProjectManager()
        project = manager.get("demo")

        mock_client.batch_get_projects.assert_called_once_with(names=["demo"])
        assert isinstance(project, Project)
        assert project.pk == "demo"
        assert str(project.arn or "").endswith("project/demo")

    @patch("boto3.client")
    def test_list_projects_hydrates_names(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_paginator.return_value = FakePaginator(
            [{"projects": ["demo"]}],
        )
        mock_client.batch_get_projects.return_value = {
            "projects": [_minimal_project_payload("demo")],
        }
        mock_boto3_client.return_value = mock_client

        manager = ProjectManager()
        projects = manager.list()

        mock_client.get_paginator.assert_called_once_with("list_projects")
        mock_client.batch_get_projects.assert_called_once_with(names=["demo"])
        assert isinstance(projects, PrimaryBoto3ModelQuerySet)
        assert len(projects) == 1
        assert isinstance(projects[0], Project)
        assert projects[0].pk == "demo"


class TestBuildManager:
    @patch("boto3.client")
    def test_list_for_project_hydrates_build_ids(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_paginator.return_value = FakePaginator(
            [{"ids": ["b1"]}],
        )
        mock_client.batch_get_builds.return_value = {
            "builds": [_minimal_build_payload("b1", "demo")],
        }
        mock_boto3_client.return_value = mock_client

        manager = BuildManager()
        builds = manager.list_for_project("demo")

        mock_client.get_paginator.assert_called_once_with("list_builds_for_project")
        mock_client.batch_get_builds.assert_called_once_with(ids=["b1"])
        assert isinstance(builds, PrimaryBoto3ModelQuerySet)
        assert len(builds) == 1
        assert isinstance(builds[0], Build)
        assert builds[0].id == "b1"
        assert builds[0].projectName == "demo"


class TestWebhookManager:
    @patch("boto3.client")
    def test_create_webhook_attaches_project_name(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_webhook.return_value = {
            "webhook": {
                "url": "https://example.com/webhook",
                "payloadUrl": "https://codebuild.example.com/webhook",
            },
        }
        mock_boto3_client.return_value = mock_client

        manager = WebhookManager()
        model = Webhook(
            projectName="demo",
            branchFilter="main",
            filterGroups=[],
        )
        webhook = manager.create(model)

        mock_client.create_webhook.assert_called_once()
        call_kwargs = mock_client.create_webhook.call_args.kwargs
        assert call_kwargs["projectName"] == "demo"
        assert isinstance(webhook, Webhook)
        assert webhook.projectName == "demo"
        assert webhook.url == "https://example.com/webhook"
