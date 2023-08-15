from collections import OrderedDict
import re
from typing import Optional, Dict, Tuple, Literal, Set, Any, Type

import boto3
import botocore.session
import inflect

from .abstract import AbstractGenerator
from .model import PydanticModelGenerator
from .shapes import PythonTypeShapeConverter

Operation = Literal['create', 'delete', 'get', 'list', 'update']


class MethodGenerator:
    """
    The base class for all method generators.  This is used to generate
    the code for a single method on a manager class.

    To use this, you subclass it and implement the :py:meth:`body`
    property, which is the body of the method.  You can also override
    any of the following properties to customize the method:

    * :py:meth:`signature`: The method signature.
    * :py:meth:`args`: The positional arguments with types for the method
    * :py:meth:`kwargs`: The keyword arguments with types for the method
    * :py:meth:`operation_call`: the code for the boto3 client call.
    * :py:meth:`return_type`: The return type annotation.
    * :py:meth:`response_class`: The response class to use for the
        boto3 client call.

    Args:
        generator: The generator that is creating the manager class for
            an object.  It has the information about the service and the models,
            and is where we're collecting all our code and imports.
    """

    #: The botocraft operation we're implementing
    operation: Operation

    def __init__(self, generator: "PydanticManagerGenerator"):
        self.inflect = inflect.engine()
        #: The generator that is creating the entire manager file.  It
        #: has the information about the service and the models, and
        #: is where we're collecting all our code and imports.
        self.generator = generator
        #: The boto3 client for the service we're generating.
        self.client = generator.client  # type: ignore
        #: Our own botocraft config for this model.
        self.model_config = generator.config
        #: The botocore service model for the service we're generating.
        self.service_model = generator.service_model  # type: ignore
        #: The boto3 operation name for the operation we're generating.  This is
        #: something like ``describe_instances``.
        self.operation_name = self.config['boto3_name']
        #: The AWS API method for the operation we're generating.  This is
        #: something like ``DescribeInstances``.
        botocore_name = self.client._PY_TO_OP_NAME[self.operation_name]
        #: The botocore operation model for the operation we're generating.
        self.operation_model = self.service_model.operation_model(botocore_name)
        #: Our model generator, which we use to generate any response models we
        #: need.
        self.model_generator = generator.model_generator
        #: The converter we use to convert botocore shapes to python types.
        self.shape_converter = generator.shape_converter
        #: Any botocraft imports we need to add to the manager.
        self.model_imports = generator.model_imports
        #: The name of the model itself
        self.model_name = generator.model_name
        #: The plural of the name of the model itself
        self.model_name_plural = self.inflect.plural(self.model_name)

    @property
    def config(self) -> Dict[str, Any]:
        """
        Return the botocraft configuration for the method we're generating.
        """
        return self.model_config['operations'][self.operation]

    def translate_type(self, shape: botocore.model.Shape) -> Tuple[str, Optional[str]]:
        """
        Translate the given botocore argument shape into a python type.

        Args:
            shape: the botocore shape for the argument we're translating.

        Returns:
            A tuple of the python type and the model we need to import for it,
            if that was created.
        """
        python_type: str
        import_model: Optional[str] = None
        try:
            python_type = self.shape_converter.convert(shape)
        except ValueError:
            if shape.type_name == 'list':
                # This is a list of submodels
                element_shape = shape.member  # type: ignore
                inner_model_name: str = element_shape.name
                if inner_model_name == 'String' or element_shape.type_name == 'string':
                    inner_model_name = self.shape_converter.convert(element_shape)
                else:
                    import_model = inner_model_name
                python_type = f'List[{inner_model_name}]'
            elif shape.type_name == 'structure':
                # This is a submodel
                inner_model_name = shape.name
                import_model = inner_model_name
                python_type = inner_model_name
        return python_type, import_model

    def _args(self, kind: Literal['args', 'kwargs']) -> OrderedDict[str, str]:
        """
        This is used to generate the arguments for the operation.

        If kind == 'args', then we generate the positional arguments, but
        if kind == 'kwargs', then we generate the keyword arguments.

        Args:
            kind: what kind of method arguments to generate.

        Returns:
            An ordered dictionary of argument names to types.
        """
        args: OrderedDict[str, str] = OrderedDict()
        for arg, arg_type in self.operation_model.input_shape.members.items():
            python_type, import_model = self.translate_type(arg_type)
            if import_model:
                self.model_imports.add(import_model)
            if kind == 'args':
                if arg in self.operation_model.input_shape.required_members:
                    args[arg] = python_type
            if kind == 'kwargs':
                if arg not in self.operation_model.input_shape.required_members:
                    args[arg] = f'{python_type} = None'
        return args

    @property
    def explicit_args(self) -> OrderedDict[str, str]:
        """
        Return the positional arguments for the given operation.

        Returns:
            A dictionary of argument names to types.
        """
        args = OrderedDict()
        for arg in self.config.get('explicit_args', []):
            if arg in self.operation_model.input_shape.required_members:
                python_type, import_model = self.translate_type(
                    self.operation_model.input_shape.members[arg]
                )
                if import_model:
                    self.model_imports.add(import_model)
                args[arg] = python_type
        return args

    @property
    def explicit_kwargs(self) -> OrderedDict[str, str]:
        """
        Return the positional arguments for the given operation.

        Returns:
            A dictionary of argument names to types.
        """
        args = OrderedDict()
        for arg in self.config.get('explicit_kwargs', []):
            if arg not in self.operation_model.input_shape.required_members:
                python_type, import_model = self.translate_type(
                    self.operation_model.input_shape.members[arg]
                )
                if import_model:
                    self.model_imports.add(import_model)
                args[arg] = python_type
        return args

    @property
    def args(self) -> OrderedDict[str, str]:
        """
        Return the positional arguments for the given operation.

        Returns:
            A dictionary of argument names to types.
        """
        return self._args('args')

    @property
    def kwargs(self) -> OrderedDict[str, str]:
        """
        Return the keyword arguments for the given operation.

        Returns:
            A dictionary of argument names to types.
        """
        return self._args('kwargs')

    @property
    def operation_call(self) -> str:
        """
        This is a body snippet that does the actual boto3 call.
        and assigns the response to ``_response``.

        It then uses response to instantiate :py:meth:`response_class`.

        Returns:
            The code for the boto3 call.
        """
        call = f"self.client.{self.operation_name}("
        call += ", ".join([f"{arg}={arg}" for arg in self.args])
        if self.args and self.kwargs:
            call += ", "
        call += ", ".join([f"{arg}={arg}" for arg in self.kwargs])
        call += ")"
        if self.return_type == 'None':
            return call
        call = "_response = " + call
        call += f"\n        response = {self.response_class}(**_response)"
        return call

    @property
    def response_class(self) -> str:
        """
        Create the response class, add it to the list of response classes,
        and return the type string

        Returns:
            The name of the response class.
        """
        model_name = self.operation_model.output_shape.name
        self.model_generator.generate_model(model_name, self.operation_model.output_shape)
        return model_name

    @property
    def return_type(self) -> str:
        """
        Set the type hint for the return type of the method.  This is either the
        response class, or whatever class the botocraft config for the operation
        specifies.

        Returns:
            The type hint for the return type of the method.
        """
        response_class = self.response_class
        return self.config.get('return_type', response_class)

    @property
    def signature(self) -> str:
        """
        Create the method signature for the operation.

        Example::

            def create(self, name: str, *, description: str) -> Model:

        Returns:
            The method signature for the operation.
        """
        args = ", ".join([f'{arg}: {arg_type}' for arg, arg_type in self.args.items()])
        kwargs = ", ".join([f'{arg}: {arg_type}' for arg, arg_type in self.kwargs.items()])
        signature = f"    def {self.operation}(self, "
        if args:
            signature += args
        if args and kwargs:
            signature += ", "
        if kwargs:
            signature += f"*, {kwargs}"
        signature += f") -> {self.return_type}:"
        return signature

    @property
    def body(self) -> str:
        """
        Return the body of the method.  It's implemented by the subclasses.

        Returns:
            The body of the method.
        """
        raise NotImplementedError

    @property
    def code(self) -> str:
        """
        Return the full code for the method.

        Returns:
            The full code for the method, ready to be inserted into the
            generated manager class.
        """
        return self.signature + self.body


