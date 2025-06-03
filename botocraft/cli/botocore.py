import re
from collections import OrderedDict
from pathlib import Path
from textwrap import (
    indent as add_prefix,
)
from typing import Dict, Final, List, Literal, cast

import botocore.model
import botocore.session
import click

from .cli import cli

IntType = Literal["int", "long", "double", "float", "timestamp", "boolean"]


def camel_to_snake(camel_str: str) -> str:
    """
    Convert a camel case string to snake case.

    Args:
        camel_str: the input camel case string

    Returns:
        The snake case version of the input string

    """
    return re.sub(r"(?<=[a-z])(?=[A-Z])", "_", camel_str).lower()


class ShapePrinter:
    #: The number of spaces to indent substructures in a shape
    SHAPE_INDENT: Final[int] = 2

    def render_string(
        self,
        shape: botocore.model.StringShape,
        indent: int = 0,
        prefix: str | None = None,
    ) -> List[str]:
        """
        Render a string shape as a descriptive string.

        Args:
            shape: the botocore shape object

        Keyword Args:
            indent: the number of spaces to indent the output
            prefix: a prefix to add to the shape name

        """
        output = []
        constraints = ""
        if "min" in shape.metadata and shape.metadata["min"] is not None:
            constraints += f"minlength: {shape.metadata['min']} "
        if "max" in shape.metadata and shape.metadata["max"] is not None:
            constraints += f"maxlength: {shape.metadata['max']} "
        if "pattern" in shape.metadata and shape.metadata["pattern"] is not None:
            constraints += f"""pattern: "{shape.metadata["pattern"]}" """
        if prefix is not None:
            output.append(
                f"{click.style(prefix, fg='cyan')}: string -> "
                f"{click.style(shape.name, fg='blue')}"
            )
        else:
            output.append(
                f"{click.style(shape.name, fg='red')}: string -> {click.style(shape.name, fg='blue')}"  # noqa: E501
            )
        if constraints:
            output.append(f"    Constraints: {click.style(constraints, fg='yellow')}")
        if shape.enum:
            values = ", ".join([f'"{v}"' for v in shape.enum])
            output.append(f"    Enum: {click.style(values, fg='yellow')}")
        if indent:
            output = [add_prefix(line, " " * indent) for line in output]
        # purge empty lines
        return [line for line in output if line.strip()]

    def render_blob(
        self,
        shape: botocore.model.StringShape,
        indent: int = 0,
        prefix: str | None = None,
    ) -> List[str]:
        """
        Render a blob shape as a descriptive string.  According to the botocore
        documentation::

            [Blobs] are assumed to be binary, and if a str/unicode type is
            passed in, it will be encoded as utf-8.

        Args:
            shape: the botocore shape object

        Keyword Args:
            indent: the number of spaces to indent the output
            prefix: a prefix to add to the shape name

        """
        output = []
        constraints = ""
        if "min" in shape.metadata and shape.metadata["min"] is not None:
            constraints += f"minlength: {shape.metadata['min']} "
        if "max" in shape.metadata and shape.metadata["max"] is not None:
            constraints += f"maxlength: {shape.metadata['max']} "
        if prefix is not None:
            output.append(
                f"{click.style(prefix, fg='cyan')}: bytes -> "
                f"{click.style(shape.name, fg='blue')}"
            )
        else:
            output.append(
                f"{click.style(shape.name, fg='red')}: bytes -> {click.style(shape.name, fg='blue')}"  # noqa: E501
            )
        if constraints:
            output.append(f"    Constraints: {click.style(constraints, fg='yellow')}")
        if indent:
            output = [add_prefix(line, " " * indent) for line in output]
        # purge empty lines
        return [line for line in output if line.strip()]

    def render_integer(
        self,
        shape: botocore.model.Shape,
        indent: int = 0,
        prefix: str | None = None,
        int_type: IntType = "int",
    ) -> List[str]:
        """
        Render a integer shape as a descriptive string.

        Args:
            shape: the botocore shape object

        Keyword Args:
            indent: the number of spaces to indent the output
            prefix: a prefix to add to the shape name
            int_type: the type of integer (int or long)

        """
        output = []
        constraints = ""
        if "min" in shape.metadata and shape.metadata["min"] is not None:
            constraints += f"min: {shape.metadata['min']} "
        if "max" in shape.metadata and shape.metadata["max"] is not None:
            constraints += f"max: {shape.metadata['max']} "
        if prefix is not None:
            output.append(
                f"{click.style(prefix, fg='cyan')}: {int_type} -> "
                f"{click.style(shape.name, fg='blue')}"
            )
        else:
            output.append(
                f"{click.style(shape.name, fg='red')}: {int_type} -> {click.style(shape.name, fg='blue')}"  # noqa: E501
            )
        if constraints:
            output.append(f"    Constraints: {click.style(constraints, fg='yellow')}")
        if indent:
            output = [add_prefix(line, " " * indent) for line in output]
        # purge empty lines
        return [line for line in output if line.strip()]

    def render_list(
        self,
        shape: botocore.model.ListShape,
        indent: int = 0,
        prefix: str | None = None,
    ) -> List[str]:
        """
        Render a list shape as a descriptive string.

        Args:
            shape: the botocore shape object

        Keyword Args:
            indent: the number of spaces to indent the output
            prefix: a prefix to add to the shape name

        """
        output = []
        member = shape.member
        if prefix is not None:
            output.append(
                f"{click.style(prefix, fg='cyan')}: list -> "
                f"{click.style(shape.name, fg='blue')} (List[{member.name}])"
            )
        else:
            output.append(
                f"{click.style(shape.name, fg='red')}: list -> {click.style(shape.name, fg='blue')} (List[{member.name}])"  # noqa: E501
            )
        output.extend(self.render(member, indent=self.SHAPE_INDENT))
        if indent:
            output = [add_prefix(line, " " * indent) for line in output]
        return [line for line in output if line.strip()]

    def render_map(
        self,
        shape: botocore.model.MapShape,
        indent: int = 0,
        prefix: str | None = None,
    ) -> List[str]:
        """
        Render a map shape as a descriptive string.

        Args:
            shape: the botocore shape object

        Keyword Args:
            indent: the number of spaces to indent the output
            prefix: a prefix to add to the shape name

        """
        output = []
        key = shape.key
        value = shape.value
        if prefix is not None:
            output.append(
                f"{click.style(prefix, fg='cyan')}: map -> "
                f"{click.style(shape.name, fg='blue')} (Map[{key.name}, {value.name}])"
            )
        else:
            output.append(
                f"{click.style(shape.name, fg='red')}: map -> {click.style(shape.name, fg='blue')} (Map[{key.name}, {value.name}])"  # noqa: E501
            )
        output.extend(self.render(key, indent=self.SHAPE_INDENT, prefix="Key"))
        output.extend(self.render(value, indent=self.SHAPE_INDENT, prefix="Value"))
        if indent:
            output = [add_prefix(line, " " * indent) for line in output]
        return [line for line in output if line.strip()]

    def render_structure(
        self,
        shape: botocore.model.StructureShape,
        indent: int = 0,
        prefix: str | None = None,
    ) -> List[str]:
        """
        Render a structure shape as a string.

        Args:
            shape: the botocore shape object

        Keyword Args:
            indent: the number of spaces to indent the output
            prefix: a prefix to add to the shape name

        """
        output = []
        if prefix is not None:
            output.append(
                f"{click.style(prefix, fg='cyan')}: structure -> "
                f"{click.style(shape.name, fg='red')}"
            )
        else:
            output.append(f"{click.style(shape.name, fg='red')}: structure")
        if hasattr(shape, "members") and shape.members:
            for member_name, member_shape in shape.members.items():
                required = ""
                if member_name in shape.required_members:
                    required = click.style(" [required]", fg="red")
                output.extend(
                    self.render(
                        member_shape,
                        indent=self.SHAPE_INDENT,
                        prefix=f"{member_name}{required}",
                    )
                )
        else:
            output.append("    No members")
        if indent:
            output = [add_prefix(line, " " * indent) for line in output]
        return [line for line in output if line.strip()]

    def render(
        self,
        shape: botocore.model.Shape,
        indent: int = 0,
        prefix: str | None = None,
    ) -> List[str]:
        """
        Render a shape as a string.

        Args:
            shape: the botocore shape object

        Keyword Args:
            indent: the number of spaces to indent the output
            prefix: a prefix to add to the shape name

        """
        output = []
        if shape.type_name == "structure":
            output = self.render_structure(
                cast("botocore.model.StructureShape", shape),
                indent=indent,
                prefix=prefix,
            )
        elif shape.type_name == "list":
            output = self.render_list(
                cast("botocore.model.ListShape", shape),
                indent=indent,
                prefix=prefix,
            )
        elif shape.type_name == "map":
            output = self.render_map(
                cast("botocore.model.MapShape", shape),
                indent=indent,
                prefix=prefix,
            )
        elif shape.type_name == "string":
            output = self.render_string(
                cast("botocore.model.StringShape", shape),
                indent=indent,
                prefix=prefix,
            )
        elif shape.type_name == "blob":
            output = self.render_blob(
                cast("botocore.model.Shape", shape),  # type: ignore[arg-type]
                indent=indent,
                prefix=prefix,
            )
        elif shape.type_name in [
            "integer",
            "long",
            "double",
            "float",
            "timestamp",
            "boolean",
        ]:
            output = self.render_integer(
                cast("botocore.model.StringShape", shape),
                indent=indent,
                prefix=prefix,
                int_type=cast("IntType", shape.type_name),
            )
        else:
            msg = f"Shape type {shape.type_name} not implemented"
            raise NotImplementedError(msg)
        return output


