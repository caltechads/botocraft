import click

import botocore.session

from .cli import cli


@cli.group(
    short_help="Inspect botocore definitions",
    name='inspect'
)
def inspect_group():
    pass


@inspect_group.command('models', short_help="List all available shapes for a service")
@click.argument('service')
def inspect_list_shapes(service):
    session = botocore.session.get_session()
    service_model = session.get_service_model(service)
    for shape_name in service_model.shape_names:  # pylint: disable=not-an-iterable
        shape = service_model._shape_resolver.get_shape_by_name(shape_name)
        if shape.type_name == 'structure':
            print(f'{shape_name}:')
            if hasattr(shape, 'members'):
                for member_name, member_shape in shape.members.items():
                    print(f'    {member_name}: {member_shape.type_name} -> {member_shape.name}')
            else:
                print('    No members')
