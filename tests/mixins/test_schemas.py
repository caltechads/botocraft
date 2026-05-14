from botocraft.mixins.schemas import (
    schema_list_add_registry_name,
    schema_response_to_schema,
)
from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.schemas import DescribeSchemaResponse, Schema


class DummyManager:
    def __init__(self) -> None:
        self.sessionized: list[object] = []

    def sessionize(self, value: object) -> None:
        self.sessionized.append(value)


def test_schema_response_to_schema_preserves_registry_name() -> None:
    manager = DummyManager()

    @schema_response_to_schema
    def get_schema(*_, **__) -> DescribeSchemaResponse | None:
        return DescribeSchemaResponse(
            SchemaArn="arn:aws:schemas:us-west-2:123456789012:schema/test",
            SchemaName="aws.test.SomeEvent",
            SchemaVersion="3",
            Type="OpenApi3",
        )

    schema = get_schema(
        manager,
        RegistryName="aws.events",
        SchemaName="aws.test.SomeEvent",
    )

    assert isinstance(schema, Schema)
    assert schema.RegistryName == "aws.events"
    assert manager.sessionized == [schema]


def test_schema_list_add_registry_name_marks_each_result() -> None:
    manager = DummyManager()
    query_set = PrimaryBoto3ModelQuerySet(
        [
            Schema(
                RegistryName="placeholder",
                SchemaArn="arn:aws:schemas:us-west-2:123456789012:schema/test-1",
                SchemaName="aws.test.First",
            ),
            Schema(
                RegistryName="placeholder",
                SchemaArn="arn:aws:schemas:us-west-2:123456789012:schema/test-2",
                SchemaName="aws.test.Second",
            ),
        ]
    )

    @schema_list_add_registry_name
    def list_schemas(*_, **__) -> PrimaryBoto3ModelQuerySet:
        return query_set

    results = list_schemas(
        manager,
        RegistryName="aws.events",
        SchemaNamePrefix="aws.test",
    )

    assert [schema.RegistryName for schema in results.results] == [
        "aws.events",
        "aws.events",
    ]
