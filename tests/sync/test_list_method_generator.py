from botocraft.sync.methods.manager.list import ListMethodGenerator
from botocraft.sync.models import BotocraftInterface
from botocraft.sync.service import ServiceGenerator


def build_list_method_generator(
    service_name: str, model_name: str
) -> ListMethodGenerator:
    interface = BotocraftInterface()
    interface.load()
    service = interface.services[service_name]
    generator = ServiceGenerator(service)
    generator.model_generator.generate_all_service_models()
    manager_def = service.managers[model_name]
    return ListMethodGenerator(
        generator.manager_generator,
        model_name,
        manager_def.methods["list"],
    )


def test_paginated_list_body_does_not_stop_on_empty_page() -> None:
    """
    An empty page can still carry a token (``nextToken``, ``Marker``, ...), so
    the generated loop must leave ending the iteration to the paginator.
    """
    generator = build_list_method_generator("bedrock-agentcore-control", "AgentRuntime")

    body = generator.body

    assert "paginator.paginate" in body
    assert "NextToken" not in body
    # Only the ResponseMetadata-only guard may break out of the loop.
    assert body.count("break") == 1


def test_list_return_type_names_the_model_class() -> None:
    generator = build_list_method_generator("bedrock-agentcore-control", "AgentRuntime")

    assert generator.queryset_item_type == "AgentCoreAgentRuntime"
    assert generator.return_type == 'PrimaryBoto3ModelQuerySet["AgentCoreAgentRuntime"]'


def test_typed_list_body_returns_queryset_without_runtime_type_check() -> None:
    generator = build_list_method_generator("bedrock-agentcore-control", "AgentRuntime")

    body = generator.body

    assert 'results: "builtins.list[AgentCoreAgentRuntime]" = []' in body
    assert "return PrimaryBoto3ModelQuerySet(results)" in body
    assert "isinstance(results[0]" not in body
