import re
import subprocess
import tempfile
import warnings
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Final, List, Set, Type, cast

import boto3
import botocore.model
import botocore.session
from docformatter.format import Formatter

from .docstring import DocumentationFormatter, FormatterArgs
from .exceptions import ModelHasNoMembersError, NoPythonTypeError
from .methods import (
    CreateMethodGenerator,
    DeleteMethodGenerator,
    GeneralMethodGenerator,
    GetManyMethodGenerator,
    GetMethodGenerator,
    ListMethodGenerator,
    ManagerMethodGenerator,
    ModelManagerMethodGenerator,
    ModelPropertyGenerator,
    ModelRelationGenerator,
    PartialUpdateMethodGenerator,
    UpdateMethodGenerator,
)
from .models import (
    ManagerDefinition,
    ManagerMethodDefinition,
    ModelAttributeDefinition,
    ModelDefinition,
    ServiceDefinition,
)
from .shapes import PythonTypeShapeConverter
from .sphinx import ServiceSphinxDocBuilder


@dataclass
class ModelTagsDAO:
    """
    A data access object for how to handle tags in a model.

    """

    #: The new set of base classes for this model, possibly including the
    #: ``TagsDictMixin`` class.
    base_class: str
    #: The name of the tag class.  This is the class that will be used to
    #: represent the tags in the model.  This will be ``None`` if there are no
    #: tags in the model.
    tag_class: str | None = None


