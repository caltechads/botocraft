from botocraft.sync.models import BotocraftInterface, ModelDefinition
from botocraft.sync.service import ModelGenerator, ServiceGenerator


def build_model_generator() -> ModelGenerator:
    interface = BotocraftInterface()
    interface.load()
    service = interface.services["ecs"]
    return ServiceGenerator(service).model_generator


def test_primary_model_skips_computed_name_property_for_real_name_field() -> None:
    generator = build_model_generator()
    model_def = ModelDefinition(
        name="CapacityProvider",
        primary_key="capacityProviderArn",
        arn_key="capacityProviderArn",
        name_key="name",
    )

    properties = generator.get_properties(
        model_def,
        "PrimaryBoto3Model",
        model_field_names={"name", "capacityProviderArn"},
    )

    assert properties is not None
    assert "def pk(self)" in properties
    assert "def arn(self)" in properties
    assert "def name(self)" not in properties


def test_primary_model_keeps_computed_name_property_for_other_name_keys() -> None:
    generator = build_model_generator()
    model_def = ModelDefinition(
        name="Service",
        primary_key="serviceArn",
        arn_key="serviceArn",
        name_key="serviceName",
    )

    properties = generator.get_properties(
        model_def,
        "PrimaryBoto3Model",
        model_field_names={"serviceArn", "serviceName"},
    )

    assert properties is not None
    assert "def pk(self)" in properties
    assert "def arn(self)" in properties
    assert "def name(self)" in properties
    assert "return self.serviceName" in properties


def test_primary_model_skips_computed_arn_property_for_real_arn_field() -> None:
    generator = build_model_generator()
    model_def = ModelDefinition(
        name="CapacityProvider",
        primary_key="id",
        arn_key="arn",
    )

    properties = generator.get_properties(
        model_def,
        "PrimaryBoto3Model",
        model_field_names={"arn", "id"},
    )

    assert properties is not None
    assert "def pk(self)" in properties
    assert "def arn(self)" not in properties


def test_primary_model_keeps_computed_arn_property_for_other_arn_keys() -> None:
    generator = build_model_generator()
    model_def = ModelDefinition(
        name="Service",
        primary_key="serviceArn",
        arn_key="serviceArn",
    )

    properties = generator.get_properties(
        model_def,
        "PrimaryBoto3Model",
        model_field_names={"serviceArn"},
    )

    assert properties is not None
    assert "def pk(self)" in properties
    assert "def arn(self)" in properties
    assert "return self.serviceArn" in properties
