from pathlib import Path
from typing import Callable, Sequence, cast

from click.testing import CliRunner

from botocraft.cli import cli
from botocraft.eventbridge.authoring import EventBridgeServiceExporter
from botocraft.services.abstract import (
    Boto3Model,
    PrimaryBoto3ModelQuerySet,
)


class FakeVersion:
    def __init__(self, schema_version: str) -> None:
        self.SchemaVersion = schema_version


class FakeSchema(Boto3Model):
    RegistryName: str
    SchemaName: str

    def versions(self) -> list[FakeVersion]:
        return [FakeVersion("1"), FakeVersion("3"), FakeVersion("2")]


class FakeExportResponse:
    def __init__(self, content: str, schema_version: str) -> None:
        self.Content = content
        self.SchemaVersion = schema_version


class FakeSchemaManager:
    def __init__(self, schemas_by_registry: dict[str, list[FakeSchema]]) -> None:
        self.schemas_by_registry = schemas_by_registry
        self.list_calls: list[tuple[str, str]] = []
        self.export_calls: list[tuple[str, str, str | None, str]] = []

    def list(
        self,
        *,
        RegistryName: str,  # noqa: N803
        SchemaNamePrefix: str,  # noqa: N803
    ) -> PrimaryBoto3ModelQuerySet:
        self.list_calls.append((RegistryName, SchemaNamePrefix))
        schemas = [
            schema
            for schema in self.schemas_by_registry.get(RegistryName, [])
            if schema.SchemaName.startswith(SchemaNamePrefix)
        ]
        return PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", schemas))

    def export(
        self,
        *,
        RegistryName: str,  # noqa: N803
        SchemaName: str,  # noqa: N803
        SchemaVersion: str | None,  # noqa: N803
        Type: str,  # noqa: N803
    ) -> FakeExportResponse:
        self.export_calls.append((RegistryName, SchemaName, SchemaVersion, Type))
        title = SchemaName.rsplit(".", maxsplit=1)[-1].replace(
            "AWSAPICallViaCloudTrail",
            "AWS API Call via CloudTrail",
        )
        content = (
            "{\n"
            f'  "title": "{title}",\n'
            '  "type": "object",\n'
            '  "properties": {\n'
            '    "detail": {\n'
            '      "type": "string"\n'
            "    }\n"
            "  }\n"
            "}\n"
        )
        return FakeExportResponse(content=content, schema_version=SchemaVersion or "3")


def fake_command_runner_factory(
) -> tuple[list[list[str]], Callable[[Sequence[str]], None]]:
    commands: list[list[str]] = []

    def run(command: Sequence[str]) -> None:
        command_list = list(command)
        commands.append(command_list)
        if command_list[0] == "datamodel-codegen":
            output_path = Path(command_list[command_list.index("--output") + 1])
            output_path.write_text(
                (
                    "from pydantic import BaseModel\n\n\n"
                    "class Event(BaseModel):\n"
                    "    detail: str | None = None\n"
                ),
                encoding="utf-8",
            )

    return commands, run