class AbstractGenerator:
    def __init__(self, service_generator: "ServiceGenerator") -> None:
        session = botocore.session.get_session()
        #: The :py:class:`ServiceGenerator` we're generating models for.
        self.service_generator = service_generator
        #: The name of the AWS service we're generating models for.
        self.service_name = service_generator.aws_service_name
        #: The botocraft service definition for our service.
        self.service_def = service_generator.service_def
        #: The botocraft interface definition.  We collect things we need to
        #: know globally here.
        self.interface = service_generator.interface
        #: The botocore service model for our service.
        self.service_model = session.get_service_model(self.service_name)
        #: The documentation formatter we will use to format docstrings.
        self.docformatter = DocumentationFormatter()
        #: The classes we've generated for this service.  The key is the class
        #: name, and the value is the code for the class.  We'll write this to a
        #: file later in the order that the classes were generated.
        self.classes: OrderedDict[str, str] = OrderedDict()
        #: A list of imports we need for our classes to function properly.  They'll
        #: be added to the top of the file.
        self.imports: Set[str] = set()

    @property
    def shapes(self) -> List[str]:
        """
        List the names of all the shapes in the service model.

        Returns:
            A list of shape names.

        """
        return self.service_model.shape_names

    def clear(self) -> None:
        """
        Clear the generated classes and imports.
        """
        self.classes = OrderedDict()
        self.imports = set()

    def get_shape(self, name: str) -> botocore.model.Shape:
        """
        Get a :py:class:`botocore.model.Shape` by name from the service model,
        :py:attr:`service_model`.

        Args:
            name: The name of the shape to retrieve.

        Returns:
            The shape object.

        """
        try:
            return self.service_model.shape_for(name)
        except botocore.model.NoShapeFoundError:
            model_name = self.service_def.resolve_model_name(name)
            return self.service_model.shape_for(model_name)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get the metadata for the botocore service definition.

        Returns:
            The contents of the metadata attribute.

        """
        return self.service_model.metadata

    def generate_all_service_models(self) -> None:
        raise NotImplementedError


class BotocoreFieldsFormatter:
    """
    Handles the formatting of fields from botocore shapes into Python code for
    model classes.  This class extracts and formats field definitions from
    botocore shapes, applying appropriate types, docstrings, and pydantic field
    configurations.
    """

    def __init__(self, model_generator: "ModelGenerator") -> None:
        """
        Initialize the formatter with a reference to the model generator.

        Args:
            model_generator: The ModelGenerator instance that's using this
                formatter.

        """
        #: Reference to the parent ModelGenerator
        self.model_generator = model_generator
        #: The documentation formatter used to format field docstrings
        self.docformatter = self.model_generator.docformatter

    def format_fields(
        self,
        model_name: str,
        model_def: ModelDefinition,
        model_shape: botocore.model.Shape | None = None,
    ) -> List[str]:
        """
        Return the Python code representing all the fields for a model from the
        botocore shape.

        Args:
            model_name: The name of the model to generate fields for
            model_def: The botocraft model definition for this model
            model_shape: The botocore shape to generate the model for. If not
                provided, it will be extracted from the botocore service model.

        Returns:
            The list of Python code representing the pydantic model fields as
            strings

        """
        fields: List[str] = []
        # Get all field definitions for this model
        model_fields = self.model_generator.botocore_shape_field_defs(model_name)

        # Get the shape if not provided
        if not model_shape:
            model_shape = self.model_generator.get_shape(model_name)

        # Use alternate_name if specified
        effective_model_name = model_def.alternate_name or model_name

        # Only proceed if the shape has members
        if not hasattr(model_shape, "members"):
            return fields

        # Process each field in the model
        for field_name, field_def in model_fields.items():
            field_code = self._format_field(
                effective_model_name, field_name, field_def, model_shape
            )
            fields.extend(field_code)

        return fields

    def _format_field(
        self,
        model_name: str,
        field_name: str,
        field_def: ModelAttributeDefinition,
        model_shape: botocore.model.Shape,
    ) -> List[str]:
        """
        Generate code for a single field in a model.

        Args:
            model_name: The model name
            field_name: The field name
            field_def: The field definition
            model_shape: The model shape

        Returns:
            List of lines of code for the field

        """
        # Get field shape and determine if it's required
        field_shape = field_def.botocore_shape
        required = self._is_field_required(field_name, field_def, model_shape)

        # Get type and documentation
        python_type, docstring = self._get_field_type_and_docs(
            model_name, field_name, field_def, field_shape, model_shape
        )

        # Build field definition with appropriate annotations and defaults
        field_code = []
        field_line = self._build_field_definition(
            field_name, field_def, python_type, required
        )
        field_code.append(field_line)

        # Add docstring if available
        if docstring:
            field_code.append(self.docformatter.format_attribute(docstring))

        return field_code

    def _is_field_required(
        self,
        field_name: str,
        field_def: ModelAttributeDefinition,
        model_shape: botocore.model.Shape,
    ) -> bool:
        """
        Determine if a field is required based on field definition and model shape.

        Args:
            field_name: The field name
            field_def: The field definition
            model_shape: The model shape

        Returns:
            True if the field is required, False otherwise

        """
        if field_def.required is not None:
            return field_def.required
        return field_name in model_shape.required_members

    def _get_field_type_and_docs(
        self,
        model_name: str,
        field_name: str,
        field_def: ModelAttributeDefinition,
        field_shape: botocore.model.Shape | None,
        model_shape: botocore.model.Shape,
    ) -> tuple[str, str | None]:
        """
        Get the Python type and documentation for a field.

        Args:
            model_name: The model name
            field_name: The field name
            field_def: The field definition
            field_shape: The field shape
            model_shape: The model shape

        Returns:
            Tuple of (python_type, docstring)

        """
        docstring = field_def.docstring

        if field_shape:
            # Get type from the botocore shape
            python_type = self.model_generator.get_python_type_for_field(
                model_name,
                field_name,
                model_shape=model_shape,
                field_def=field_def,
                field_shape=field_shape,
            )
            # Use shape documentation if no explicit docstring provided
            if not docstring:
                docstring = cast("str", field_shape.documentation)
        else:
            # No shape, must have explicit type in field definition
            assert field_def.python_type, (
                f"Field {field_name} in model {model_name} has no botocore "
                "shape or python type"
            )
            python_type = field_def.python_type

        return python_type, docstring

    def _build_field_definition(
        self,
        field_name: str,
        field_def: ModelAttributeDefinition,
        python_type: str,
        required: bool,
    ) -> str:
        """
        Build the field definition code.

        Args:
            field_name: The field name
            field_def: The field definition
            python_type: The Python type for the field
            required: Whether the field is required

        Returns:
            Field definition code as a string

        """
        # Handle Optional types and default values
        default = None
        if not required:
            if not field_def.readonly and not field_def.rename:
                python_type = f"Optional[{python_type}]"
            default = "None" if field_def.default is None else field_def.default

        # Determine displayed field name (could be renamed)
        display_name = field_def.rename or field_name

        # Start building the field line
        field_line = f"    {display_name}: {python_type}"

        # Determine if we need pydantic Field
        needs_field_class = False
        field_class_args = []

        if default:
            if python_type.startswith("List[") and default == "None":
                field_class_args.append("default_factory=list")
                needs_field_class = True
            elif python_type.startswith("Dict[") and default == "None":
                field_class_args.append("default_factory=dict")
                needs_field_class = True
            else:
                field_class_args.append(f"default={default}")

        if field_def.rename:
            field_class_args.append(f'alias="{field_name}"')
            needs_field_class = True

        if field_def.readonly:
            field_class_args.append("frozen=True")
            needs_field_class = True

        if needs_field_class:
            field_line += f" = Field({', '.join(field_class_args)})"
        elif default:
            field_line += f" = {field_def.default}"

        return field_line


class ExtraFieldsFormatter:
    """
    Handles the formatting of manually defined extra fields into Python code for
    model classes.

    This class is responsible for generating field definitions for extra fields
    that are exclusively defined in the botocraft model definition and not
    present in the botocore service definition.
    """

    def __init__(self, model_generator: "ModelGenerator") -> None:
        """
        Initialize the formatter with a reference to the model generator.

        Args:
            model_generator: The ModelGenerator instance that's using this
                formatter.

        """
        #: Reference to the parent ModelGenerator
        self.model_generator = model_generator
        #: The documentation formatter used to format field docstrings
        self.docformatter = self.model_generator.docformatter

    def format_fields(self, model_def: ModelDefinition) -> List[str]:
        """
        Build out the manually defined extra fields for a model.

        Extra fields are exclusively defined in the botocraft model definition.
        We add them manually to the model definition.

        Args:
            model_def: The botocraft model definition for this model

        Returns:
            A list of formatted field code lines

        """
        fields: List[str] = []

        # Get the extra_fields attribute or return empty list if not present
        extra_fields = getattr(model_def, "extra_fields", {})

        # Process each field
        for field_name, field_def in extra_fields.items():
            field_code = self._format_single_field(field_name, field_def)
            fields.extend(field_code)

            # Update imports for this field
            if hasattr(field_def, "imports") and field_def.imports:
                self.model_generator.imports.update(field_def.imports)

        return fields

    def _format_single_field(
        self, field_name: str, field_def: ModelAttributeDefinition
    ) -> List[str]:
        """
        Format a single extra field into Python code.

        Args:
            field_name: The name of the field
            field_def: The definition of the field

        Returns:
            List of code lines for this field

        """
        field_code = []
        needs_field_class = False
        field_class_args = []

        # Handle default values
        if field_def.default:
            if self._is_container_with_none_default(field_def):
                field_class_args.append(self._get_container_factory(field_def))
                needs_field_class = True
            else:
                field_class_args.append(f"default={field_def.default}")

        # Handle readonly fields
        if field_def.readonly:
            field_class_args.append("frozen=True")
            needs_field_class = True

        # Handle field renaming
        if field_def.rename:
            field_line = f"    {field_def.rename}: {field_def.python_type}"
            field_class_args.append(f'alias="{field_name}"')
            needs_field_class = True
        else:
            field_line = f"    {field_name}: {field_def.python_type}"

        # Append Field class or default value if needed
        if needs_field_class:
            field_line += f" = Field({', '.join(field_class_args)})"
        elif field_def.default:
            field_line += f" = {field_def.default}"

        field_code.append(field_line)

        # Add docstring if available
        if field_def.docstring:
            field_code.append(self.docformatter.format_attribute(field_def.docstring))

        return field_code

    def _is_container_with_none_default(
        self, field_def: ModelAttributeDefinition
    ) -> bool:
        """
        Check if field is a container type (List or Dict) with None default.

        Args:
            field_def: The field definition to check

        Returns:
            True if the field is a container with None default, False otherwise

        """
        return (
            field_def.python_type.startswith("List[")
            or field_def.python_type.startswith("Dict[")
        ) and field_def.default == "None"

    def _get_container_factory(self, field_def: ModelAttributeDefinition) -> str:
        """
        Get the appropriate default_factory for a container type.

        Args:
            field_def: The field definition

        Returns:
            String with the default_factory configuration

        """
        if field_def.python_type.startswith("List["):
            return "default_factory=list"
        if field_def.python_type.startswith("Dict["):
            return "default_factory=dict"
        return f"default={field_def.default}"


class ModelGenerator(AbstractGenerator):
    """
    Generate pydantic model definitions from botocore shapes.
    """

    def __init__(self, service_generator: "ServiceGenerator") -> None:
        super().__init__(service_generator)
        #: The shape converter we will use to convert botocore shapes to python types
        self.shape_converter = PythonTypeShapeConverter(service_generator, self)
        #: The fields formatter for converting botocore shapes to field definitions
        self.fields_formatter = BotocoreFieldsFormatter(self)
        #: The formatter for extra fields defined in the botocraft model definition
        self.extra_fields_formatter = ExtraFieldsFormatter(self)

    def get_model_def(self, model_name: str) -> ModelDefinition:
        """
        Return the :py:class:`ModelDefinition` for a model.

        Notes:
            If there is no human defined model definition for the model, we will
            create a default one.

        Args:
            model_name: The name of the model to get the definition for.

        Returns:
            The model definition.

        """
        if model_name in self.service_def.primary_models:
            defn = self.service_def.primary_models[model_name]
            if defn.readonly:
                defn.base_class = "ReadonlyPrimaryBoto3Model"
            else:
                defn.base_class = "PrimaryBoto3Model"
            return defn
        if model_name in self.service_def.secondary_models:
            defn = self.service_def.secondary_models[model_name]
            if defn.readonly:
                defn.base_class = "ReadonlyBoto3Model"
            else:
                defn.base_class = "Boto3Model"
            return defn
        return ModelDefinition(base_class="Boto3Model", name=model_name)

    def add_extra_fields_from_output_shape(
        self, model_name: str, model_fields: Dict[str, ModelAttributeDefinition]
    ) -> Dict[str, ModelAttributeDefinition]:
        """
        Extract extra fields from the output shape of a get or list method.
        These are fields that are in the output of the get/list methods but not
        in the service models.  We add them to the models as readonly fields so
        that we can load them from the API responses.

        Args:
            model_name: the name of the model to add fields to
            model_fields: the botocraft model field definitions for the model

        Returns:
            ``model_fields`` with any extra fields from the output shape added

        """
        model_def = self.get_model_def(model_name)
        if not model_def.output_shape:
            return model_fields
        output_shape = self.get_shape(model_def.output_shape)
        if not hasattr(output_shape, "members"):
            return model_fields
        for field_name, field_shape in output_shape.members.items():
            if field_name not in model_fields:
                model_fields[field_name] = ModelAttributeDefinition(
                    readonly=True, botocore_shape=field_shape
                )
        return model_fields

    def mark_readonly_fields(
        self, model_name: str, model_fields: Dict[str, ModelAttributeDefinition]
    ) -> Dict[str, ModelAttributeDefinition]:
        """
        Mark model fields as readonly if they are not in any of the input shapes
        defined for the model.  Such fields are returned by AWS but are not
        settable by the user.

        Args:
            model_name: The name of the model to mark fields for.
            model_fields: The botocraft model field definitions for the model.

        Returns:
            The updated model fields.

        """
        model_def = self.get_model_def(model_name)
        if not model_def.input_shapes:
            return model_fields
        # First include any fields that were manually set to writable
        # in the botocraft model definition
        writable_fields: Set[str] = {
            field_name
            for field_name in model_def.fields
            if model_def.fields[field_name].readonly is False
        }
        # Now add any fields that are in the input shapes
        for input_shape_name in model_def.input_shapes:
            input_shape = self.get_shape(input_shape_name)
            if hasattr(input_shape, "members"):
                writable_fields.update(input_shape.members.keys())
        # Mark any fields that are not in writable_fields as readonly
        for field_name, field_def in model_fields.items():
            if field_name not in writable_fields:
                field_def.readonly = True
        return model_fields

    def botocore_shape_field_defs(
        self, model_name: str
    ) -> Dict[str, ModelAttributeDefinition]:
        """
        Return the fields for a botocore shape as a dictionary of field names to
        botocraft field definitions.  This incorporates settings from the
        :py:class:`ModelAttributeDefinitions` from the  ``fields`` attribute of
        the associated model definition, if it exists.

        Note:
            This really only makes sense on
            :py:class:`botocore.model.StructureShape` objects or bespoke
            models, since they are the only ones that have fields (aka
            "members").

        Side Effects:
            If this is not a bespoke model, we set
            :py:attr:`ModelAttributeDefinition.botocore_shape` on each field
            definition, and we set :py:attr:`ModelAttributeDefinition.readonly`
            if the field is not in any of the input shapes for the model.

        Returns:
            A dictionary of field names to field definitions.

        """
        model_def = self.get_model_def(model_name)
        if model_def.bespoke:
            return model_def.extra_fields
        model_shape = self.get_shape(model_name)
        fields: Dict[str, ModelAttributeDefinition] = deepcopy(model_def.fields)
        if hasattr(model_shape, "members"):
            for field, field_shape in model_shape.members.items():
                if field not in fields:
                    fields[field] = ModelAttributeDefinition()
                    if field in model_shape.required_members:
                        fields[field].required = True
                fields[field].botocore_shape = field_shape
        fields = self.mark_readonly_fields(model_name, fields)
        # These are our manually defined extra fields
        if model_def.extra_fields:
            fields.update(model_def.extra_fields)
        # These are the fields that are in the output shape of the get/list
        # methods but not in the service model shape
        fields = self.add_extra_fields_from_output_shape(model_name, fields)
        return fields  # noqa: RET504

    def generate_all_service_models(self) -> None:
        """
        Generate all the service models.
        """
        for model_name in self.service_def.primary_models:
            _ = self.generate_single_model(model_name)

    def format_extra_fields_from_model_def(
        self, model_def: ModelDefinition
    ) -> List[str]:
        """
        Build out the manually defined extra fields for a model.

        Extra fields are exclusively defined in the botocraft model definition.
        We add them manually to the model definition.

        Args:
            model_def: The botocraft model definition for this model

        Returns:
            A list of extra fields.

        """
        return self.extra_fields_formatter.format_fields(model_def)

    def get_properties(self, model_def: ModelDefinition, base_class: str) -> str | None:
        """
        Handle the special properties and methods for primary models.  A primary
        model is a model that has either ``PrimaryBoto3Model`` or
        ``ReadonlyPrimaryBoto3Model`` as its ``base_class``.   Primary models are
        the main models that represent AWS resources, and are those that users can
        create, update, and delete.

        This means:

        * Adding a ``pk`` property that is an alias for the primary key.
        * Maybe adding a ``arn`` property that is an alias for the ARN key.
        * Maybe adding a ``name`` property that is an alias for the name key.
        * Adding any extra properties that were defined in the model definition.
        * Adding any relations to other models that were defined in the model
          definition.
        * Adding any manager shortcut methods that were defined in the model
          definition.

        Args:
            model_def: the botocraft model definition for this model
            base_class: the base class for this model

        Returns:
            The properties for this model, or ``None`` if this is not a primary
            model.

        """
        properties: str = ""
        if base_class in ["PrimaryBoto3Model", "ReadonlyPrimaryBoto3Model"]:
            assert model_def.primary_key or "pk" in model_def.properties, (
                f'Primary service model "{model_def.name}" has no primary key defined'
            )

            if "pk" not in model_def.properties and model_def.primary_key:
                # There is no ``pk`` property, in the ``properties:`` section,
                # but there is a ``primary_key:`` attribute.  We need to add a
                # ``pk`` property that is an alias for the primary key.
                properties = f'''
    @property
    def pk(self) -> Optional[str]:
        """
        Return the primary key of the model.   This is the value of the
        :py:attr:`{model_def.primary_key}` attribute.

        Returns:
            The primary key of the model instance.
        """
        return self.{model_def.primary_key}
'''
            if model_def.arn_key:
                properties += f'''

    @property
    def arn(self) -> Optional[str]:
        """
        Return the ARN of the model.   This is the value of the
        :py:attr:`{model_def.arn_key}` attribute.

        Returns:
            The ARN of the model instance.
        """
        return self.{model_def.arn_key}
'''

            if model_def.name_key:
                properties += f'''

    @property
    def name(self) -> Optional[str]:
        """
        Return the name of the model.   This is the value of the
        :py:attr:`{model_def.name_key}` attribute.

        Returns:
            The name of the model instance.
        """
        return self.{model_def.name_key}
'''
        # Build any regular properties that were defined in the model definition
        for property_name in model_def.properties:
            if not properties:
                properties = ""
            properties += ModelPropertyGenerator(
                self, model_def.name, property_name
            ).code

        # Now build the relations to other models
        for property_name in model_def.relations:
            if not properties:
                properties = ""
            properties += ModelRelationGenerator(
                self, model_def.name, property_name
            ).code

        # Now build the manager shortcut methods
        for method_name in model_def.manager_methods:
            if not properties:
                properties = ""
            # This acutally needs to be the official name of the model from our
            # botocraft model definition, not the alternate_name if it has one
            properties += ModelManagerMethodGenerator(
                self.service_generator, model_def.name, method_name
            ).code

        return properties

    def get_python_type_for_field(
        self,
        model_name: str,
        field_name: str,
        field_def: ModelAttributeDefinition | None = None,
        model_shape: botocore.model.Shape | None = None,
        field_shape: botocore.model.Shape | None = None,
    ) -> str:
        """
        Return the python type annotation for a field on a model by combining
        the ``model_shape``, ``field_shape`` and ``field_def``.

        Args:
            model_name: The name of the model to get the field from.
            field_name: The name of the field.

        Keyword Args:
            field_def: The botocraft field definition for the field.  If not
                provided, we will look it up in the model definition.
            model_shape: The shape of the model.  If not provided, we will look
                it up in the service model.
            field_shape: The shape of the field.  If not provided, we will look
                it up in the model shape.

        Returns:
            The python type annotation for the field.

        """
        if not model_shape:
            model_shape = self.get_shape(model_name)
        if not hasattr(model_shape, "members"):
            raise ModelHasNoMembersError(model_name)
        if not field_shape:
            field_shape = cast(
                "botocore.model.StructureShape", model_shape
            ).members.get(field_name)
        if not field_def:
            model_def = self.get_model_def(model_name)
            field_def = model_def.fields.get(field_name, ModelAttributeDefinition())
        python_type = field_def.python_type
        if not field_shape and not python_type:
            msg = (
                f"{model_name}.{field_name} has neither a botocore shape nor a "
                "manually defined python_type."
            )
            raise TypeError(msg)
        if not python_type:
            python_type = self.shape_converter.convert(
                cast("botocore.model.StructureShape", field_shape)
            )
        return self.validate_python_type(model_name, field_name, field_def, python_type)

    def validate_python_type(
        self,
        model_name: str,
        field_name: str,
        field_def: ModelAttributeDefinition,
        python_type: str,
    ) -> str:
        """
        After we have guessed the python type for a field, we need to validate
        it to make sure it's not going to cause problems for us later.

        Args:
            model_name: the name of the model
            field_name: the name of the field
            field_def: the botocraft field definition for the field
            python_type: the python type we have guessed for the field

        Raises:
            NoPythonTypeError: we could not determine the type for the field
            TypeError: we have determined that the type for the field is invalid

        Returns:
            The python type annotation for the field on the model.

        """
        if python_type is None:
            raise NoPythonTypeError(field_name, model_name)
        name = field_def.rename if field_def.rename else field_name
        if python_type == name or f"[{name}]" in python_type:
            # If our type annotation is for a model with the same name as the field
            # we'll get recursion errors when trying to import the file.  Quoting
            # the type annotation fixes this sometimes.
            python_type = f'"{python_type}"'
        if field_def.readonly and (
            python_type == f'"{name}"' or f'["{name}"]' in python_type
        ):
            # If the field is readonly, and the type is equal to the field name,
            # even if it is quoted, we will get a "TypeError: forward references
            # must evaluate to types".  This happens because when the field is
            # readonly, we set it equal to ``Field(frozen=True, default=None)``.
            # This causes python typing a lot of consternation, and it throws
            # the TypeError.
            msg = (
                f"Field {model_name}.{name} has type equal to its name, "
                'but is marked as readonly.  This will cause a "TypeError: forward '
                'references must evaluate to types". Fix this in '
                f"botocraft/data/{self.service_generator.aws_service_name}/models.yml ."
                "by either giving an alternate_name for the model named {name} or "
                f"by renaming the field {model_name}.{name} with the rename attribute."
            )
            raise TypeError(msg)
        if not field_def.required and (
            python_type == f'"{name}"' or f'["{name}"]' in python_type
        ):
            # If the field is optional with a None default value, and the type
            # is equal to the field name, pydantic will throw an exception when
            # trying to load data into that field: "ValidationError: Input
            # should be None".  This happens even the type is quoted.
            msg = (
                f"Field {model_name}.{name} has type equal to its name, "
                'but is marked as optional.  This will cause a "ValidationError: Input '
                'should be None" exception from pydantic when trying to load data '
                "into this field.  Fix this in "
                f"botocraft/data/{self.service_generator.aws_service_name}/models.yml ."
                "by either giving an alternate_name for the model named {name} or "
                f"by renaming the field {model_name}.{name} with the rename attribute."
            )
            raise TypeError(msg)

        return python_type

    def format_fields_from_botocore_shape(
        self,
        model_name: str,
        model_def: ModelDefinition,
        model_shape: botocore.model.Shape | None = None,
    ) -> List[str]:
        """
        Return the python code representing all the fields for a model from the
        botocore shape.  This is used to generate the fields for a model when we
        do have a botocore shape for it.

        Args:
            model_name: The name of the model to generate
            model_def: The botocraft model definition for this model

        Keyword Args:
            model_shape: The botocore shape to generate the model for

        Returns:
            The list of python code representing the pydantic model fields as
            strings

        """
        return self.fields_formatter.format_fields(model_name, model_def, model_shape)

    def handle_tag_class(
        self,
        model_def: ModelDefinition,
        base_class: str,
    ) -> ModelTagsDAO:
        """
        Determine whether we need to add
        :py:class:`~botocraft.mixins.tags.TagsDictMixin` as a mixin for the
        model, and if so, what the name of the tag class is.

        If the model has a ``Tags`` or ``TagList`` field case was, we will add
        the :py:model:`~botocraft.mixins.tags.TagsDictMixin` class to the base
        class for this model.  This is used to add the ``tags`` model property
        that is a writable dictionary of tags for the model instead of a list of
        dicts, as AWS uses.

        Args:
            model_def: The botocraft model definition for this model.
            base_class: The current base class(es) for this model.

        Returns:
            The new set of base classes for this model, possibly including the
            ``TagsDictMixin`` class.

        """
        model_name = model_def.name
        if model_def.bespoke:
            # If this is a bespoke model, we need just look at the
            # ModelDefinition.extra_fields for the tags field -- there won't
            # be a botocore shape for this model.   model_fields here are the
            # definitoins for the extra fields in the botocraft model definition.
            model_fields = model_def.extra_fields
        else:
            # This is a botocore model, so we need to get the fields from the
            # botocore model shape.  THis includes the extra fields that are
            # manually defined in the botocraft model definition.  This is
            # a list of model field definitions, augmented from data from the
            # corresponding members of the botocore shappe.
            model_fields = self.botocore_shape_field_defs(model_name)
        field_names = {name.lower(): name for name in model_fields}

        # See if we need to add the TagsDictMixin
        tag_class: str | None = None
        tag_attr: str | None = None
        for name in ["tags", "taglist"]:
            if name in field_names:
                # set the tag_attr to the normally capitalized name of the field
                # in the model definition
                tag_attr = field_names[name]
                break
        if tag_attr:
            # We do have tags defined in the model definition
            if tag_attr != "Tags" and model_fields[tag_attr].rename != "Tags":
                warnings.warn(  # noqa: B028
                    f'Model {model_name} has a field named "tags".  Rename it '
                    'to "Tags" in the model definition.'
                )
            # Extract the name of the tag class from the python type annotation.
            # Different services use different types for tags.
            if model_def.bespoke:
                # If this is a bespoke model, we need to look at the
                # ModelDefinition.extra_fields for the tags field -- there won't
                # be a botocore shape for this model.
                tag_class = model_fields[tag_attr].python_type
                assert tag_class, (
                    f"Bespoke Model {model_name} has a Tag field named "
                    f"{tag_attr} but no python type annotation for it."
                )
            else:
                tag_class = self.get_python_type_for_field(
                    model_name, tag_attr, model_fields[tag_attr]
                )
            if tag_class == "Dict[str, str]":
                # Almost all tags are stored as List[Dict[str, str]] in the
                # botocore model, but some oddballs are actually stored in
                # the exact form we want: Dict[str, str].  In this case, we
                # don't need to add the TagsDictMixin class.
                tag_class = None
            else:
                tag_class = re.sub(r"List\[(.*)\]", r"\1", tag_class)
                tag_class = re.sub(r'"(.*)"', r"\1", tag_class)
                base_class = f"TagsDictMixin, {base_class}"
        return ModelTagsDAO(base_class=base_class, tag_class=tag_class)

    def generate_single_model(  # noqa: PLR0912
        self, model_name: str, model_shape: botocore.model.Shape | None = None
    ) -> str:
        """
        Generate the code for a single model and its dependent models and save
        them to :py:attr:`classes`.

        Args:
            model_name: The name of the model to generate. This will be the
                name of the class.

        Keyword Args:
            model_shape: The botocore shape to generate the model for.  If not provided,
                we will look it up in the service model.

        Side Effects:
            This may add new models to :py:attr:`classes` and new imports to
            :py:attr:`imports`.

        Returns:
            The name of the model class that was generated.

        """
        # Save the original model name so we can use it later when
        # we're looking up the model definition and fields.
        orig_model_name = model_name
        if model_name in self.classes:
            # If we've already generated this model, just return it.
            return model_name

        # The list of Python code lines for this model representing the
        # pydantic model fields.
        field_code: List[str] = []

        # Get the model definition for this model from the service definition
        # file in ``botocraft/data/<service_name>/models.yml``.
        model_def = self.get_model_def(model_name)
        # Handle the case where the model name is different from the
        # botocore model name.
        if model_def.alternate_name:
            model_name = model_def.alternate_name
        # Get the base class for this model
        base_class = cast("str", model_def.base_class)

        if model_def.bespoke:
            # This is not a botocore model, so we just add the code for the
            # fields defined in the ModelDefinition.extra_fields attribute.
            field_code = self.format_extra_fields_from_model_def(model_def)
        else:
            # This is a botocore model, so we generate the code for fields from a
            # combination of the botocore model shape and the botocraft model
            # definition, including any extra fields that are defined in the
            # botocraft model definition.
            model_shape = self.get_shape(orig_model_name)
            field_code = self.format_fields_from_botocore_shape(
                orig_model_name, model_def, model_shape=model_shape
            )

        # Add any botocraft defined properties.  This includes relations.
        properties = self.get_properties(model_def, base_class)

        # Add any botocraft defined mixins to the class inheritance
        if model_def.mixins:
            for mixin in model_def.mixins:
                self.imports.add(f"from {mixin.import_path} import {mixin.name}")
            base_class = ", ".join(
                [mixin.name for mixin in model_def.mixins] + [base_class]
            )

        tags_dao = self.handle_tag_class(model_def, base_class)
        code: str = f"class {model_name}({tags_dao.base_class}):\n"
        if model_shape:
            # If we have a botocore shape for this model, get the docstring
            # for the class from the shape.
            docstring = self.docformatter.format_docstring(model_shape.documentation)
        else:
            # If we don't have a botocore shape for this model, get the
            # docstring from the botocraft model definition, if it exists.
            _docstring = model_def.docstring if model_def.docstring else None
            if _docstring:
                docstring = self.docformatter.format_docstring(_docstring)
            else:
                # If we don't have a docstring, we need to set it to None
                # so that the docformatter doesn't try to format it.
                docstring = None
        if docstring:
            code += f'    """{docstring}"""\n'
        if tags_dao.tag_class:
            # The ``tag_class`` attribute is the class that will be used to
            # represent the tags in the model.  This is used by TagsDictMixin
            # to convert the tags to a dictionary of tag key/value pairs.
            code += f"    tag_class: ClassVar[Type] = {tags_dao.tag_class}\n"
        if "PrimaryBoto3Model" in base_class:
            if model_def.alternate_name:
                manager_name = f"{model_def.alternate_name}Manager"
            else:
                manager_name = f"{model_name}Manager"
            code += f"    manager_class: ClassVar[Type[Boto3ModelManager]] = {manager_name}\n\n"  # noqa: E501
        if field_code:
            code += "\n".join(field_code)
        if properties:
            code += f"\n{properties}"
        if not field_code and not properties:
            code += "    pass"
        # Add the class to the list so we only generate it once and can
        # write it out to the file later.
        self.classes[model_name] = code
        assert code, (
            f"Model {model_name} has no fields or properties defined.  This is "
            "probably a bug in the botocraft model definition or generator code."
        )
        return model_name


class ManagerGenerator(AbstractGenerator):
    """
    Generates the code for the manager class for a service.

    Args:
        service_generator: The :py:class:`ServiceGenerator` we're generating
            models for.

    """

    #: A mapping of botocore operation names to the method generator class that
    #: will generate the code for that method.
    METHOD_GENERATORS: Final[Dict[str, Type[ManagerMethodGenerator]]] = {
        "create": CreateMethodGenerator,
        "update": UpdateMethodGenerator,
        "partial_update": PartialUpdateMethodGenerator,
        "delete": DeleteMethodGenerator,
        "get": GetMethodGenerator,
        "get_many": GetManyMethodGenerator,
        "list": ListMethodGenerator,
    }

    def __init__(self, service_generator: "ServiceGenerator") -> None:
        super().__init__(service_generator)
        self.model_generator = self.service_generator.model_generator
        self.shape_converter = self.model_generator.shape_converter
        self.client = boto3.client(self.service_name)  # type: ignore[call-overload]

    def generate_manager(self, model_name: str, manager_def: ManagerDefinition) -> None:
        """
        Generate the code for a single manager, and its dependent response
        classes and save them to :py:attr:`classes`.

        Args:
            model_name: The name of the model to generate the manager for.
            manager_def: The botocraft manager definition for the manager.

        """
        methods: OrderedDict[str, str] = OrderedDict()
        for method_name, method_def in manager_def.methods.items():
            generator = self.get_method_generator(model_name, method_name, method_def)
            methods[method_name] = generator.code
        method_code = "\n\n".join(methods.values())
        base_class = "Boto3ModelManager"
        model_def = self.model_generator.get_model_def(model_name)
        if model_def.alternate_name:
            manager_name = f"{model_def.alternate_name}Manager"
        else:
            manager_name = f"{model_name}Manager"

        # Add any botocraft defined mixins to the class inheritance
        if manager_def.mixins:
            for mixin in manager_def.mixins:
                self.imports.add(f"from {mixin.import_path} import {mixin.name}")
            base_class = ", ".join(
                [mixin.name for mixin in manager_def.mixins] + [base_class]
            )

        # If this is a readonly manager, we need to use the readonly manager
        # base class
        if manager_def.readonly:
            base_class = "ReadonlyBoto3ModelManager"
        code = f"""


