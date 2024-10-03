import re
from collections import OrderedDict
from textwrap import (
    indent as add_prefix,
)
from textwrap import (
    wrap,
)
from typing import Dict, List, Optional

import botocore.session
import click

from .cli import cli


def camel_to_snake(camel_str: str) -> str:
    """
    Convert a camel case string to snake case.

    Args:
        camel_str: the input camel case string

    Returns:
        The snake case version of the input string

    """
    return re.sub(r"(?<=[a-z])(?=[A-Z])", "_", camel_str).lower()


def print_shape(
    service_model: botocore.model.ServiceModel,
    shape_name: str,
    indent: int = 0,
    label: Optional[str] = None,
    documentation: bool = False,
) -> None:
    """
    Print the name and members of a shape.

    Args:
        service_model: the botocore service model object
        shape_name: the name of the shape to print

    Keyword Args:
        indent: the number of spaces to indent the output
        label: a label to print before the shape name
        documentation: whether to print the shape documentation

    """
    shape = service_model._shape_resolver.get_shape_by_name(shape_name)  # type: ignore[attr-defined]  # noqa: SLF001
    output = []
    if shape.type_name == "structure":
        if label is not None:
            output.append(
                f"{click.style(label, fg='cyan')}: {click.style(shape_name, fg='red')}"
            )
        else:
            output.append(click.style(f"{shape_name}:", fg="red"))
        if documentation and hasattr(shape, "documentation") and shape.documentation:
            docs = wrap(shape.documentation)
            output.append(f"    {click.style(docs, fg='green')}")
        if hasattr(shape, "members") and shape.members:
            for member_name, member_shape in shape.members.items():
                output.append(
                    f"    {click.style(member_name, fg='cyan')}: {member_shape.type_name} -> "  # noqa: E501
                    f"{click.style(member_shape.name, fg='blue')}"
                )
        else:
            output.append("    No members")
    # purge empty lines
    output = [line for line in output if line.strip()]
    _output = "\n".join(output)
    if indent:
        _output = add_prefix(_output, " " * indent)
    print(_output)


@cli.group(short_help="Inspect botocore definitions", name="botocore")
def botocore_group():
    pass


@botocore_group.command("services", short_help="List all available botocore services")
def botocore_list_services():
    """
    List codenames and human names for all botocore services.
    """
    session = botocore.session.get_session()
    for service_name in session.get_available_services():
        service_model = session.get_service_model(service_name)
        print(
            f"{click.style(service_name, fg='blue')}: "
            f"{service_model.metadata['serviceId']}"
        )


@botocore_group.command("models", short_help="List all available shapes for a service")
@click.option("--names-only", is_flag=True, help="List only model names, not shapes")
@click.argument("service")
def botocore_list_shapes(service: str, names_only: bool):
    """
    List all shapes in a botocore service model.

    Args:
        service: the name of the service
        names_only: whether to list only the names of the shapes

    """
    session = botocore.session.get_session()
    service_model = session.get_service_model(service)
    for shape_name in service_model.shape_names:  # pylint: disable=not-an-iterable
        if names_only:
            click.secho(shape_name, fg="red")
        else:
            print_shape(service_model, shape_name)


