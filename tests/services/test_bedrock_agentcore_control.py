from datetime import datetime, timezone
from typing import Any, Iterator, cast

import pytest
from botocore.stub import Stubber

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.bedrock_agentcore_control import (
    AgentCoreAgentRuntime,
    AgentCoreAgentRuntimeManager,
)

RUNTIME_ID = "rt-example01"
ARN = "arn:aws:bedrock-agentcore:us-west-2:000000000000:runtime/rt-example01"
UPDATED = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def _version(number: str, status: str = "READY") -> dict[str, Any]:
    """Return one ``ListAgentRuntimeVersions`` item."""
    return {
        "agentRuntimeArn": ARN,
        "agentRuntimeId": RUNTIME_ID,
        "agentRuntimeVersion": number,
        "agentRuntimeName": "example_runtime",
        "description": f"version {number}",
        "lastUpdatedAt": UPDATED,
        "status": status,
    }


@pytest.fixture
def stubbed(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Any, Stubber]]:
    """Return a runtime manager whose client is stubbed, so no AWS call is made."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    manager = AgentCoreAgentRuntimeManager()
    with Stubber(manager.client) as stubber:
        yield manager, stubber
        stubber.assert_no_pending_responses()


def _add(stubber: Stubber, items: list[dict[str, Any]], token: str | None = None):
    response: dict[str, Any] = {"agentRuntimes": items}
    if token:
        response["nextToken"] = token
    expected: dict[str, Any] = {"agentRuntimeId": RUNTIME_ID}
    stubber.add_response("list_agent_runtime_versions", response, expected)


def test_list_versions_paginates_two_pages(stubbed) -> None:
    manager, stubber = stubbed
    stubber.add_response(
        "list_agent_runtime_versions",
        {"agentRuntimes": [_version("1"), _version("2")], "nextToken": "page2"},
        {"agentRuntimeId": RUNTIME_ID},
    )
    stubber.add_response(
        "list_agent_runtime_versions",
        {"agentRuntimes": [_version("3")]},
        {"agentRuntimeId": RUNTIME_ID, "nextToken": "page2"},
    )

    result = manager.list_versions(RUNTIME_ID)

    assert [v.agentRuntimeVersion for v in result] == ["1", "2", "3"]


def test_list_versions_empty_page_with_token_continues(stubbed) -> None:
    manager, stubber = stubbed
    stubber.add_response(
        "list_agent_runtime_versions",
        {"agentRuntimes": [], "nextToken": "page2"},
        {"agentRuntimeId": RUNTIME_ID},
    )
    stubber.add_response(
        "list_agent_runtime_versions",
        {"agentRuntimes": [_version("1")]},
        {"agentRuntimeId": RUNTIME_ID, "nextToken": "page2"},
    )

    result = manager.list_versions(RUNTIME_ID)

    assert [v.agentRuntimeVersion for v in result] == ["1"]


def test_list_versions_empty(stubbed) -> None:
    manager, stubber = stubbed
    _add(stubber, [])

    result = manager.list_versions(RUNTIME_ID)

    assert isinstance(result, PrimaryBoto3ModelQuerySet)
    assert len(result) == 0


def test_list_versions_returns_typed_models(stubbed) -> None:
    manager, stubber = stubbed
    _add(stubber, [_version("1"), _version("2", status="UPDATING")])

    result = manager.list_versions(RUNTIME_ID)

    assert isinstance(result, PrimaryBoto3ModelQuerySet)
    versions = cast("list[AgentCoreAgentRuntime]", list(result))
    assert all(isinstance(item, AgentCoreAgentRuntime) for item in versions)
    assert [v.status for v in versions] == ["READY", "UPDATING"]
    assert all(isinstance(v.lastUpdatedAt, datetime) for v in versions)


def test_list_versions_requires_runtime_id(stubbed) -> None:
    manager, _ = stubbed

    with pytest.raises(TypeError):
        manager.list_versions()