class {manager_name}({base_class}):

    service_name: str = '{self.service_name}'

{method_code}
"""
        self.classes[manager_name] = code

    def get_method_generator(
        self, model_name: str, method_name: str, method_def: ManagerMethodDefinition
    ) -> ManagerMethodGenerator:
        """
        Return the appropriate method generator class for a given method
        definition.

        Args:
            model_name: the model name for the manager we're generating
            method_name: the name of the method we're generating
            method_def: the method definition for the method we're generating

        Returns:
            A method generator class.

        """
        try:
            method_generator_class = self.METHOD_GENERATORS[method_name]
        except KeyError:
            # We have no specific method generator for this method, so we
            # will use the general method generator.
            generator: ManagerMethodGenerator = GeneralMethodGenerator(
                self, model_name, method_def, method_name=method_name
            )
        else:
            # We have a specific method generator for this method, so we
            # will use that.
            generator = method_generator_class(self, model_name, method_def)

        return generator

    def generate_all_manager_models(self) -> None:
        for model_name, manager_def in self.service_def.managers.items():
            self.generate_manager(model_name, manager_def)
        self.imports.update(self.model_generator.imports)


class ServiceGenerator:
    """
    Generate the code for a single AWS service.

    This means:

        * Managers
        * Service Models
        * Request/Response Models

    Args:
        service_def: The :py:class:`ServiceDefinition` for the service we are
            generating code for.

    """

    service_path: Path = Path(__file__).parent.parent / "services"

    def __init__(self, service_def: ServiceDefinition) -> None:
        #: The service definition
        self.service_def = service_def
        #: The botocraft interface object, where we will collect all our global data
        self.interface = service_def.interface
        #: A set of model imports we need to add to the top of the file
        self.imports: Set[str] = {
            "from datetime import datetime",
            "from typing import ClassVar, Type, Optional, Literal, Dict, List, Union, Any, cast",  # noqa: E501
            "from pydantic import Field",
            "from .abstract import Boto3Model, ReadonlyBoto3Model, PrimaryBoto3Model, "
            "ReadonlyPrimaryBoto3Model, Boto3ModelManager, ReadonlyBoto3ModelManager",
            "from botocraft.mixins.tags import TagsDictMixin",
        }
        #: A dictionary of model names to class code.  This is populated by
        #: service models
        self.model_classes: Dict[str, str] = {}
        #: A dictionary of botocore response classes names to class code. This
        #: is populated when we build the manager classes
        self.response_classes: Dict[str, str] = {}
        #: A dictionary of manager classes names to class code. This is populated
        #: when we build the manager classes
        self.manager_classes: Dict[str, str] = {}
        #: The :py:class:`ModelGenerator` class we will use to generate models
        self.model_generator = ModelGenerator(self)
        #: The :py:class:`ManagerGenerator` class we will use to generate managers
        self.manager_generator = ManagerGenerator(self)
        #: The :py:class:`ManagerGenerator` class we will use to generate managers
        self.sphinx_generator = ServiceSphinxDocBuilder(self)

    @property
    def aws_service_name(self) -> str:
        """
        Return the boto3 service name for this service.
        """
        return self.service_def.name

    @property
    def safe_service_name(self) -> str:
        """
        Return the safe service name for this service.  This is the name we
        use to generate the file name for the service.
        """
        return self.service_def.safe_service_name

    @property
    def service_full_name(self) -> str:
        """
        Return what AWS thinks the full name of this services is.

        Returns:
            The full name of the service, as defined in the botocore service.

        """
        return self.model_generator.service_model.metadata["serviceId"]

    @property
    def classes(self) -> Dict[str, str]:
        """
        Return a dictionary of all the classes we have generated.
        """
        return {
            **self.model_classes,
            **self.response_classes,
            **self.manager_classes,
        }

    @property
    def code(self) -> str:
        """
        The code for this service.
        """
        imports = "\n".join(list(self.imports))
        model_classes = "\n\n".join(self.model_classes.values())
        response_classes = "\n\n".join(self.response_classes.values())
        manager_classes = "\n\n".join(self.manager_classes.values())
        return f"""
