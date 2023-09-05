from copy import deepcopy
from collections import OrderedDict
from pathlib import Path
import re
from typing import Dict, Set, List, Optional, Type, cast

import black
import black.parsing
import boto3
import botocore.model
import botocore.session
from docformatter.format import Formatter
import isort

from .docstring import DocumentationFormatter, FormatterArgs
from .methods import (  # pylint: disable=import-error
    ManagerMethodGenerator,
    ListMethodGenerator,
    GetMethodGenerator,
    GetManyMethodGenerator,
    CreateMethodGenerator,
    UpdateMethodGenerator,
    PartialUpdateMethodGenerator,
    DeleteMethodGenerator,
    ModelPropertyGenerator,
    GeneralMethodGenerator,
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
        #: The botocraft interface definition.  We collect things we need to
        #: know globally here.
        self.interface = service_generator.interface
        session = botocore.session.get_session()
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
        return self.service_model.shape_for(name)

    def generate(self) -> None:
        raise NotImplementedError


class ModelGenerator(AbstractGenerator):
    """
    Generate pydantic model definitions for a service.
    """

    def __init__(self, service_generator: "ServiceGenerator") -> None:
        super().__init__(service_generator)
        self.shape_converter = PythonTypeShapeConverter(service_generator, self)

    def get_model_def(self, model_name: str) -> ModelDefinition:
        """
        Return the :py:class:`ModelDefinition` for a model.
        """
        if model_name in self.service_def.primary_models:
            defn = self.service_def.primary_models[model_name]
            if defn.readonly:
                defn.base_class = 'ReadonlyPrimaryBoto3Model'
            else:
                defn.base_class = 'PrimaryBoto3Model'
            return defn
        elif model_name in self.service_def.secondary_models:
            defn = self.service_def.secondary_models[model_name]
            if defn.readonly:
                defn.base_class = 'ReadonlyBoto3Model'
            else:
                defn.base_class = 'Boto3Model'
            return defn
        return ModelDefinition(base_class='Boto3Model', name=model_name)

    def fields(self, model_name: str) -> Dict[str, ModelAttributeDefinition]:
        """
        Return the fields for a botocore shape as a dictionary of field names to
        field definitions.  This incorporates settings from the
        :py:class:`ModelAttributeDefinitions` from the  ``fields`` attribute of
        the associated model definition, if it exists.

        .. note::
            This really only makes sense on `botocore.model.StructureShape`
            objects, since they are the only ones that have fields.

        Returns:
            A dictionary of field names to field definitions.
        """
        fields: Dict[str, ModelAttributeDefinition] = deepcopy(
            self.get_model_def(model_name).fields
        )
        model_shape = self.get_shape(model_name)
        if hasattr(model_shape, 'members'):
            for field in model_shape.members:
                if field not in fields:
                    fields[field] = ModelAttributeDefinition()
                    if field in model_shape.required_members:
                        fields[field].required = True
        return fields

    def generate(self) -> None:
        """
        Generate all the service models.
        """
        for model_name in self.service_def.primary_models:
            _ = self.generate_model(model_name)

    def extra_fields(self, model_def: ModelDefinition) -> List[str]:
        """
        Build out the extra fields for a model.

        Extra fields are fields that are in the output of the
        create/get/list/update methods but not in actual models.  We add them to
        the models so that we can load them from the API responses.

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
        for field_name, field_def in getattr(model_def, 'extra_fields', {}).items():
            if field_def.docstring:
                fields.append(
                    self.docformatter.format_attribute(field_def.docstring)
                )
            field = f'    {field_name}: {field_def.python_type}'
            if field_def.readonly:
                field = re.sub(r'Optional\[(.*)\]', r'\1', field)
                _default = f', default={field_def.default}' if field_def.default else ''
                field += f' = Field(frozen=True{_default})'
            elif field_def.default:
                field += f' = {field_def.default}'
            self.imports.update(field_def.imports)
            fields.append(field)
        return fields

    def get_properties(
        self,
        model_def: ModelDefinition,
        base_class: str
    ) -> Optional[str]:
        """
        Handle the special properties for primary models.

        Args:
            model_def: the botocraft model definition for this model
            base_class: the base class for this model

        Returns:
            The properties for this model, or ``None`` if this is not a primary
            model.
        """
        properties: str = ''
        if base_class in ['PrimaryBoto3Model', 'ReadonlyPrimaryBoto3Model']:
            assert model_def.primary_key or 'pk' in model_def.properties, \
                f'Primary service model "{model_def.name}" has no primary key defined'

            if 'pk' not in model_def.properties and model_def.primary_key:
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
        for property_name in model_def.properties:
            if not properties:
                properties = ''
            properties += ModelPropertyGenerator(self, model_def.name, property_name).code

        return properties

    def field_type(
        self,
        model_name: str,
        field_name: str,
        model_shape: Optional[botocore.model.Shape] = None,
        field_shape: Optional[botocore.model.Shape] = None
    ) -> str:
        """
        Return the python type annotation for a field.

        Args:
            model_name: The name of the model to get the field from.
            field_name: The name of the field.

        Keyword Args:
            model_shape: The shape of the model.  If not provided, we will look
                it up in the service model.
            field_shape: The shape of the field.  If not provided, we will look
                it up in the model shape.

        Returns:
            The python type annotation for the field.
        """
        if not model_shape:
            model_shape = self.get_shape(model_name)
        if not hasattr(model_shape, 'members'):
            raise ValueError(f'Model {model_name} has no fields.')
        if not field_shape:
            field_shape = cast(botocore.model.StructureShape, model_shape).members.get(field_name)
        if not field_shape:
            raise ValueError(f'Model {model_name} has no field {field_name}.')
        model_def = self.get_model_def(model_name)
        field_def = model_def.fields.get(field_name, ModelAttributeDefinition())
        python_type = field_def.python_type
        if not python_type:
            python_type = self.shape_converter.convert(field_shape)
        if python_type is None:
            raise ValueError(f'Could not determine type for field {field_name}.')
        return python_type

    def generate_model(
        self,
        model_name: str,
        shape: Optional[botocore.model.Shape] = None
    ) -> str:
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

        if model_name == 'CloudwatchLogsExportConfiguration':
            pass
        model_def = self.get_model_def(model_name)
        base_class = cast(str, model_def.base_class)
        if not shape:
            shape = self.get_shape(model_name)
        if model_def.alternate_name:
            model_name = model_def.alternate_name

        if hasattr(shape, 'members'):
            for field_name, field_shape in shape.members.items():
                #: The botocraft definition for this field
                field_def = model_def.fields.get(field_name, ModelAttributeDefinition())
                # Whether this field is required
                required: bool = (field_name in shape.required_members) or field_def.required
                # Our guess as to the python type for this field
                python_type = self.field_type(model_name, field_name, model_shape=shape, field_shape=field_shape)
                default = None
                if not required:
                    if not field_def.readonly:
                        python_type = f'Optional[{python_type}]'
                    if field_def.default is None:
                        default = 'None'
                    else:
                        default = field_def.default
                # Add the docstring for this field
                fields.append(
                    self.docformatter.format_attribute(field_shape.documentation)
                )
                field_line = f'    {field_name}: {python_type}'
                if field_def.readonly:
                    _default = f', default={default}' if default else ''
                    field_line += f' = Field(frozen=True{_default})'
                elif default:
                    field_line += f' = {field_def.default}'
                fields.append(field_line)
            fields.extend(self.extra_fields(model_def))

            properties = self.get_properties(model_def, base_class)
            if model_def.mixins:
                for mixin in model_def.mixins:
                    self.imports.add(f'from {mixin.import_path} import {mixin.name}')
                base_class = ', '.join([mixin.name for mixin in model_def.mixins] + [base_class])

            code: str = f'class {model_name}({base_class}):\n'
            docstring = self.docformatter.format_docstring(shape)
            if docstring:
                code += f'    """{docstring}"""\n'
            if 'PrimaryBoto3Model' in base_class:
                code += f'    objects: ClassVar[Boto3ModelManager] = {model_name}Manager()\n\n'
            if fields:
                code += '\n'.join(fields)
            if properties:
                code += f'\n{properties}'
            if not fields and not properties:
                code += '    pass'
            self.classes[model_name] = code
        return model_name


class ManagerGenerator(AbstractGenerator):

    #: A mapping of botocore operation names to the method generator class that
    #: will generate the code for that method.
    METHOD_GENERATORS: Dict[str, Type[ManagerMethodGenerator]] = {
        'create': CreateMethodGenerator,
        'update': UpdateMethodGenerator,
        'partial_update': PartialUpdateMethodGenerator,
        'delete': DeleteMethodGenerator,
        'get': GetMethodGenerator,
        'get_many': GetManyMethodGenerator,
        'list': ListMethodGenerator,
    }

    def __init__(self, service_generator: "ServiceGenerator") -> None:
        super().__init__(service_generator)
        self.model_generator = self.service_generator.model_generator
        self.shape_converter = self.model_generator.shape_converter
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
        for method_name, method_def in manager_def.methods.items():
            try:
                method_generator_class = self.METHOD_GENERATORS[method_name]
            except KeyError:
                generator: ManagerMethodGenerator = GeneralMethodGenerator(
                    self,
                    model_name,
                    method_def,
                    method_name=method_name
                )
            else:
                generator = method_generator_class(
                    self,
                    model_name,
                    method_def
                )
            methods[method_name] = generator.code
        method_code = '\n\n'.join(methods.values())
        base_class = 'Boto3ModelManager'
        if manager_def.mixins:
            for mixin in manager_def.mixins:
                self.imports.add(f'from {mixin.import_path} import {mixin.name}')
            base_class = ', '.join([mixin.name for mixin in manager_def.mixins] + [base_class])
        if manager_def.readonly:
            base_class = 'ReadonlyBoto3ModelManager'
        code = f"""


class {model_name}Manager({base_class}):

    service_name: str = '{self.service_name}'

{method_code}
"""
        self.classes[f'{model_name}Manager'] = code

    def generate(self) -> None:
        for model_name, manager_def in self.service_def.managers.items():
            self.generate_manager(model_name, manager_def)
        self.imports.update(self.model_generator.imports)


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
                'from typing import ClassVar, Optional, Literal, Dict, List, Any, cast',
                'from pydantic import Field',
                'from .abstract import Boto3Model, ReadonlyBoto3Model, PrimaryBoto3Model, '
                'ReadonlyPrimaryBoto3Model, Boto3ModelManager, ReadonlyBoto3ModelManager',
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
        model_classes = '\n\n'.join(self.model_classes.values())
        response_classes = '\n\n'.join(self.response_classes.values())
        manager_classes = '\n\n'.join(self.manager_classes.values())
        return f"""
# This file is automatically generated by botocraft.  Do not edit directly.
# pylint: disable=anomalous-backslash-in-string,unsubscriptable-object,line-too-long,arguments-differ,arguments-renamed
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

        # Generate the service managers and request/response models
        self.manager_generator.generate()
        self.response_classes = deepcopy(self.model_generator.classes)
        self.manager_classes = deepcopy(self.manager_generator.classes)
        self.imports.update(self.manager_generator.imports)
        self.model_generator.clear()

        self.write()

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
        and with docformatter.

        Args:
            code: the code to write to the output file.
        """
        code = self.code
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
        except (KeyError, black.parsing.InvalidInput):  # pylint: disable=c-extension-no-member
            print(code)
            raise
        formatted_code = isort.code(formatted_code)
        formatted_code = Formatter(FormatterArgs(), None, None, None)._format_code(formatted_code)
        output_file = self.service_path / f'{self.service_def.name}.py'
        with open(output_file, 'w', encoding='utf-8') as fd:
            fd.write(formatted_code)
