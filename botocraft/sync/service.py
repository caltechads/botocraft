import re
import warnings
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Set, Type, cast

import black
import black.parsing
import boto3
import botocore.model
import botocore.session
import isort
from docformatter.format import Formatter

from .docstring import DocumentationFormatter, FormatterArgs
from .methods import (  # pylint: disable=import-error
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
        self.classes: OrderedDict[str, str] = OrderedDict()
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

    def generate(self) -> None:
        raise NotImplementedError


class ModelGenerator(AbstractGenerator):
    """
    Generate pydantic model definitions from botocore shapes.
    """

    def __init__(self, service_generator: "ServiceGenerator") -> None:
        super().__init__(service_generator)
        #: The shape converter we will use to convert botocore shapes to python
        #: types, and build the appropriate python classes for ``StructureShape``
        #: objects.
        self.shape_converter = PythonTypeShapeConverter(service_generator, self)

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

    def add_extra_fields(
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
            model_fields with the extra fields added

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

    def fields(self, model_name: str) -> Dict[str, ModelAttributeDefinition]:
        """
        Return the fields for a botocore shape as a dictionary of field names to
        botocraft field definitions.  This incorporates settings from the
        :py:class:`ModelAttributeDefinitions` from the  ``fields`` attribute of
        the associated model definition, if it exists.

        Note:
            This really only makes sense on :py:class:`botocore.model.StructureShape`
            objects, since they are the only ones that have fields (aka "members").

        Side Effects:
            We set :py:attr:`ModelAttributeDefinition.botocore_shape` on each
            field definition, and we set :py:attr:`ModelAttributeDefinition.readonly`
            if the field is not in any of the input shapes for the model.

        Returns:
            A dictionary of field names to field definitions.

        """
        model_def = self.get_model_def(model_name)
        fields: Dict[str, ModelAttributeDefinition] = deepcopy(model_def.fields)
        model_shape = self.get_shape(model_name)
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
        fields = self.add_extra_fields(model_name, fields)
        return fields  # noqa: RET504

    def generate(self) -> None:
        """
        Generate all the service models.
        """
        for model_name in self.service_def.primary_models:
            _ = self.generate_model(model_name)

    def extra_fields(self, model_def: ModelDefinition) -> List[str]:
        """
        Build out the manually defined extra fields for a model.

        Extra fields are exclusively defined in the botocore model definition.
        We add them manually to the model definition by inspecting the response
        shape for the create/get/list/update methods and adding any fields that
        aren't already defined in the service model shape.

        Args:
            model_def: The botocraft model definition for this model

        Returns:
            A list of extra fields.

        """
        fields: List[str] = []
        for field_name, field_def in getattr(model_def, "extra_fields", {}).items():
            if field_def.docstring:
                fields.append(self.docformatter.format_attribute(field_def.docstring))
            field = f"    {field_name}: {field_def.python_type}"
            if field_def.readonly:
                field = re.sub(r"Optional\[(.*)\]", r"\1", field)
                _default = f", default={field_def.default}" if field_def.default else ""
                field += f" = Field(frozen=True{_default})"
            elif field_def.default:
                field += f" = {field_def.default}"
            self.imports.update(field_def.imports)
            fields.append(field)
        return fields

    def get_properties(
        self, model_def: ModelDefinition, base_class: str
    ) -> Optional[str]:
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
            assert (
                model_def.primary_key or "pk" in model_def.properties
            ), f'Primary service model "{model_def.name}" has no primary key defined'

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
            properties += ModelManagerMethodGenerator(
                self.service_generator, model_def.name, method_name
            ).code

        return properties

    def field_type(
        self,
        model_name: str,
        field_name: str,
        field_def: Optional[ModelAttributeDefinition] = None,
        model_shape: Optional[botocore.model.Shape] = None,
        field_shape: Optional[botocore.model.Shape] = None,
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
            msg = f"Model {model_name} has no fields."
            raise ValueError(msg)
        if not field_shape:
            field_shape = cast(botocore.model.StructureShape, model_shape).members.get(
                field_name
            )
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
                cast(botocore.model.StructureShape, field_shape)
            )
        return self.validate_type(model_name, field_name, field_def, python_type)

    def validate_type(
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
            ValueError: we could not determine the type for the field
            TypeError: we have determined that the type for the field is invalid

        Returns:
            The python type annotation for the field on the model.

        """
        if python_type is None:
            msg = f"Could not determine type for field {field_name}."
            raise ValueError(msg)
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

    def generate_model(  # noqa: PLR0912, PLR0915
        self, model_name: str, model_shape: Optional[botocore.model.Shape] = None
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
        # The list of fields for this model
        fields: List[str] = []

        # Get the model definition for this model from the service definition
        # file in ``botocraft/data/<service_name>/models.yml``.
        model_def = self.get_model_def(model_name)
        # Get the base class for this model
        base_class = cast(str, model_def.base_class)
        # This needs to be up here before we check for alternate names
        model_fields = self.fields(model_name)
        if not model_shape:
            model_shape = self.get_shape(model_name)
        if model_def.alternate_name:
            model_name = model_def.alternate_name

        if hasattr(model_shape, "members"):
            # Get the list of all the fields for this model, along with their
            # botocode definitions.  This includes fields from the botocore model,
            # and any extra fields we have defined in the botocraft model
            # definition.
            for field_name, field_def in model_fields.items():
                # The botocore shape for this field.  We determined this in
                # :py:meth:`fields`.
                field_shape = field_def.botocore_shape
                # Whether this field is required
                required: bool = (
                    field_name in model_shape.required_members
                ) or field_def.required
                docstring = field_def.docstring
                # Deterimine the python type for this field
                if field_shape:
                    python_type = self.field_type(
                        model_name,
                        field_name,
                        model_shape=model_shape,
                        field_def=field_def,
                        field_shape=field_shape,
                    )
                    if not docstring:
                        docstring = cast(str, field_shape.documentation)
                else:
                    assert field_def.python_type, (
                        f"Field {field_name} in model {model_name} has no botocore "
                        "shape or python type"
                    )
                    python_type = field_def.python_type
                default = None
                if not required:
                    if not field_def.readonly and not field_def.rename:
                        python_type = f"Optional[{python_type}]"
                    default = "None" if field_def.default is None else field_def.default

                # Determine whether we need to add a pydantic.Field class
                # instance as the value for this field.
                needs_field_class: bool = False
                field_class_args: List[str] = []
                if default:
                    field_class_args.append(f"default={default}" if default else "")
                field_line = f"    {field_name}: {python_type}"
                if field_def.rename:
                    # We need it to be a pydantic Field class instance so that we can
                    # set the serialization_alias attribute.
                    needs_field_class = True
                    field_line = f"    {field_def.rename}: {python_type}"
                    field_class_args.append(f'serialization_alias="{field_name}"')
                if field_def.readonly:
                    # We need it to be a pydantic Field class instance so that we can
                    # set the frozen attribute.
                    needs_field_class = True
                    field_class_args.append("frozen=True")
                if needs_field_class:
                    field_line += f' = Field({", ".join(field_class_args)})'
                elif default:
                    field_line += f" = {field_def.default}"
                fields.append(field_line)
                # Add the docstring for this field
                if docstring:
                    fields.append(self.docformatter.format_attribute(docstring))

            # Add any botocraft defined properties.  This includes relations.
            properties = self.get_properties(model_def, base_class)

            # Add any botocraft defined mixins to the class inheritance
            if model_def.mixins:
                for mixin in model_def.mixins:
                    self.imports.add(f"from {mixin.import_path} import {mixin.name}")
                base_class = ", ".join(
                    [mixin.name for mixin in model_def.mixins] + [base_class]
                )

            # See if we need to add the TagsDictMixin
            tag_class: Optional[str] = None
            has_tags: bool = False
            field_names = {name.lower(): name for name in model_fields}
            if "tags" in field_names:
                # We do have tags defined in the model definition
                has_tags = True
                tag_attr = field_names["tags"]
                if tag_attr == "tags":
                    if model_fields[tag_attr].rename != "Tags":
                        warnings.warn(  # noqa: B028
                            f'Model {model_name} has a field named "tags".  Rename it '
                            'to "Tags" in the model definition.'
                        )
                # Extract the name of the tag class from the python type annotation.
                # Different services use different types for tags.
                tag_class = self.field_type(
                    model_name, tag_attr, model_fields[tag_attr]
                )
                tag_class = re.sub(r"List\[(.*)\]", r"\1", tag_class)
                tag_class = re.sub(r'"(.*)"', r"\1", tag_class)
            if has_tags:
                base_class = f"TagsDictMixin, {base_class}"

            # Actually build the class code
            code: str = f"class {model_name}({base_class}):\n"
            docstring = self.docformatter.format_docstring(model_shape)
            if docstring:
                code += f'    """{docstring}"""\n'
            if has_tags:
                code += f"    tag_class: ClassVar[Type] = {tag_class}\n"
            if "PrimaryBoto3Model" in base_class:
                if model_def.alternate_name:
                    manager_name = f"{model_def.alternate_name}Manager"
                else:
                    manager_name = f"{model_name}Manager"
                code += f"    manager_class: ClassVar[Type[Boto3ModelManager]] = {manager_name}\n\n"  # noqa: E501
            if fields:
                code += "\n".join(fields)
            if properties:
                code += f"\n{properties}"
            if not fields and not properties:
                code += "    pass"
            self.classes[model_name] = code
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

    def generate(self) -> None:
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
            "from typing import ClassVar, Type, Optional, Literal, Dict, List, Any, cast",  # noqa: E501
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
# pylint: disable=anomalous-backslash-in-string,unsubscriptable-object,line-too-long,arguments-differ,arguments-renamed,unused-import,redefined-outer-name
# pyright: reportUnusedImport=false
# mypy: disable-error-code="index, override, assignment"
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

"""  # noqa: E501

    def generate(self) -> None:
        """
        Generate the code for this service.
        """
        # Generate the service models
        self.model_generator.generate()
        self.model_classes = deepcopy(self.model_generator.classes)
        self.imports.update(self.model_generator.imports)
        self.model_generator.clear()

        # Generate the service managers and request/response models
        self.manager_generator.generate()
        self.response_classes = deepcopy(self.model_generator.classes)
        self.manager_classes = deepcopy(self.manager_generator.classes)
        self.imports.update(self.manager_generator.imports)
        self.model_generator.clear()

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
        Write the generated code to the output file, and format it with black,
        isort, and docformatter.

        Args:
            code: the code to write to the output file.

        """
        code = self.code
        # First format the code with black so we fix most of the formatting
        # issues.
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
        except (KeyError, black.parsing.InvalidInput):  # pylint: disable=c-extension-no-member
            code = [f"{i:04} " + line for i, line in enumerate(code.split("\n"))]
            print("\n".join(code))
            raise
        # Now sort the imports with isort
        formatted_code = isort.code(formatted_code)
        # Finally format the docstrings with docformatter
        formatted_code = Formatter(FormatterArgs(), None, None, None)._format_code(  # noqa: SLF001
            formatted_code
        )
        output_file = self.service_path / f"{self.service_def.name}.py"
        with output_file.open("w", encoding="utf-8") as fd:
            fd.write(formatted_code)
