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


def _get_response(**overrides: Any) -> dict[str, Any]:
    """
    Return a ``GetAgentRuntime`` response, with no ``description`` by default.

    AWS omits ``description`` for runtimes created without one (for example
    commons-module runtimes), so it is absent unless a caller adds it.
    """
    response: dict[str, Any] = {
        "agentRuntimeArn": ARN,
        "agentRuntimeId": RUNTIME_ID,
        "agentRuntimeVersion": "1",
        "agentRuntimeName": "example_runtime",
        "createdAt": UPDATED,
        "lastUpdatedAt": UPDATED,
        "roleArn": "arn:aws:iam::000000000000:role/example",
        "status": "READY",
        "lifecycleConfiguration": {},
    }
    response.update(overrides)
    return response


def test_get_without_description(stubbed) -> None:
    manager, stubber = stubbed
    stubber.add_response(
        "get_agent_runtime", _get_response(), {"agentRuntimeId": RUNTIME_ID}
    )

    runtime = manager.get(RUNTIME_ID)

    assert runtime is not None
    assert runtime.agentRuntimeId == RUNTIME_ID
    assert runtime.description is None


ROLE = "arn:aws:iam::000000000000:role/example"
CLIENT_TOKEN = "t" * 36
ARTIFACT = {"containerConfiguration": {"containerUri": "uri"}}
NETWORK = {"networkMode": "PUBLIC"}


def _runtime(**overrides: Any) -> AgentCoreAgentRuntime:
    """Return a runtime with the fields create and update require."""
    fields: dict[str, Any] = {
        "agentRuntimeArn": ARN,
        "agentRuntimeId": RUNTIME_ID,
        "agentRuntimeVersion": "1",
        "agentRuntimeName": "example_runtime",
        "lastUpdatedAt": UPDATED,
        "status": "READY",
        "createdAt": UPDATED,
        "roleArn": ROLE,
        "agentRuntimeArtifact": ARTIFACT,
        "networkConfiguration": NETWORK,
    }
    fields.update(overrides)
    return AgentCoreAgentRuntime(**fields)


def _update_response() -> dict[str, Any]:
    """Return the fields ``UpdateAgentRuntime`` requires on its response."""
    return {
        "agentRuntimeArn": ARN,
        "agentRuntimeId": RUNTIME_ID,
        "agentRuntimeVersion": "1",
        "createdAt": UPDATED,
        "lastUpdatedAt": UPDATED,
        "status": "UPDATING",
    }


def _create_response() -> dict[str, Any]:
    """Return the fields ``CreateAgentRuntime`` requires on its response."""
    return {
        "agentRuntimeArn": ARN,
        "agentRuntimeId": RUNTIME_ID,
        "agentRuntimeVersion": "1",
        "createdAt": UPDATED,
        "status": "CREATING",
    }


def _base_write_params() -> dict[str, Any]:
    """Return the write fields a runtime holds besides the empty containers."""
    return {
        "agentRuntimeArtifact": ARTIFACT,
        "roleArn": ROLE,
        "networkConfiguration": NETWORK,
    }


def test_update_omits_empty_containers(stubbed) -> None:
    manager, stubber = stubbed
    expected = {
        **_base_write_params(),
        "agentRuntimeId": RUNTIME_ID,
        "clientToken": CLIENT_TOKEN,
    }
    stubber.add_response("update_agent_runtime", _update_response(), expected)

    manager.update(_runtime(), clientToken=CLIENT_TOKEN)


def test_update_sends_allowed_ports(stubbed) -> None:
    manager, stubber = stubbed
    ports = [{"port": 8080}]
    expected = {
        **_base_write_params(),
        "agentRuntimeId": RUNTIME_ID,
        "allowedPorts": ports,
        "clientToken": CLIENT_TOKEN,
    }
    stubber.add_response("update_agent_runtime", _update_response(), expected)

    manager.update(_runtime(allowedPorts=ports), clientToken=CLIENT_TOKEN)


def test_create_omits_empty_containers(stubbed) -> None:
    manager, stubber = stubbed
    expected = {
        **_base_write_params(),
        "agentRuntimeName": "example_runtime",
    }
    stubber.add_response("create_agent_runtime", _create_response(), expected)

    manager.create(_runtime())


def test_create_sends_allowed_ports(stubbed) -> None:
    manager, stubber = stubbed
    ports = [{"port": 8080}]
    expected = {
        **_base_write_params(),
        "agentRuntimeName": "example_runtime",
        "allowedPorts": ports,
    }
    stubber.add_response("create_agent_runtime", _create_response(), expected)

    manager.create(_runtime(allowedPorts=ports))


def test_update_omits_empty_environment_variables(stubbed) -> None:
    manager, stubber = stubbed
    expected = {
        **_base_write_params(),
        "agentRuntimeId": RUNTIME_ID,
        "clientToken": CLIENT_TOKEN,
    }
    stubber.add_response("update_agent_runtime", _update_response(), expected)

    manager.update(_runtime(environmentVariables={}), clientToken=CLIENT_TOKEN)


def test_update_sends_environment_variables(stubbed) -> None:
    manager, stubber = stubbed
    variables = {"LOG_LEVEL": "INFO"}
    expected = {
        **_base_write_params(),
        "agentRuntimeId": RUNTIME_ID,
        "environmentVariables": variables,
        "clientToken": CLIENT_TOKEN,
    }
    stubber.add_response("update_agent_runtime", _update_response(), expected)

    manager.update(_runtime(environmentVariables=variables), clientToken=CLIENT_TOKEN)


def test_get_without_ports_then_update_omits_empty_defaults(stubbed) -> None:
    manager, stubber = stubbed
    stubber.add_response(
        "get_agent_runtime",
        _get_response(agentRuntimeArtifact=ARTIFACT, networkConfiguration=NETWORK),
        {"agentRuntimeId": RUNTIME_ID},
    )
    expected = {
        **_base_write_params(),
        "agentRuntimeId": RUNTIME_ID,
        "lifecycleConfiguration": {},
        "clientToken": CLIENT_TOKEN,
    }
    stubber.add_response("update_agent_runtime", _update_response(), expected)

    runtime = manager.get(RUNTIME_ID)

    assert runtime is not None
    manager.update(runtime, clientToken=CLIENT_TOKEN)


def test_get_then_update_sends_only_held_values(stubbed) -> None:
    manager, stubber = stubbed
    stubber.add_response(
        "get_agent_runtime",
        _get_response(
            agentRuntimeArtifact=ARTIFACT,
            networkConfiguration=NETWORK,
            allowedPorts=[{"port": 8080}],
        ),
        {"agentRuntimeId": RUNTIME_ID},
    )
    expected = {
        **_base_write_params(),
        "agentRuntimeId": RUNTIME_ID,
        "allowedPorts": [{"port": 8080}],
        "lifecycleConfiguration": {},
        "clientToken": CLIENT_TOKEN,
    }
    stubber.add_response("update_agent_runtime", _update_response(), expected)

    runtime = manager.get(RUNTIME_ID)

    assert runtime is not None
    manager.update(runtime, clientToken=CLIENT_TOKEN)


def test_get_with_description(stubbed) -> None:
    manager, stubber = stubbed
    stubber.add_response(
        "get_agent_runtime",
        _get_response(description="hello"),
        {"agentRuntimeId": RUNTIME_ID},
    )

    runtime = manager.get(RUNTIME_ID)

    assert runtime is not None
    assert runtime.description == "hello"