class CreateMethodGenerator(MethodGenerator):
    """
    Handle the generation of a create method.
    """

    operation: Operation = 'create'

    def __init__(self, generator: "PydanticManagerGenerator"):
        super().__init__(generator)
        self.model_imports.add(self.model_name)

    @property
    def signature(self) -> str:
        """
        For create methods, we add the model as the only argument.

        Returns:
            The method signature for the operation.
        """
        defaults = self.config.get('defaults', {})
        signature = f"    def {self.operation}(self, model: {self.model_name}"
        if self.explicit_args or self.explicit_kwargs:
            signature += ", "
        signature += ", ".join([f"{arg}: {arg_type}" for arg, arg_type in self.explicit_args.items()])
        if self.explicit_args and self.explicit_kwargs:
            signature += ", "
        signature += ", ".join([
            f"{arg}: {arg_type} = {defaults.get(arg, 'None')}"
            for arg, arg_type in self.explicit_kwargs.items()
        ])
        signature += f") -> {self.return_type}:"
        return signature

    @property
    def operation_args(self) -> OrderedDict[str, str]:
        mapping = self.config.get('mapping', {})
        _args = OrderedDict()
        for arg in self.args:
            if arg in self.explicit_args.keys():
                _arg = arg
            else:
                _arg = f"data['{mapping.get(arg, arg)}']"
            _args[arg] = _arg
        return _args

    @property
    def operation_kwargs(self) -> OrderedDict[str, str]:
        mapping = self.config.get('mapping', {})
        _args = OrderedDict()
        for arg in self.kwargs:
            if arg in self.explicit_kwargs.keys():
                _arg = arg
            else:
                _arg = f"data['{mapping.get(arg, arg)}']"
            _args[arg] = _arg
        return _args

    @property
    def operation_call(self) -> str:
        """
        This is a body snippet that does the actual boto3 call.
        and assigns the response to ``_response``.

        This is different from the base class, because we need to do a few things:

        * We need to map model attributes to the boto3 call arguments.
        * In some cases the boto3 call arguments are different from the model
          attributes, so we need to override the mapping with something
        * Some boto3 call arguments are not actually model attributes, so we
          need to explicitly pass them in.

        It then uses response to instantiate :py:meth:`response_class`.

        Returns:
            The code for the boto3 call.
        """
        call = "data = model.model_dump()"
        call += f"\n        _response = self.client.{self.operation_name}("
        call += ", ".join([f"{arg}={_arg}" for arg, _arg in self.operation_args.items()])
        if self.args and self.kwargs:
            call += ", "
        call += ", ".join([f"{arg}={_arg}" for arg, _arg in self.operation_kwargs.items()])
        call += ")"
        call += f"\n        response = {self.response_class}(**_response)"
        return call

    @property
    def body(self) -> str:
        response_attr = self.config.get('response_attr', self.model_name.lower())
        code = f"""
        {self.operation_call}
        return cast({self.return_type}, response.{response_attr})
"""
        return code

    @property
    def return_type(self) -> str:
        """
        For create, update and delete methods, we return the model itself, not
        the response model, unless it's overriden in our botocraft operation
        config, in which case we return that.

        Returns:
            The name of the return type class.
        """
        # We're doing this weird line to make sure that the return type is
        # imported into the generated class, even if it's not used in the
        # method signature.
        _ = super().return_type
        return self.config.get('return_type', self.model_name)


