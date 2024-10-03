import textwrap

import click
import yaml

from botocraft.sync.models import BotocraftInterface

from .cli import cli


@cli.group(short_help="Inspect botocraft service definitions", name="data")
def data_group():
    pass


@data_group.command("models", short_help="List model definitions for a service")
@click.argument("service")
def data_list_models(service: str) -> None:
    """
    Print the model definitions for a service.

    Args:
        service: The name of the AWS service to print the manager definitions
            for

    Raises:
        click.ClickException: no service definition for the given service

    """
    interface = BotocraftInterface()
    interface.load()
    if service not in interface.services:
        msg = f'No service definition for AWS Service "{service}"'
        raise click.ClickException(msg)
    service_definition = interface.services[service]
    for model_name, model_def in service_definition.models.items():
        click.secho(model_name, fg="green")
        click.echo(textwrap.indent(yaml.dump(model_def.model_dump()), "  "))


@data_group.command("managers", short_help="List model definitions for a service")
@click.argument("service")
def data_list_managers(service: str) -> None:
    """
    Print the manager definitions for a service.

    Args:
        service: The name of the AWS service to print the manager definitions
            for

    Raises:
        click.ClickException: no service definition for the given service

    """
    interface = BotocraftInterface()
    interface.load()
    if service not in interface.services:
        msg = f'No service definition for AWS Service "{service}"'
        raise click.ClickException(msg)
    service_definition = interface.services[service]
    for mgr_name, mgr_def in service_definition.managers.items():
        click.secho(mgr_name, fg="green")
        click.echo(textwrap.indent(yaml.dump(mgr_def.model_dump()), "  "))
