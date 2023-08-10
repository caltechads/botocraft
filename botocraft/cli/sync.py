import click
from .cli import cli

from ..sync import (
    PydanticModelGenerator,
    PydanticManagerGenerator,
    CRUDLMapping
)


@cli.group(
    short_help="Work with botocraft Pydantic models",
    name='models'
)
def models_group():
    pass


@models_group.command('sync', short_help="Sync shapes for a service to Pydantic models")
@click.argument('service')
@click.argument('model', nargs=-1)
def models_sync(service, model):
    generator = PydanticModelGenerator(service, model)
    generator.generate()


@cli.group(
    short_help="Work with botocraft Pydantic models",
    name='managers'
)
def managers_group():
    pass


@managers_group.command('sync', short_help="Sync shapes for a service to Pydantic managers")
@click.argument('service')
@click.argument('model_name')
@click.argument('operation', nargs=-1)
def managers_sync(service, model_name, operation):
    mapping = CRUDLMapping(
        create='create_service',
        get='describe_services',
        update='update_service',
        delete='delete_service',
        list='list_services',
    )
    generator = PydanticManagerGenerator('ecs', 'Service', mapping)
    generator.generate()