class UpdateMethodGenerator(CreateMethodGenerator):

    operation: Operation = 'update'


class DeleteMethodGenerator(MethodGenerator):
    """
    Generate the code for the delete method.

    boto3 delete methods typically return the dict of the full object that was
    deleted, so we'll convert that to the model we're working with and return
    that instead.
    """

    operation: Operation = 'delete'

    @property
    def return_type(self) -> str:
        """
        For create, update and delete methods, we return the model itself, not
        the response model, unless it's overriden in our botocraft operation
        config, in which case we return that.

        Returns:
            The name of the return type class.
        """
        _ = self.response_class
        return self.config.get('return_type', self.model_name)

    @property
    def body(self) -> str:
        response_attr = self.config.get('response_attr', self.model_name.lower())
        code = f"""
        {self.operation_call}
"""
        if not self.return_type == 'None':
            code += f"        return cast({self.model_name}, response.{response_attr})"
        return code


class GetMethodGenerator(MethodGenerator):
    """
    Generate the code for the ``get`` method.

    There typically is no boto3 operation that gets a single object, so we'll
    have to find the boto3 operation that returns the all the data
    we need for our model and then filter it down to the single object we're
    looking for.

    This also means changing the method signature to prevent people from
    asking for multiple objects.
    """

    operation: Operation = 'get'

    @property
    def args(self) -> OrderedDict[str, str]:
        """
        Return the positional arguments for the given operation.

        This is the same as the parent class, except we change the name of the
        argument from the plural to the singular.

        Returns:
            A dictionary of argument names to types.
        """
        args = super().args
        new_args = OrderedDict()
        for arg, arg_type in args.items():
            if arg == self.model_name_plural.lower():
                arg = self.model_name.lower()
                arg_type = re.sub(r'List\[(.*)\]', r'\1', arg_type)
            new_args[arg] = arg_type
        return new_args

    @property
    def operation_call(self) -> str:
        name = self.model_name.lower()
        plural = self.model_name_plural.lower()
        return super().operation_call.replace(f'{name}={name}', f'{plural}=[{name}]')

    @property
    def return_type(self) -> str:
        """
        For get methods, we return the model itself, not the response model,
        unless it's overriden in our botocraft operation config, in which case
        we return that.

        Returns:
            The name of the return type class.
        """
        _ = super().return_type
        return self.config.get('return_type', f'Optional[{self.model_name}]')

    @property
    def body(self) -> str:
        """
        Generate the code for the get method.

        Returns:
            The code for the get method.
        """
        response_attr = self.config.get('response_attr', self.model_name_plural.lower())
        code = f"""
        {self.operation_call}
        if response.{response_attr}:
            return response.{response_attr}[0]  # type: ignore # pylint: disable=unsubscriptable-object
        return None
"""
        return code