# This file is automatically generated by botocraft.  Do not edit directly.
# mypy: disable-error-code="index, override, assignment, union-attr, misc"
{imports}

# ===============
# Managers
# ===============

{manager_classes}


# ==============
# Service Models
# ==============

{model_classes}


# =======================
# Request/Response Models
# =======================

{response_classes}

"""

    def generate(self) -> None:
        """
        Generate the code for this service.
        """
        # Generate the service models
        self.model_generator.generate_all_service_models()
        self.model_classes = deepcopy(self.model_generator.classes)
        self.imports.update(self.model_generator.imports)

        # Generate the service managers and request/response models
        self.manager_generator.generate_all_manager_models()
        # We have to do this because very occasionaly there are no real
        # primary models, and we use a response model as one.  Thus we need
        # to remove any primary models from the response classes
        self.response_classes = {
            k: v
            for k, v in self.model_generator.classes.items()
            if k not in self.model_classes
        }
        self.manager_classes = deepcopy(self.manager_generator.classes)
        self.imports.update(self.manager_generator.imports)
        self.model_generator.clear()
        self.manager_generator.clear()

        # Write the generated code to the output file
        self.write()
        # Write the sphinx documentation for the service
        self.sphinx_generator.write()

        # Update the interface with the manager models we generated
        for model_name in self.model_classes:
            self.interface.add_model(model_name, self.service_def.name)
        for model_name in self.response_classes:
            self.interface.add_model(model_name, self.service_def.name)
        for model_name in self.manager_classes:
            self.interface.add_model(model_name, self.service_def.name)

    def write(self) -> None:
        """
        Write the generated code to the output file, and format it with ruff for
        code formatting and auto-fixing, then docformatter for docstring formatting.

        """
        code = self.code
        output_file = self.service_path / f"{self.service_def.safe_service_name}.py"

        # Use ruff to format and auto-fix the code
        with tempfile.TemporaryDirectory(dir=self.service_path) as temp_dir:
            temp_path = Path(temp_dir) / f"{self.service_def.safe_service_name}.py"
            init_path = Path(temp_dir) / "__init__.py"
            with init_path.open("w", encoding="utf-8") as f:
                f.write(
                    '"""This file is automatically generated by botocraft.  Do not edit directly."""\n'  # noqa: E501
                )

            with temp_path.open("w", encoding="utf-8") as f:
                f.write(code)

            try:
                # Format with ruff (replaces black)
                subprocess.run(
                    ["ruff", "format", str(temp_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Fix with ruff (auto-fixes linting issues, including import sorting)
                subprocess.run(
                    ["ruff", "check", "--fix", str(temp_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Read the formatted content
                with temp_path.open("r", encoding="utf-8") as f:
                    formatted_code = f.read()

            except subprocess.CalledProcessError as e:
                # Print the problematic code with line numbers for easier debugging
                code_lines = [
                    f"{i:04} " + line for i, line in enumerate(code.split("\n"))
                ]
                print("\n".join(code_lines))
                print(f"ruff error: {e.stdout}\n{e.stderr}")
                raise

        # Format the docstrings with docformatter
        formatted_code = Formatter(FormatterArgs(), None, None, None)._format_code(  # noqa: SLF001
            formatted_code
        )

        # Write the final formatted code to the output file
        with output_file.open("w", encoding="utf-8") as fd:
            fd.write(formatted_code)
