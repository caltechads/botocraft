from copy import deepcopy
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Set, List, Optional, Type

import black
import black.parsing
import boto3
import botocore.model
import botocore.session
from docformatter.format import Formatter
import isort

from .docstring import DocumentationFormatter, FormatterArgs
from .methods import (  # pylint: disable=import-error
    MethodGenerator,
    ListMethodGenerator,
    GetMethodGenerator,
    CreateMethodGenerator,
    UpdateMethodGenerator,
    DeleteMethodGenerator,
)
from .models import (
    ServiceDefinition,
    ModelAttributeDefinition,
    ModelDefinition,
    ManagerDefinition,
)
from .shapes import PythonTypeShapeConverter


class AbstractGenerator:

    def __init__(self, service_generator: "ServiceGenerator") -> None:
        #: The :py:class:`ServiceGenerator` we're generating models for.
        self.service_generator = service_generator
        #: The name of the AWS service we're generating models for.
        self.service_name = service_generator.aws_service_name
        #: The botocraft service definition for our service.
        self.service_def = service_generator.service_def
        #: The botocraft interface definition.  We collect things we need to know
        #: globally here.
        self.interface = service_generator.interface
        session = botocore.session.get_session()
        #: The botocore service model for our service.
        self.service_model = session.get_service_model(self.service_name)
        #: The documentation formatter we will use to format docstrings.
        self.docformatter = DocumentationFormatter()
        #: The shape converter we will use to convert botocore shapes to python types
        self.shape_converter = PythonTypeShapeConverter()
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
        return (
            self.service_model  # type: ignore  # pylint: disable=protected-access
            ._shape_resolver
            .get_shape_by_name(name)
        )

    def generate(self) -> None:
        raise NotImplementedError


