from pathlib import Path

import click

from botocraft.eventbridge.authoring import (
    EventBridgeAuthoringError,
    EventBridgeServiceExporter,
)

from .cli import cli


def create_eventbridge_service_exporter() -> EventBridgeServiceExporter:
    """
    Build shared EventBridge service exporter.

    Returns:
        Configured EventBridge exporter.

    """
    return EventBridgeServiceExporter()


@cli.group(
    short_help="Author and export EventBridge event models",
    name="eventbridge",
)
def eventbridge_group() -> None:
    """
    EventBridge authoring helpers.
    """


@eventbridge_group.command(
    "export-service",
    short_help="Export raw EventBridge schema models for one AWS service",
)
@click.argument("service")
@click.option(
    "--registry-name",
    "registry_names",
    multiple=True,
    default=("aws.events",),
    show_default=True,
    help="Registry to search. Repeat to search more than one registry.",
)
@click.option(
    "--raw-root",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path("botocraft/eventbridge/raw"),
    show_default=True,
    help="Root directory where raw event modules are generated.",
)
@click.option(
    "--schema-name-prefix",
    default=None,
    help="Override the schema name prefix. Defaults to aws.<service>.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show planned exports without writing files or running code generators.",
)
def export_eventbridge_service(
    service: str,
    registry_names: tuple[str, ...],
    raw_root: Path,
    schema_name_prefix: str | None,
    dry_run: bool,
) -> None:
    """
    Export raw EventBridge models for one AWS service.

    Args:
        service: AWS service name embedded in schema names such as
            ``aws.ecs`` or ``aws.cloudtrail``.

    Keyword Args:
        registry_names: Candidate EventBridge registries to search.
        raw_root: Root directory where raw modules are written.
        schema_name_prefix: Optional prefix override for schema lookup.
        dry_run: When ``True``, skip file writes and subprocesses.

    Raises:
        click.ClickException: Export fails or no matching schemas are found.

    """
    exporter = create_eventbridge_service_exporter()
    try:
        report = exporter.export_service(
            service,
            registry_names=registry_names,
            raw_root=raw_root,
            schema_name_prefix=schema_name_prefix,
            dry_run=dry_run,
        )
    except EventBridgeAuthoringError as exc:
        raise click.ClickException(str(exc)) from exc

    action = "Plan" if report.dry_run else "Wrote"
    click.echo(
        f"{action} {len(report.modules)} raw EventBridge module(s) for service "
        f"'{report.service}'."
    )
    for module in report.modules:
        click.echo(
            f"- {module.registry_name}/{module.schema_name}"
            f"@{module.schema_version or 'latest'} "
            f"-> {module.file_path} ({module.class_name})"
        )
