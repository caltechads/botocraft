from collections import OrderedDict
from typing import (
    Optional,
    Literal,
    TYPE_CHECKING,
)

import botocore.session
import inflect


from botocraft.sync.models import OperationDefinition

if TYPE_CHECKING:
    from botocraft.sync.service import ManagerGenerator


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

    def resolve_type(self, shape: botocore.model.Shape) -> str:
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
            elif shape.type_name == 'map':
                # This is a map of submodels.  I'm assuming here that the key
                # and value types are simple types like String or Integer.
                value_type = self.shape_converter.convert(shape.key)  # type: ignore  # pylint: disable=no-member
                key_type = self.shape_converter.convert(shape.value)  # type: ignore  # pylint: disable=no-member
                python_type = f'Dict[{key_type}, {value_type}]'
            elif shape.type_name == 'structure':
                # This is a submodel
                inner_model_name = shape.name
                import_model = inner_model_name
                python_type = inner_model_name
        if import_model:
            if import_model in self.generator.service_generator.classes:
                # We generated this model in this service so we don't need to
                # import it
                pass
            elif import_model in self.generator.interface.models:
                # We generated this model in another service, so we need to
                # import it
                import_path = self.generator.interface.models[import_model]
                self.imports.add(f"from {import_path} import {import_model}")
            else:
                # What the heck is this?
                self.model_generator.generate_model(
                    import_model,
                    shape=shape
                )
        return python_type

    def is_required(self, arg: str) -> bool:
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
            arg in self.input_shape.required_members or
            (arg in mapping and mapping[arg].required)
        )

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
        if self.input_shape is None:
            return args
        mapping = self.operation_def.args
        for arg, arg_type in self.input_shape.members.items():
            if arg in mapping and mapping[arg].hidden:
                # This is a hidden argument, so we don't want to expose it
                # in the method signature
                continue
            python_type = self.resolve_type(arg_type)
            if kind == 'args':
                if self.is_required(arg):
                    args[arg] = python_type
            else:
                if not self.is_required(arg):
                    default: Optional[str] = 'None'
                    if arg in mapping:
                        default = mapping[arg].default
                    args[arg] = f'Optional[{python_type}] = {default}'
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
        for arg in self.operation_def.explicit_args:
            if arg in self.input_shape.required_members:
                args[arg] = self.resolve_type(self.input_shape.members[arg])
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
        for arg in self.operation_def.explicit_kwargs:
            if arg not in self.input_shape.required_members:
                args[arg] = f'Optional[{self.resolve_type(self.input_shape.members[arg])}]'
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
        call = f"self.client.{self.boto3_name}("
        call += ", ".join([f"{arg}={arg}" for arg in self.args])
        if self.args and self.kwargs:
            call += ", "
        call += ", ".join([f"{arg}={arg}" for arg in self.kwargs])
        call += ")"
        if self.return_type == 'None':
            return call
        call = "_response = " + call
        call += f"\n        response = {self.response_class}.model_construct(**_response)"
        return call

    @property
    def response_class(self) -> str:
        """
        Create the response class, add it to the list of response classes,
        and return the type string

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
        return self.response_class

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