class ModelGenerator(AbstractGenerator):
    """
    Generate pydantic model definitions for a service.
    """

    def get_model_def(self, model_name: str) -> ModelDefinition:
        """
        Return the :py:class:`ModelDefinition` for a model.
        """
        return self.service_def.models.get(model_name, ModelDefinition(name=model_name))

    def generate(self) -> None:
        """
        Generate all the service models.
        """
        for model_name in self.service_def.models:
            self.generate_model(model_name)

    def resolve_type(self, field_shape: botocore.model.Shape) -> str:
        """
        Resolve the Python type for a field shape.

        Args:
            field_shape: The shape to resolve.

        Returns:
            The Python type for the shape.
        """
        try:
            python_type = self.shape_converter.convert(field_shape)
        except ValueError as exc:
            if field_shape.type_name == 'list':
                # This is a list of submodels
                element_shape = field_shape.member  # type: ignore  # pylint: disable=no-member
                inner_model_name: str = element_shape.name
                if inner_model_name == 'String' or element_shape.type_name == 'string':
                    inner_model_name = self.shape_converter.convert(element_shape)
                else:
                    self.generate_model(inner_model_name, shape=element_shape)
                    inner_model_name = f'"{inner_model_name}"'
                python_type = f'List[{inner_model_name}]'
            elif field_shape.type_name == 'map':
                # This is a map of submodels.  I'm assuming here that the key
                # and value types are simple types like String or Integer.
                value_type = self.shape_converter.convert(field_shape.key)  # type: ignore  # pylint: disable=no-member
                key_type = self.shape_converter.convert(field_shape.value)  # type: ignore  # pylint: disable=no-member
                python_type = f'Dict[{key_type}, {value_type}]'
            elif field_shape.type_name == 'structure':
                # This is a submodel
                inner_model_name = field_shape.name
                self.generate_model(inner_model_name, shape=field_shape)
                python_type = f'"{inner_model_name}"'
            elif field_shape.name in ['Timestamp', 'DateTime']:
                python_type = 'datetime'
                self.imports.add('from datetime import datetime')
            else:
                raise ValueError(
                    f'Could not resolve type for field {field_shape.name}.  Shape: {field_shape}.'
                ) from exc
        return python_type

    def extra_fields(self, model_def: ModelDefinition) -> List[str]:
        """
        Build out the extra fields for a model.

        Extra fields are fields that are in the output of the
        create/get/list/update methods but not in actual models.  We add them to
        the models so that we can load them from the API responses.

        Extra fields are exclusively defined in the botocore model definition.  We
        add them manually to the model definition by inspecting the response shape
        for the create/get/list/update methods and adding any fields that aren't
        already defined in the service model shape.

        Args:
            model_def: The botocraft model definition for this model

        Returns:
            A list of extra fields.
        """
        fields: List[str] = []
        for field_name, field_def in getattr(model_def, 'extra_fields', {}).items():
            if field_def.docstring:
                fields.append(
                    self.docformatter.format_attribute(field_def.docstring)
                )
            field = f'    {field_name}: {field_def.python_type}'
            if field_def.readonly:
                _default = f', default={field_def.default}' if field_def.default else ''
                field += f' = Field(frozen=True{_default})'
            elif field_def.default:
                field += f' = {field_def.default}'
            self.imports.update(field_def.imports)
            fields.append(field)
        return fields

    def generate_model(
        self,
        model_name: str,
        shape: Optional[botocore.model.Shape] = None
    ) -> None:
        """
        Generate the code for a single model and its dependent models and save
        them to :py:attr:`classes`.

        Args:
            model_name: The name of the model to generate. This will be the
                name of the class.

        Side Effects:
            This may add new models to :py:attr:`classes` and new imports to
            :py:attr:`imports`.

        Keyword Args:
            shape: The shape to generate the model for.  If not provided, we
                will look it up in the service model.
        """
        fields: List[str] = []

        model_def = self.get_model_def(model_name)
        if not shape:
            shape = self.get_shape(model_name)
        if model_def.alternate_name:
            model_name = model_def.alternate_name
        if model_name in self.classes or model_name in self.service_generator.classes:
            # We've already generated this model
            return
        if model_name in self.interface.models:
            # This is a model that we're importing from another service
            import_path = self.interface.models[model_name]
            self.imports.add(f'from {import_path} import {model_name}')
            return

        if hasattr(shape, 'members'):
            for field_name, field_shape in shape.members.items():
                #: The botocraft definition for this field
                field_def = model_def.fields.get(field_name, ModelAttributeDefinition())
                # Our guess as to the python type for this field
                python_type: Optional[str] = field_def.python_type or self.resolve_type(field_shape)
                # Whether this field is required
                required: bool = (field_name in shape.required_members) or field_def.required

                if python_type is None:
                    raise ValueError(
                        f'Could not resolve type for field {field_name} in {model_name}.  Shape: {field_shape}.'
                    )
                default = None
                if not required:
                    python_type = f'Optional[{python_type}]'
                    if field_def.default is None:
                        default = 'None'
                # Add the docstring for this field
                fields.append(
                    self.docformatter.format_attribute(field_shape.documentation)
                )
                field_line = f'    {field_name}: {python_type}'
                if field_def.readonly:
                    _default = f', default={field_def.default}' if field_def.default else ''
                    field_line += f' = Field(frozen=True{_default})'
                elif default:
                    field_line += f' = {field_def.default}'
                fields.append(field_line)
            fields.extend(self.extra_fields(model_def))

            base_class = 'Boto3Model'
            if model_def.readonly:
                base_class = 'ReadonlyBoto3Model'

            code: str = f'class {model_name}({base_class}):\n'
            docstring = self.docformatter.format_docstring(shape)
            if docstring:
                code += f'    """{docstring}"""\n'
            if fields:
                code += '\n'.join(fields)
            else:
                code += '    pass'
            self.classes[model_name] = code


