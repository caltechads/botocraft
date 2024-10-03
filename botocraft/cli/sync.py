from typing import Optional

import click

from botocraft.sync.models import BotocraftInterface

from .cli import cli


@cli.command("sync", short_help="Sync an aws service to botocraft")
@click.option("--service", default=None, help="The name of the AWS service to sync")
def models_sync(service: Optional[str]) -> None:
    interface = BotocraftInterface()
    interface.load()
    if service and service not in interface.services:
        msg = f'No service definition for AWS Service "{service}"'
        raise click.ClickException(msg)
    interface.generate(service=service)