class ListMethodGenerator(MethodGenerator):

    operation: Operation = 'list'

    @property
    def return_type(self) -> str:
        """
        For create, update and delete methods, we return the model itself, not
        the response model, unless it's overriden in our botocraft operation
        config, in which case we return that.

        Returns:
            The name of the return type class.
        """
        _ = self.response_class
        return self.config.get('return_type', f'List[{self.model_name}]')

    @property
    def body(self) -> str:
        response_attr = self.config.get(
            'response_attr',
            self.inflect.plural(self.model_name.lower())
        )
        code = f"""
        {self.operation_call}
        return response.{response_attr}
"""
        return code


class PydanticManagerGenerator:

    #: A mapping of botocore operation names to the method generator class that
    #: will generate the code for that method.
    METHOD_GENERATORS: Dict[str, Type[MethodGenerator]] = {
        'create': CreateMethodGenerator,
        'update': UpdateMethodGenerator,
        'delete': DeleteMethodGenerator,
        'get': GetMethodGenerator,
        'list': ListMethodGenerator,
    }

    def __init__(
        self,
        generator: "PydanticServiceGenerator",
        model_name: str
    ):
        self.generator = generator
        self.client = generator.client
        self.model_name: str = model_name
        self.service_name: str = generator.service_name
        self.service_model = generator.service_model
        self.model_imports: Set[str] = generator.model_imports
        self.model_generator: PydanticModelGenerator = generator.model_generator
        self.shape_converter: PythonTypeShapeConverter = generator.shape_converter
        #: A mapping of method names to the code for the method
        self.methods: Dict[str, str] = {}

    @property
    def config(self) -> Dict[str, Any]:
        return self.generator.config[self.model_name]

    @property
    def code(self) -> str:
        self.model_imports.add(self.model_name)
        for operation in self.config['operations']:
            method_generator = self.METHOD_GENERATORS[operation](self)
            self.methods[operation] = method_generator.code
        methods = '\n\n'.join(self.methods.values())
        code = f"""


class {self.model_name}Manager:

    service_name: str = '{self.service_name}'

    def __init__(self) -> None:
        #: The boto3 client for the AWS service
        self.client = boto3.client(self.service_name)  # type: ignore

{methods}
"""
        return code


class PydanticServiceGenerator(AbstractGenerator):
    """
    Generate an entire file of managers for a given service.

    Args:
        service_name: The name of the AWS service we're generating the managers
            for.
    """

    subfolder: str = 'managers'
    data_file: str = 'managers.yml'

    def __init__(self, service_name: str):
        super().__init__(service_name)
        self.client = boto3.client(service_name)  # type: ignore
        #: The botocore service model for the service we're generating the
        #: manager for.
        self.service_model = self.client.meta.service_model
        #: A set of imports that need to be added to the generated file.
        self.model_imports: Set[str] = set()
        #: A mapping of model names to the code for the model manager.
        self.managers: Dict[str, str] = {}
        # The model generator is used to generate the response models
        self.model_generator: PydanticModelGenerator = PydanticModelGenerator(service_name)
        # Ensure we don't regenerate the models we've already generated
        # during the main model generation step.
        for model_name in self.config:
            self.model_generator.classes[model_name] = ''
        self.model_generator.classes['Tag'] = ''
        self.shape_converter = PythonTypeShapeConverter()

    @property
    def code(self) -> str:
        for model_name in self.config:
            manager_generator = PydanticManagerGenerator(self, model_name)
            self.managers[model_name] = manager_generator.code
        model_imports = ',\n    '.join(self.model_imports)
        output_classes = '\n\n'.join(self.model_generator.classes.values())
        manager_classes = '\n\n'.join(self.managers.values())
        code = f"""
from typing import List, Literal, Optional, cast

import boto3
from botocraft.models import (
    Boto3Model,
    {model_imports}
)

{output_classes}

{manager_classes}
"""
        return code

    def generate(self) -> None:
        self.write(self.code)
