from collections import OrderedDict
from typing import (
    Optional,
    Literal,
    cast,
    TYPE_CHECKING,
)

import botocore.session
import inflect

from botocraft.sync.models import OperationDefinition, OperationArgumentDefinition
from botocraft.sync.methods.models import MethodDocstringDefinition

if TYPE_CHECKING:
    from botocraft.sync.service import ManagerGenerator


class ManagerMethodGenerator:
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
    operation: str

    def __init__(
        self,
        generator: "ManagerGenerator",
        model_name: str,
        operation_def: OperationDefinition
    ):
        self.inflect = inflect.engine()
        #: The generator that is creating the entire manager file.  It
        #: has the information about the service and the models, and
        #: is where we're collecting all our code and imports.
        self.generator = generator
        #: The boto3 client for the service we're generating.
        self.client = generator.client  # type: ignore
        #: Our own botocraft config for this model.
        self.operation_def = operation_def
        #: The botocore service model for the service we're generating.
        self.service_model = generator.service_model  # type: ignore
        #: The boto3 operation name for the operation we're generating.  This is
        #: something like ``describe_instances``.
        self.boto3_name = self.operation_def.boto3_name
        #: The AWS API method for the operation we're generating.  This is
        #: something like ``DescribeInstances``.
        botocore_name = self.client._PY_TO_OP_NAME[self.boto3_name]
        #: The botocore operation model for the operation we're generating.
        self.operation_model = self.service_model.operation_model(botocore_name)
        #: The input shape for the operation we're generating.
        self.input_shape = self.operation_model.input_shape
        #: The output shape for the operation we're generating.
        self.output_shape = self.operation_model.output_shape
        #: Our model generator, which we use to generate any response models we
        #: need.
        self.model_generator = generator.model_generator
        #: The converter we use to convert botocore shapes to python types.
        self.shape_converter = generator.shape_converter
        #: Any botocraft imports we need to add to the manager.
        self.imports = generator.imports
        #: The name of the model itself
        self.model_name = model_name
        #: The plural of the name of the model itself
        self.model_name_plural = self.inflect.plural(self.model_name)
        #: Our documentation formatter
        self.docformatter = generator.docformatter

    def get_explicit_args_from_request(self) -> OrderedDict[str, OperationArgumentDefinition]:
        """
        Compare the botocore input shape for the operation with the
        :py:class:`ModelAttributeDefinition` dict for the model we're working
        with, and return a dictionary of the arguments that are not part of the
        model.

        Returns:
            A dictionary of argument names to argument definitions.
        """
        model_fields = self.model_generator.fields(self.model_name)
        args: OrderedDict[str, OperationArgumentDefinition] = OrderedDict()
        if self.input_shape is not None:
            for arg in self.input_shape.members:
                if arg in self.operation_def.args:
                    # We're explicitly defining this argument in our botocraft
                    # config, so we don't need to do anything here.
                    continue
                if arg not in model_fields:
                    args[arg] = OperationArgumentDefinition(explicit=True)
                    if arg in self.input_shape.required_members:
                        args[arg].required = True
        return args

    def is_required(self, arg_name: str) -> bool:
        """
        Determine if the given argument is required for the method signature.

        Args:
            arg: the name of the argument

        Returns:
            If this argument is required for the method signature,
            return ``True``, otherwise return ``False``.
        """
        if self.input_shape is None:
            return False
        mapping = self.operation_def.args
        return (
            arg_name in self.input_shape.required_members or
            (arg_name in mapping and mapping[arg_name].required)
        )

    def serialize(self, arg: str) -> str:
        """
        Wrap the boto3 operation argument assignment with `self.serialize()`
        if necessary.

        Args:
            arg: the name of the method argument

        Returns:
            A string that is either the argument name, or the argument name
            wrapped in a call to ``self.serialize()``.
        """
        mapping = self.operation_def.args
        arg_def = mapping.get(arg, OperationArgumentDefinition())
        if arg_def.exclude_none:
            return f'self.serialize({arg}, exclude_none=True)'
        return f'self.serialize({arg})'

    def _args(self, kind: Literal['args', 'kwargs']) -> OrderedDict[str, str]:
        """
        This is used to generate the arguments for the botocraft method
        signature.

        If kind == 'args', then we generate the positional arguments, but
        if kind == 'kwargs', then we generate the keyword arguments.

        Args:
            kind: what kind of method arguments to generate.

        Returns:
            An ordered dictionary of argument names to types.
        """
        args: OrderedDict[str, str] = OrderedDict()
        if self.input_shape is None:
            return args
        mapping = self.operation_def.args
        for arg_name, arg_shape in self.input_shape.members.items():
            if arg_name in mapping and mapping[arg_name].hidden:
                # This is a hidden argument, so we don't want to expose it
                # in the method signature
                continue
            python_type = self.shape_converter.convert(arg_shape, quote=True)
            if kind == 'args':
                if self.is_required(arg_name):
                    args[arg_name] = python_type
            else:
                if not self.is_required(arg_name):
                    default: Optional[str] = 'None'
                    if arg_name in mapping:
                        default = mapping[arg_name].default
                    if default == 'None':
                        args[arg_name] = f'Optional[{python_type}] = None'
                    else:
                        args[arg_name] = f'{python_type} = {default}'
        return args

    @property
    def explicit_args(self) -> OrderedDict[str, str]:
        """
        Return the positional arguments for the given operation.

        Returns:
            A dictionary of argument names to types.
        """
        args: OrderedDict[str, str] = OrderedDict()
        if not self.input_shape:
            return args
        for arg_name in self.operation_def.explicit_args:
            if arg_name in self.input_shape.required_members:
                args[arg_name] = self.shape_converter.convert(
                    self.input_shape.members[arg_name],
                    quote=True
                )
        return args

    @property
    def explicit_kwargs(self) -> OrderedDict[str, str]:
        """
        Return the positional arguments for the given operation.

        Returns:
            A dictionary of argument names to types.
        """
        args: OrderedDict[str, str] = OrderedDict()
        if not self.input_shape:
            return args
        for arg_name in self.operation_def.explicit_kwargs:
            if arg_name not in self.input_shape.required_members:
                args[arg_name] = self.shape_converter.convert(
                    self.input_shape.members[arg_name],
                    quote=True
                )
                arg_def = self.operation_def.args.get(arg_name, OperationArgumentDefinition())
                if arg_def.default in [None, "None"]:
                    args[arg_name] = f'Optional[{args[arg_name]}]'
        return args

    @property
    def args(self) -> OrderedDict[str, str]:
        """
        Return the keyword arguments for the given operation.  The
        positional arguments are the arguments are required.
        They will include a type.

        Example:

            ..code-block:: python

                {
                    'arg1': 'str'
                    'arg2': 'List[str]'
                }

        Returns:
            A dictionary of argument names to types.
        """
        return self._args('args')

    @property
    def kwargs(self) -> OrderedDict[str, str]:
        """
        Return the keyword arguments for the given operation.  These
        apply to both the method signature and to the boto3 operation call.

        keyword arguments are the arguments that are not required.
        They will include a type and a default value.

        Example:

            ..code-block:: python

                {
                    'arg1': 'str = "default"',
                    'arg2': 'Optional[str] = None'
                }

        Returns:
            A dictionary of argument names to types/defaults.
        """
        return self._args('kwargs')

    @property
    def operation_args(self) -> str:
        """
        Return the argument string for the boto3 call.  We use the
        output of :py:meth:`args` and :py:meth:`kwargs` to generate
        this string.

        Example:

            ``name=name, description=description``
        """
        arg_str = ", ".join([f"{arg}={self.serialize(arg)}" for arg in self.args])
        if self.args and self.kwargs:
            arg_str += ", "
        arg_str += ", ".join([f"{arg}={self.serialize(arg)}" for arg in self.kwargs])
        return arg_str

    @property
    def operation_call(self) -> str:
        """
        This is a body snippet that does the actual boto3 call.  and assigns the
        response to ``_response``.  It then uses response to instantiate
        :py:meth:`response_class`.

        Example:

            ..code-block:: python

                _response = self.client.create(name=name, description=description)
                response = ResponseModel.model_construct(**_response)

        Returns:
            The code for the boto3 call.
        """
        call = f"self.client.{self.boto3_name}({self.operation_args})"
        if self.return_type == 'None':
            return call
        call = "_response = " + call
        call += f"\n        response = {self.response_class}.model_construct(**_response)"
        return call

    @property
    def response_class(self) -> str:
        """
        Create the response class, add it to the list of response classes, and
        return the type string.  The response class is the class that we use to
        deserialize the boto3 response into a pydantic model.

        If there is no output shape defined in botocore for the operation, then
        we return ``None``.

        Returns:
            The name of the response class.
        """
        if self.output_shape is None:
            return 'None'
        model_name = self.output_shape.name
        self.model_generator.generate_model(
            model_name,
            shape=self.operation_model.output_shape
        )
        return model_name

    @property
    def response_attr(self) -> Optional[str]:
        """
        Deduce the name of the attribute in the boto3 response that we want to
        return from the method.  This is either some variation of the name of
        the model itself, or whatever the botocraft config for the operation
        specifies.

        Returns:
            _type_: _description_
        """
        if self.output_shape is None:
            return None
        if not hasattr(self.output_shape, 'members'):
            return None
        if self.operation_def.response_attr:
            return self.operation_def.response_attr
        potential_names = [
            self.model_name.lower(),
            self.model_name_plural.lower(),
        ]
        response_attrs = {attr.lower(): attr for attr in self.output_shape.members}
        for attr in response_attrs:
            if attr in potential_names:
                return response_attrs[attr]
        attrs = ", ".join([f'"{attr}"' for attr in response_attrs])
        if not attrs:
            attrs = "No attributes"
        raise ValueError(
            f"Can't deduce response attribute for response class {self.output_shape.name}: {attrs}"
        )

    @property
    def response_attr_multiplicity(self) -> Literal['one', 'many']:
        """
        Determine if the response attribute is a list or not.

        Returns:
            ``'one'`` if the response attribute is not a list, ``'many'`` if it
            is a list.
        """
        if self.output_shape is None:
            return 'one'
        if not hasattr(self.output_shape, 'members'):
            return 'one'
        if self.response_attr is None:
            return 'one'
        shape = self.output_shape.members[self.response_attr]
        if hasattr(shape, 'type') and shape.type == 'list':
            return 'many'
        elif hasattr(shape, 'type_name') and shape.type_name == 'list':
            return 'many'
        return 'one'

    @property
    def return_type(self) -> str:
        """
        Set the type hint for the return type of the method.  This is either the
        response class, or whatever class the botocraft config for the operation
        specifies.

        Returns:
            The type hint for the return type of the method.
        """
        if self.operation_def.return_type:
            return self.operation_def.return_type
        # If our output shape has no members, then we return None
        output_shape = cast(botocore.model.StructureShape, self.output_shape)
        if (
            not hasattr(output_shape, 'members') or
            hasattr(output_shape, 'members') and not output_shape.members
        ):
            return 'None'
        return self.response_class

    @property
    def signature(self) -> str:
        """
        Create the method signature for the operation.

        Example:

            .. code-block:: python

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

    def get_arg_docstring(self, arg: str) -> Optional[str]:
        """
        Return the docstring for the given argument.

        Args:
            arg: the name of the argument

        Returns:
            The docstring for the argument.
        """
        if arg in self.operation_def.args:
            arg_def = self.operation_def.args[arg]
            if arg_def.docstring:
                return arg_def.docstring
        if self.input_shape is not None:
            if arg in self.input_shape.members:
                return self.input_shape.members[arg].documentation
        return None

    @property
    def docstrings_def(self) -> MethodDocstringDefinition:
        """
        Build the docstring definition for the method.

        Returns:
            A :py:class:`MethodDocstringDefinition` instance.
        """
        docstrings: MethodDocstringDefinition = MethodDocstringDefinition()
        docstrings.method = (
            self.operation_def.docstring
            if self.operation_def.docstring
            else self.operation_model.documentation
        )
        for arg in self.args:
            docstrings.args[arg] = self.get_arg_docstring(arg)
        for arg in self.kwargs:
            docstrings.kwargs[arg] = self.get_arg_docstring(arg)
        return docstrings

    @property
    def docstring(self) -> Optional[str]:
        """
        Return the docstring for the method.
        """
        return self.docstrings_def.render(self.docformatter)

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
        code = self.signature
        docstring = self.docstring
        if docstring:
            code += docstring
        code += self.body
        return code