def print_shape(
    service_model: botocore.model.ServiceModel,
    shape_name: str,
    indent: int = 0,
    prefix: str | None = None,
) -> None:
    """
    Print the name and members of a shape.

    Args:
        service_model: the botocore service model object
        shape_name: the name of the shape to print

    Keyword Args:
        indent: the number of spaces to indent the output
        prefix: a label to print before the shape name

    """
    shape = service_model._shape_resolver.get_shape_by_name(shape_name)  # type: ignore[attr-defined]  # noqa: SLF001
    renderer = ShapePrinter()
    output = renderer.render(
        shape,
        indent=indent,
        prefix=prefix,
    )
    print("\n".join(output))


def print_operation(service_model: botocore.model.ServiceModel, name: str) -> None:
    """
    Print the full info for a botocore operation.

    Args:
        service_model: the botocore service model object
        name: the name of the operation to print

    """
    operation_model = service_model.operation_model(name)
    print(f"{name}:")
    boto3_name = camel_to_snake(name)
    print(f"    boto3 name: {boto3_name}")
    input_shape = operation_model.input_shape
    if input_shape is not None:
        print_shape(service_model, input_shape.name, indent=4, prefix="Input")
    output_shape = operation_model.output_shape
    if output_shape is not None:
        print_shape(service_model, output_shape.name, indent=4, prefix="Output")


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
@click.option("--shape-type", default=None, help="Show only this type of shape")
@click.argument("service")
def botocore_list_shapes(service: str, names_only: bool, shape_type: str | None):
    """
    List all shapes in a botocore service model.

    Args:
        service: the name of the service
        names_only: whether to list only the names of the shapes
        shape_type: the type of shape to list

    """
    session = botocore.session.get_session()
    service_model = session.get_service_model(service)
    for shape_name in service_model.shape_names:  # pylint: disable=not-an-iterable
        if names_only:
            if shape_type:
                shape = service_model._shape_resolver.get_shape_by_name(shape_name)  # type: ignore[attr-defined]  # noqa: SLF001
                if shape.type_name != shape_type:
                    continue
            click.secho(shape_name, fg="red")
        else:
            print_shape(service_model, shape_name)