def test_eventbridge_export_service_uses_default_registry(
    monkeypatch,
    tmp_path,
) -> None:
    manager = FakeSchemaManager(
        {
            "aws.events": [
                FakeSchema(
                    RegistryName="aws.events",
                    SchemaName="aws.cloudtrail.AWSAPICallViaCloudTrail",
                ),
            ]
        }
    )
    commands, runner = fake_command_runner_factory()
    exporter = EventBridgeServiceExporter(schema_manager=manager, command_runner=runner)
    monkeypatch.setattr(
        "botocraft.cli.eventbridge.create_eventbridge_service_exporter",
        lambda: exporter,
    )

    result = CliRunner().invoke(
        cli,
        [
            "eventbridge",
            "export-service",
            "cloudtrail",
            "--raw-root",
            str(tmp_path / "raw"),
        ],
    )

    assert result.exit_code == 0
    assert manager.list_calls == [("aws.events", "aws.cloudtrail")]
    assert manager.export_calls == [
        (
            "aws.events",
            "aws.cloudtrail.AWSAPICallViaCloudTrail",
            "3",
            "JSONSchemaDraft4",
        )
    ]
    assert commands[0][0] == "datamodel-codegen"
    assert commands[0][commands[0].index("--input-file-type") + 1] == "jsonschema"
    generated = tmp_path / "raw" / "cloudtrail" / "aws_api_call_via_cloudtrail.py"
    assert generated.exists()
    assert "class CloudtrailAWSAPICallViaCloudTrailEvent" in generated.read_text(
        encoding="utf-8"
    )
    service_init = (tmp_path / "raw" / "cloudtrail" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert (
        "from .aws_api_call_via_cloudtrail import "
        "CloudtrailAWSAPICallViaCloudTrailEvent  # noqa: F401"
    ) in service_init
    raw_init = (tmp_path / "raw" / "__init__.py").read_text(encoding="utf-8")
    assert "from .cloudtrail import *  # noqa: F403" in raw_init


def test_eventbridge_export_service_fails_cleanly_for_default_registry(
    monkeypatch,
    tmp_path,
) -> None:
    manager = FakeSchemaManager({})
    _, runner = fake_command_runner_factory()
    exporter = EventBridgeServiceExporter(schema_manager=manager, command_runner=runner)
    monkeypatch.setattr(
        "botocraft.cli.eventbridge.create_eventbridge_service_exporter",
        lambda: exporter,
    )

    result = CliRunner().invoke(
        cli,
        [
            "eventbridge",
            "export-service",
            "cloudtrail",
            "--raw-root",
            str(tmp_path / "raw"),
        ],
    )

    assert result.exit_code != 0
    assert "Retry with one or more explicit --registry-name values." in result.output


def test_eventbridge_export_service_supports_registry_override_and_idempotent_exports(
    monkeypatch,
    tmp_path,
) -> None:
    manager = FakeSchemaManager(
        {
            "custom.registry": [
                FakeSchema(
                    RegistryName="custom.registry",
                    SchemaName="custom.cloudtrail.AWSAPICallViaCloudTrail",
                ),
            ]
        }
    )
    _, runner = fake_command_runner_factory()
    exporter = EventBridgeServiceExporter(schema_manager=manager, command_runner=runner)
    monkeypatch.setattr(
        "botocraft.cli.eventbridge.create_eventbridge_service_exporter",
        lambda: exporter,
    )
    runner_cli = CliRunner()
    args = [
        "eventbridge",
        "export-service",
        "cloudtrail",
        "--registry-name",
        "custom.registry",
        "--schema-name-prefix",
        "custom.cloudtrail",
        "--raw-root",
        str(tmp_path / "raw"),
    ]

    first = runner_cli.invoke(cli, args)
    second = runner_cli.invoke(cli, args)

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert manager.list_calls == [
        ("custom.registry", "custom.cloudtrail"),
        ("custom.registry", "custom.cloudtrail"),
    ]
    service_init_lines = (
        tmp_path / "raw" / "cloudtrail" / "__init__.py"
    ).read_text(encoding="utf-8").splitlines()
    assert service_init_lines.count(
        "from .aws_api_call_via_cloudtrail import "
        "CloudtrailAWSAPICallViaCloudTrailEvent  # noqa: F401"
    ) == 1


def test_rename_primary_class_prefers_root_event_model(tmp_path) -> None:
    def run(command: Sequence[str]) -> None:
        command_list = list(command)
        if command_list[0] == "datamodel-codegen":
            output_path = Path(command_list[command_list.index("--output") + 1])
            output_path.write_text(
                (
                    "from pydantic import BaseModel, Field\n\n\n"
                    "class SSMCalendarStateChangeEvent(BaseModel):\n"
                    "    state: str\n\n\n"
                    "class CalendarStateChangeModel(BaseModel):\n"
                    "    detail: SSMCalendarStateChangeEvent\n"
                    "    detail_type: str = Field(..., alias='detail-type')\n"
                ),
                encoding="utf-8",
            )

    exporter = EventBridgeServiceExporter(
        schema_manager=FakeSchemaManager(
            {
                "aws.events": [
                    FakeSchema(
                        RegistryName="aws.events",
                        SchemaName="aws.ssm.CalendarStateChange",
                    ),
                ]
            }
        ),
        command_runner=run,
    )
    exporter.export_service(
        "ssm",
        registry_names=("aws.events",),
        raw_root=tmp_path / "raw",
    )

    file_path = tmp_path / "raw" / "ssm" / "calendarstatechange.py"
    contents = file_path.read_text(encoding="utf-8")
    assert "class SSMCalendarStateChangeEventDetail(BaseModel):" in contents
    assert "detail: SSMCalendarStateChangeEventDetail" in contents
    assert "class SSMCalendarStateChangeEvent(BaseModel):" in contents