@botocore_group.command("model", short_help="List all available shapes for a service")
@click.option("--dependencies", is_flag=True, help="List dependencies for the model")
@click.option("--operations", is_flag=True, help="List operations for the model")
@click.option("--documentation", is_flag=True, help="Show documentation for the model")
@click.argument("service")
@click.argument("model")
def botocore_list_shape(
    service: str,
    model: str,
    dependencies: bool,
    operations: bool,
    documentation: bool,
):
    session = botocore.session.get_session()
    service_model = session.get_service_model(service)
    if model not in list(service_model.shape_names):
        click.secho(f"Model {model} not found in service {service}", fg="red")
    print_shape(service_model, model, documentation=documentation)
    if operations:
        _operations = [op for op in list(service_model.operation_names) if model in op]
        if _operations:
            print()
            click.secho("Operations:", fg="yellow")
            click.secho("-" * len("Operations"), fg="yellow")
            print()
            for operation in _operations:
                click.secho(camel_to_snake(operation), fg="cyan")
    if dependencies:
        print()
        click.secho("Dependencies:", fg="yellow")
        click.secho("-" * len("Dependencies"), fg="yellow")
        print()
        shape = service_model._shape_resolver.get_shape_by_name(model)  # type: ignore[attr-defined]  # noqa: SLF001
        if (
            shape.type_name == "structure"
            and hasattr(shape, "members")
            and shape.members
        ):
            for member_name, member_shape in shape.members.items():
                if member_shape.type_name == "structure":
                    click.secho(f"{model}.{member_name}:", fg="cyan")
                    print_shape(service_model, member_shape.name, indent=4)
                elif member_shape.type_name == "list":
                    list_shape = member_shape.member
                    click.secho(f"{model}.{member_name} -> List:", fg="cyan")
                    if list_shape.type_name == "structure":
                        print_shape(service_model, list_shape.name, indent=4)
                elif member_shape.type_name == "string":
                    if member_shape.enum:
                        click.secho(f"{model}.{member_name}:", fg="cyan")
                        click.secho(f"    {member_name} -> Enum:", fg="cyan")
                        values = ", ".join(member_shape.enum)
                        click.secho(f"      {values}", fg="white")


@botocore_group.command(
    "operations", short_help="List all available operations for a service"
)
@click.argument("service")
def botocore_list_operations(service: str):
    """
    Print all operations for a service, along with their input and output shapes.

    Args:
        service: the name of the service

    """
    session = botocore.session.get_session()
    service_model = session.get_service_model(service)
    for name in service_model.operation_names:  # pylint: disable=not-an-iterable
        operation_model = service_model.operation_model(name)
        print(f"{name}:")
        boto3_name = camel_to_snake(name)
        print(f"    boto3 name: {boto3_name}")
        input_shape = operation_model.input_shape
        if input_shape is not None:
            print_shape(service_model, input_shape.name, indent=4, label="Input")
        output_shape = operation_model.output_shape
        if output_shape is not None:
            print_shape(service_model, output_shape.name, indent=4, label="Output")


@botocore_group.command(
    "primary-models", short_help="List all probable primary models for a service"
)
@click.argument("service")
def botocore_list_primary_models(service: str):
    """
    List all probable primary models for a service.

    Args:
        service: the name of the service

    """
    session = botocore.session.get_session()
    service_model = session.get_service_model(service)
    operation_names: List[str] = list(service_model.operation_names)
    prefixes = (
        "Put",
        "Get",
        "Create",
        "Delete",
        "Describe",
        "List",
        "Update",
        "Modify",
    )
    writable_prefixes = ("Put", "Create", "Delete", "Update", "Modify")
    # First pass: list all shapes
    # Second pass: assign operations to the most specific shape
    # Then print the shapes with their operations
    models: Dict[str, List[str]] = {}
    names = list(service_model.shape_names)
    names.sort(key=lambda x: len(x))
    names.reverse()
    taken = []
    for shape_name in names:
        shape = service_model._shape_resolver.get_shape_by_name(shape_name)  # type: ignore[attr-defined]  # noqa: SLF001
        if shape.type_name != "structure":
            continue
        operations = [
            op
            for op in operation_names
            if shape_name in op and op.startswith(prefixes) and op not in taken
        ]
        if operations:
            models[shape_name] = operations
            taken.extend(operations)
    _models = OrderedDict(sorted(models.items(), key=lambda x: x[1]))
    for model in _models:
        operations = _models[model]
        writable: bool = False
        label: str = ""
        for op in operations:
            if op.startswith(writable_prefixes):
                writable = True
                break
        if not writable:
            label = click.style(": [READONLY]", fg="green")
        click.echo(f'{click.style(model, fg="red")}{label}')
        for operation in operations:
            click.secho(f"    {camel_to_snake(operation)}", fg="cyan")
