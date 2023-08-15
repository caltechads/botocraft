import click
from .cli import cli

from botocraft.sync import (
    PydanticModelGenerator,
    PydanticServiceGenerator
)


@cli.group(
    short_help="Work with botocraft Pydantic models",
    name='models'
)
def models_group():
    pass


@models_group.command('sync', short_help="Sync shapes for a service to Pydantic models")
@click.argument('service')
def models_sync(service):
    generator = PydanticModelGenerator(service)
    generator.generate()


@cli.group(
    short_help="Work with botocraft Pydantic models",
    name='managers'
)
def managers_group():
    pass


@managers_group.command('sync', short_help="Sync shapes for a service to Pydantic managers")
@click.argument('service')
def managers_sync(service):
    generator = PydanticServiceGenerator(service)
    generator.generate()
