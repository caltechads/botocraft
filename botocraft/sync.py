from dataclasses import dataclass, field
from pathlib import Path
import re
from textwrap import wrap
from typing import Optional, List, Dict, Tuple, Literal, Set

import boto3
import botocore.session
import black
import black.parsing
from markdownify import markdownify
from docformatter.format import Formatter


@dataclass
class FormatterArgs:

    line_range: Optional[Tuple[int, int]] = None
    length_range: Optional[Tuple[int, int]] = None
    black: bool = True
    style: Literal['sphinx', 'epytext'] = 'sphinx'
    force_wrap: bool = False
    make_summary_multi_line: bool = True
    pre_summary_newline: bool = True
    post_summary_newline: bool = True
    post_description_blank: bool = False
    non_strict: bool = False
    rest_section_adorns: str = r'''[!\"#$%&'()*+,-./\\:;<=>?@[]^_`{|}~]{4,}'''
    tab_width: int = 4
    wrap_summaries: int = 79
    wrap_descriptions: int = 79
    non_cap: List[str] = field(default_factory=list)


class DocumentationFormatter:

    MARKDOWN_LINK_RE = re.compile(
        r"(?:\[(?P<text>.*?)\])\((?P<link>.*?)\)",
        re.MULTILINE | re.DOTALL
    )

    def __init__(self, max_length: int = 79):
        #: Wrap lines at this length.
        self.max_length = max_length

    def _clean_uls(self, documentation: str) -> str:
        """
        Look through ``documentation`` for unordered lists and clean them up.

        This means wrapping them properly at 79 characters, and adding a blank
        line before and after.

        Args:
            documentation: the partially processed reStructuredText
                documentation

        Returns:
            The documentation with unordered lists cleaned up.
        """
        lines = []
        source_lines = documentation.split('\n')
        for i, line in enumerate(source_lines):
            if line.startswith('*'):
                previous_line = source_lines[i - 1]
                if previous_line.strip() != '' and not previous_line.startswith('*'):
                    lines.append('')
                if len(line) > self.max_length:
                    wrapped = wrap(line, self.max_length)
                    lines.append(wrapped[0])
                    lines.extend([f'  {line}' for line in wrapped[1:]])
                else:
                    lines.append(line)
            else:
                if len(line) > self.max_length:
                    lines.extend(wrap(line, self.max_length))
                else:
                    lines.append(line)
        return '\n'.join(lines)

    def _clean_links(self, documentation: str) -> str:
        """
        Transform our Markdown links to reStructuredText links.

        Args:
            documentation: the partially processed reStructuredText
                documentation

        Returns:
            The documentation with links cleaned up.
        """
        for match in self.MARKDOWN_LINK_RE.finditer(documentation):
            text = match.group('text')
            link = match.group('link')
            link = link.replace(' ', '')
            documentation = documentation.replace(match.group(0), f'`{text} <{link}>`_')
        return documentation

    def clean(self, documentation: str, max_lines: Optional[int] = None) -> str:
        """
        Take the input documentation in HTML format and clean it up for use in a
        docstring, as reStructuredText.

        Args:
            documentation: the HTML documentation to clean up

        Returns:
            Properly formatted reStructuredText documentation.
        """
        documentation = markdownify(documentation)
        if max_lines is not None:
            documentation = '\n'.join(documentation.split('\n')[:max_lines])
        if '\n' in documentation:
            documentation = '\n'.join([line.strip() for line in documentation.split('\n')])
        documentation = documentation.replace('`', '``')
        documentation = self._clean_uls(documentation)
        documentation = self._clean_links(documentation)
        return documentation

    def format_docstring(self, shape: botocore.model.Shape) -> str:
        """
        Format the documentation for a model.

        Args:
            shape: the botocore shape for the model

        Returns:
            The formatted documentation for the model as reStructuredText.
        """
        documentation = shape.documentation
        documentation = self.clean(documentation)
        return documentation

    def format_attribute(self, shape: botocore.model.Shape) -> str:
        """
        Format the documentation for a single attribute of a model.

        Args:
            shape: the botocore shape for the attribute

        Returns:
            The formatted documentation for the attribute as reStructuredText.
        """
        documentation = shape.documentation
        documentation = self.clean(documentation, max_lines=1)
        lines = wrap(documentation, self.max_length)
        return '\n'.join([f'    #: {line.strip()}' for line in lines])