@botocore_group.command("model", short_help="List all available shapes for a service")
@click.option("--dependencies", is_flag=True, help="List dependencies for the model")
@click.option("--operations", is_flag=True, help="List operations for the model")
@click.argument("service")
@click.argument("model")
def botocore_list_shape(
    service: str,
    model: str,
    dependencies: bool,
    operations: bool,
):
    session = botocore.session.get_session()
    service_model = session.get_service_model(service)
    if model not in list(service_model.shape_names):
        click.secho(f"Model {model} not found in service {service}", fg="red")
    print_shape(service_model, model)
    if operations:
        _operations = [op for op in list(service_model.operation_names) if model in op]
        if _operations:
            print()
            click.secho("Operations:", fg="yellow")
            click.secho("-" * len("Operations"), fg="yellow")
            print()
            for operation in _operations:
                print_operation(service_model, operation)
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
@click.option("--name", help="List only the operation with this name")
@click.option(
    "--names-only/--no-names-only", help="List only the names of the operations"
)
@click.argument("service")
def botocore_list_operations(service: str, name: str | None, names_only: bool):
    """
    Print all operations for a service, along with their input and output shapes.

    Args:
        service: the name of the service

    Keyword Args:
        name: the name of the operation to print
        names_only: whether to list only the names of the operations

    Keyword Args:
        name: the name of the operation to list

    """
    session = botocore.session.get_session()
    service_model = session.get_service_model(service)
    for _name in service_model.operation_names:  # pylint: disable=not-an-iterable
        if name and name != _name:
            continue
        if names_only:
            click.secho(_name, fg="red")
            continue
        print_operation(service_model, _name)
        if name:
            break


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
        click.echo(f"{click.style(model, fg='red')}{label}")
        for operation in operations:
            click.secho(f"    {camel_to_snake(operation)}", fg="cyan")


@botocore_group.command(
    "bootstrap",
    short_help=(
        "Bootstrap a botocore service model with empty yaml files in botocore/data"
    ),
)
@click.argument("service")
def botocore_bootstrap(service: str) -> None:
    """
    Bootstrap a botocore service model with empty yaml files in botocore/data.

    First, run ``botocraft botocore services`` to list available services, and
    find the botocore name for the service you want to bootstrap.  Then, run
    this command to create the necessary files for the service.

    Finally, go edit the files in `botocore/data/<service>` to add the primary
    model definitions and any other necessary information.

    Args:
        service: the name of the botocore service to bootstrap

    """
    path = Path(__file__).resolve().parent.parent / "data" / service
    if not path.exists():
        path.mkdir(parents=True, exist_ok=False)
    else:
        click.secho(f"Path {path} already exists, not creating it.", fg="red")
    models_yaml = path / "models.yaml"
    models_yaml.touch(exist_ok=True)
    managers_yaml = path / "managers.yaml"
    managers_yaml.touch(exist_ok=True)
    click.secho(
        f"Created {models_yaml} and {managers_yaml}",
        fg="green",
    )
    click.secho(
        "Now edit the files to add the primary model definitions and their managers.",
        fg="white",
    )