class ManagerGenerator(AbstractGenerator):

    #: A mapping of botocore operation names to the method generator class that
    #: will generate the code for that method.
    METHOD_GENERATORS: Dict[str, Type[MethodGenerator]] = {
        'create': CreateMethodGenerator,
        'update': UpdateMethodGenerator,
        'delete': DeleteMethodGenerator,
        'get': GetMethodGenerator,
        'list': ListMethodGenerator,
    }

    def __init__(self, service_generator: "ServiceGenerator") -> None:
        super().__init__(service_generator)
        self.model_generator = self.service_generator.model_generator
        self.client = boto3.client(self.service_name)  # type: ignore

    def generate_manager(
        self,
        model_name: str,
        manager_def: ManagerDefinition
    ) -> None:
        """
        Generate the code for a single manager, and its dependent response
        classes and save them to :py:attr:`classes`.

        Args:
            model_name: The name of the model to generate the manager for.
        """
        methods: OrderedDict[str, str] = OrderedDict()
        for operation_name, operation_def in manager_def.operations.items():
            try:
                method_generator_class = self.METHOD_GENERATORS[operation_name]
            except KeyError as exc:
                raise NotImplementedError(
                    f'{self.service_name}:{model_name}Manager: No method generator for operation {operation_name}'
                ) from exc

            generator = method_generator_class(
                self,
                model_name,
                operation_def
            )
            methods[operation_name] = generator.code
        method_code = '\n\n'.join(methods.values())
        code = f"""


class {model_name}Manager:

    service_name: str = '{self.service_name}'

    def __init__(self) -> None:
        #: The boto3 client for the AWS service
        self.client = boto3.client(self.service_name)  # type: ignore

{method_code}
"""
        self.classes[f'{model_name}Manager'] = code

    def generate(self) -> None:
        for model_name, manager_def in self.service_def.managers.items():
            self.generate_manager(model_name, manager_def)


class ServiceGenerator:
    """
    Generate the code for a single AWS service.
    """

    service_path: Path = Path(__file__).parent.parent / 'services'

    def __init__(self, service_def: ServiceDefinition) -> None:
        #: The service definition
        self.service_def = service_def
        #: The botocraft interface object, where we will collect all our global data
        self.interface = service_def.interface
        #: A set of model imports we need to add to the top of the file
        self.imports: Set[str] = set(
            [
                'from datetime import datetime',
                'from typing import Optional, Literal, Dict, List, cast',
                'import boto3',
                'from pydantic import Field',
                'from .abstract import Boto3Model, ReadonlyBoto3Model',
            ]
        )
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

    @property
    def aws_service_name(self) -> str:
        """
        Return the boto3 service name for this service.
        """
        return self.service_def.name

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
        imports = '\n'.join(list(self.imports))
        model_classes = '\n\n'.join(sorted(self.model_classes.values()))
        response_classes = '\n\n'.join(sorted(self.response_classes.values()))
        manager_classes = '\n\n'.join(sorted(self.manager_classes.values()))
        return f"""
# This file is automatically generated by botocraft.  Do not edit directly.
{imports}


# ==============
# Service Models
# ==============

{model_classes}


# =======================
# Request/Response Models
# =======================

{response_classes}

# ===============
# Managers
# ===============

{manager_classes}
"""

    def generate(self) -> None:
        """
        Generate the code for this service.
        """
        # Generate the service models
        self.model_generator.generate()
        self.model_classes = deepcopy(self.model_generator.classes)
        self.imports.update(self.model_generator.imports)
        self.model_generator.clear()

        # Generate the service managers and response models
        self.manager_generator.generate()
        self.response_classes = deepcopy(self.model_generator.classes)
        self.manager_classes = deepcopy(self.manager_generator.classes)
        self.imports.update(self.manager_generator.imports)
        self.model_generator.clear()

        self.write()

        # Update the interface with the models we generated
        for model_name in self.model_classes:
            self.interface.add_model(model_name, self.service_def.name)
        for model_name in self.response_classes:
            self.interface.add_model(model_name, self.service_def.name)
        for model_name in self.manager_classes:
            self.interface.add_model(model_name, self.service_def.name)

    def write(self) -> None:
        """
        Write the generated code to the output file, and format it with black,
        and with docformatter.

        Args:
            code: the code to write to the output file.
        """
        code = self.code
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
        except (KeyError, black.parsing.InvalidInput):
            print(code)
            raise
        formatted_code = isort.code(formatted_code)
        formatted_code = Formatter(FormatterArgs(), None, None, None)._format_code(formatted_code)
        output_file = self.service_path / f'{self.service_def.name}.py'
        with open(output_file, 'w', encoding='utf-8') as fd:
            fd.write(formatted_code)