class PydanticModelGenerator:

    models: List[str] = []
    subfolder: str = 'models'

    def __init__(
        self,
        service_name: str,
        models: List[str],
    ):
        session = botocore.session.get_session()
        #: The botocore service model for our service.
        self.service_model = session.get_service_model(service_name)
        if not models:
            models = self.__class__.models
        #: The list of models to generate.
        self.models = models
        #: The path to which to write the generated code.
        self.output = Path(__file__).parent / self.subfolder / f'{service_name}.py'
        self.code = """# This file was autogenerated by botocraft.  Do not edit directly.
from typing import Optional, List, Literal

from pydantic import BaseModel


"""
        #: We keep track of the classes we've generated so we can add them to
        #: the code in the right order.
        self.classes: Dict[str, str] = {}
        #: The formatter we use to clean up the documentation.
        self.formatter = DocumentationFormatter()

    def get_shape(self, name: str) -> botocore.model.Shape:
        """
        Get a :py:class:`botocore.model.Shape` by name from the service model,
        :py:attr:`service_model`.

        Args:
            name: The name of the shape to retrieve.

        Returns:
            The shape object.
        """
        return self.service_model._shape_resolver.get_shape_by_name(name)  # type: ignore  # pylint: disable=protected-access

    def generate(self) -> None:
        """
        Generate the code for the models and write it to the output file.
        """
        for model_name in self.models:
            self.generate_model(model_name, self.get_shape(model_name))
        code = self.code + '\n\n'.join(self.classes.values())
        self.write(code)

    def _handle_StringShape(self, shape: botocore.model.StringShape) -> str:
        if shape.enum:
            contents = ', '.join([f"'{value}'" for value in shape.enum])
            python_type = f'Literal[{contents}]'
        else:
            python_type = 'str'
        return python_type

    def generate_model(
        self,
        model_name: str,
        shape: botocore.model.Shape
    ) -> None:
        """
        Generate the code for a single model and save it to :py:attr:`classes`.

        Args:
            model_name: The name of the model to generate. This will be the
                name of the class.
            shape: The shape object for the model from the botocore service
                model.
        """
        if model_name in self.classes:
            print(f'Skipping model for {model_name}; already generated')
            return
        else:
            print(f'Generating model for {model_name}')
        fields: List[str] = []
        code: str = ''

        if hasattr(shape, 'members'):
            for name, field_shape in shape.members.items():
                # Our guess as to the python type for this field
                python_type: Optional[str] = None
                # Whether this field is required
                required: bool = name in shape.required_members
                # The default value for this field, if any
                default: Optional[str] = None

                if field_shape.type_name == 'string':
                    python_type = self._handle_StringShape(field_shape)
                elif field_shape.type_name == 'boolean':
                    python_type = 'bool'
                elif field_shape.type_name == 'integer':
                    python_type = 'int'
                elif field_shape.type_name == 'double':
                    python_type = 'float'
                elif field_shape.type_name == 'list':
                    # This is a list of submodels
                    element_shape = field_shape.member
                    inner_model_name: str = element_shape.name
                    if inner_model_name == 'String':
                        inner_model_name = 'str'
                    elif element_shape.type_name == 'string':
                        inner_model_name = self._handle_StringShape(element_shape)
                    else:
                        self.generate_model(inner_model_name, element_shape)
                    python_type = f'List[{inner_model_name}]'
                elif field_shape.type_name == 'structure':
                    # This is a submodel
                    inner_model_name = field_shape.name
                    self.generate_model(inner_model_name, field_shape)
                    python_type = inner_model_name

                if python_type:
                    if not required:
                        python_type = f'Optional[{python_type}]'
                        default = 'None'
                    fields.append(self.formatter.format_attribute(field_shape))
                    field_line = f'    {name}: {python_type}'
                    if default:
                        field_line += f' = {default}'
                    fields.append(field_line)

            code = f'class {model_name}(BaseModel):\n'
            code += f'    """{self.formatter.format_docstring(shape)}"""\n'
            code += '\n'.join(fields)
            self.classes[model_name] = code

    def write(self, code: str) -> None:
        """
        Write the generated code to the output file, and format it with black,
        and with docformatter.

        Args:
            code: the code to write to the output file.
        """
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
        except black.parsing.InvalidInput:
            print(code)
            raise
        formatted_code = Formatter(FormatterArgs(), None, None, None)._format_code(formatted_code)
        with open(self.output, 'w', encoding='utf-8') as output_file:
            output_file.write(formatted_code)


@dataclass
class CRUDLMapping:
    """
    A mapping of the CRUDL operations to the names of the
    boto3 operations that implement them.

    .. note::
        If this is a read-onl service, you can omit the ``create``,
        ``update``, and ``delete`` fields.
    """
    create: Optional[str] = None
    get: Optional[str] = None
    update: Optional[str] = None
    delete: Optional[str] = None
    list: Optional[str] = None


