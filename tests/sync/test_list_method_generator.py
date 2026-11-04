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
