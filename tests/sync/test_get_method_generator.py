from botocraft.sync.methods.manager.get import GetMethodGenerator
from botocraft.sync.models import BotocraftInterface
from botocraft.sync.service import ServiceGenerator


def build_get_method_generator(
    service_name: str, model_name: str
) -> GetMethodGenerator:
    interface = BotocraftInterface()
    interface.load()
    service = interface.services[service_name]
    generator = ServiceGenerator(service)
    manager_def = service.managers[model_name]
    return GetMethodGenerator(
        generator.manager_generator,
        model_name,
        manager_def.methods["get"],
    )


def test_get_response_class_uses_explicit_wrapper_model() -> None:
    generator = build_get_method_generator("events", "Rule")

    assert generator.response_class == "DescribeRuleResponse"
    assert "DescribeRuleResponse" in generator.model_generator.classes


def test_get_response_class_keeps_primary_model_when_explicit_type_matches() -> None:
    generator = build_get_method_generator("events", "EventBus")

    assert generator.response_class == "EventBus"
    assert "EventBus" in generator.model_generator.classes