class PydanticManagerGenerator:

    subfolder = 'managers'

    def __init__(
        self,
        service_name: str,
        model_name: str,
        mapping: CRUDLMapping,
    ):
        self.client = boto3.client(service_name)
        self.mapping = mapping
        self.service_name = service_name
        self.model_name = model_name
        self.service_model = self.client.meta.service_model
        self.output = Path(__file__).parent / self.subfolder / f'{service_name}.py'
        self.methods: Dict[str, str] = {}
        self.model_imports: Set[str] = set()
        self.model_generator: PydanticModelGenerator = PydanticModelGenerator(
            service_name, []
        )

    def _handle_StringShape(self, shape: botocore.model.StringShape) -> str:
        if shape.enum:
            contents = ', '.join([f"'{value}'" for value in shape.enum])
            python_type = f'Literal[{contents}]'
        else:
            python_type = 'str'
        return python_type

    def translate_type(self, shape: botocore.model.Shape) -> Tuple[str, Optional[str]]:
        python_type: str
        import_model: Optional[str] = None
        if shape.type_name == 'string':
            python_type = self._handle_StringShape(shape)
        elif shape.type_name == 'boolean':
            python_type = 'bool'
        elif shape.type_name == 'integer':
            python_type = 'int'
        elif shape.type_name == 'list':
            # This is a list of submodels
            element_shape = shape.member
            inner_model_name: str = element_shape.name
            if element_shape.type_name == 'string':
                inner_model_name = self._handle_StringShape(element_shape)
            elif inner_model_name == 'String':
                inner_model_name = 'str'
            else:
                import_model = inner_model_name
            python_type = f'List[{inner_model_name}]'
        elif shape.type_name == 'structure':
            # This is a submodel
            inner_model_name = shape.name
            import_model = inner_model_name
            python_type = inner_model_name
        return python_type, import_model

    def extract_args(self, operation: str) -> Tuple[List[str], List[str]]:
        """
        Return the named arguments and positional arguments for the given
        operation.

        Args:
            operation: the boto3 operation to inspect.

        Returns:
            _type_: _description_
        """
        botocore_name = self.client._PY_TO_OP_NAME[operation]
        operation_model = self.service_model.operation_model(botocore_name)
        args: List[str] = []
        kwargs: List[str] = []
        for arg, arg_type in operation_model.input_shape.members.items():
            python_type, import_model = self.translate_type(arg_type)
            if import_model:
                self.model_imports.add(import_model)
            if arg in operation_model.input_shape.required_members:
                args.append(f'{arg}: {python_type}')
            else:
                kwargs.append(f'{arg}: Optional[{python_type}] = None')
        return args, kwargs

    def generate_method(self, operation: str, operation_name: str) -> None:
        """
        Generate the code for the manager for the given operation and write it
        to the output file.

        Args:
            operation: the boto3 operation to generate the method for.
            operation_name: the name of the operation to generate the method
                for.
        """
        if operation in ['create', 'update']:
            signature = f'self, model: {self.model_name}'
            self.model_imports.add(self.model_name)
        else:
            args, kwargs = self.extract_args(operation_name)
            signature = ',\n        '.join(['self'] + args + kwargs)
        code = f"""
    def {operation}(
        {signature}
    ) -> None:
"""
        if operation in ['create', 'update']:
            code += f"""
        self.client.{operation_name}(**model.dict(exclude_unset=True))
"""
        elif operation == 'get':
            if operation_name.startswith('describe_'):
                code += f"""

"""
        self.methods[operation] = code

    def generate(self) -> None:
        for operation, operation_name in self.mapping.__dict__.items():
            if operation_name:
                self.generate_method(operation, operation_name)
        model_imports = ',\n    '.join(self.model_imports)
        code = f"""
from typing import List, Literal, Optional

import boto3
from botocraft.models import (
    {model_imports}
)

class {self.model_name}Manager:

    service_name = '{self.service_name}'

    def __init__(self) -> None:
        self.client = boto3.client(self.service_name)

{"".join(self.methods.values())}
"""
        self.write(code)

    def write(self, code: str) -> None:
        """
        Write the generated code to the output file, and format it with black,
        and with docformatter.

        Args:
            code: the code to write to the output file.
        """
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
        except black.parsing.InvalidInput:
            print(code)
            raise
        formatted_code = Formatter(FormatterArgs(), None, None, None)._format_code(formatted_code)
        with open(self.output, 'w', encoding='utf-8') as output_file:
            output_file.write(formatted_code)
