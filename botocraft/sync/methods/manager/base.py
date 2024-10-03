import re
from collections import OrderedDict
from typing import (
    TYPE_CHECKING,
    Final,
    List,
    Literal,
    Optional,
    cast,
)

import botocore.session
import inflect

from botocraft.sync.models import (
    ManagerMethodDefinition,
    MethodArgumentDefinition,
    MethodDocstringDefinition,
)

if TYPE_CHECKING:
    from botocraft.sync.service import (
        DocumentationFormatter,
        ManagerGenerator,
        ModelGenerator,
        PythonTypeShapeConverter,
    )


class ManagerMethodGenerator:
    """
    The base class for all manager method generators.  This is used to generate
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

    #: A list of arguments that various boto3 calls use for pagination.  We
    #: want to hide them automatically sometimes.
    PAGINATOR_ARGS: Final[List[str]] = [
        "nextToken",
        "maxResults",
        "MaxResults",
        "NextToken",
        "Marker",
        "MaxRecords",
        "PageSize",
    ]

    #: The botocraft method we're implementing
    method_name: str

    def __init__(
        self,
        generator: "ManagerGenerator",
        model_name: str,
        method_def: ManagerMethodDefinition,
        method_name: Optional[str] = None,
    ):
        if method_name is not None:
            self.method_name = method_name
        self.inflect = inflect.engine()
        #: The generator that is creating the entire manager file.  It
        #: has the information about the service and the models, and
        #: is where we're collecting all our code and imports.
        self.generator = generator
        #: The boto3 client for the service we're generating.
        self.client = generator.client  # type: ignore[has-type]
        #: Our own botocraft config for this model.
        self.method_def = method_def
        #: The botocore service model for the service we're generating.
        self.service_model = generator.service_model  # type: ignore[has-type]
        #: The boto3 operation name for the method we're generating.  This is
        #: something like ``describe_instances``.
        self.boto3_name = self.method_def.boto3_name
        #: The AWS API method for the operation we're generating.  This is
        #: something like ``DescribeInstances``.
        botocore_name = self.client._PY_TO_OP_NAME[self.boto3_name]  # noqa: SLF001
        #: The botocore operation model for the operation we're generating.
        self.operation_model = self.service_model.operation_model(botocore_name)
        #: The input shape for the boto3 operation
        self.input_shape = self.operation_model.input_shape
        #: The output shape for the boto3 operation
        self.output_shape = self.operation_model.output_shape
        #: Our model generator, which we use to generate any response models we
        #: need.
        self.model_generator = cast("ModelGenerator", generator.model_generator)  # type: ignore[has-type]
        #: The converter we use to convert botocore shapes to python types.
        self.shape_converter = cast(
            "PythonTypeShapeConverter",
            generator.shape_converter,  # type: ignore[has-type]
        )
        #: Any botocraft imports we need to add to the manager.
        self.imports = generator.imports
        #: The name of the model itself
        self.model_name = model_name
        #: The botocraft model definition for the model we're working with.
        self.model_def = self.model_generator.get_model_def(self.model_name)
        #: The plural of the name of the model itself
        self.model_name_plural = self.inflect.plural(self.model_name)
        if self.model_def.plural:
            self.model_name_plural = self.model_def.plural
        #: Our documentation formatter
        self.docformatter = cast("DocumentationFormatter", generator.docformatter)  # type: ignore[has-type]

    def get_explicit_args_from_request(
        self,
    ) -> OrderedDict[str, MethodArgumentDefinition]:
        """
        Compare the botocore input shape for the operation with the
        :py:class:`ModelAttributeDefinition` dict for the model we're working
        with, and return a dictionary of the arguments that are not part of the
        model.

        Returns:
            A dictionary of argument names to argument definitions.

        """
        model_fields = self.model_generator.fields(self.model_name)
        args: OrderedDict[str, MethodArgumentDefinition] = OrderedDict()
        if self.input_shape is not None:
            for arg in self.input_shape.members:
                if arg in self.method_def.args:
                    # We're explicitly defining this argument in our botocraft
                    # config, so we don't need to do anything here.
                    continue
                if arg not in model_fields:
                    args[arg] = MethodArgumentDefinition(explicit=True)
                    if arg in self.input_shape.required_members:
                        args[arg].required = True
        return args

    def is_required(
        self, arg_name: str, location: Literal["method", "operation"] = "method"
    ) -> bool:
        """
        Determine if the given argument is required for the method signature.

        Args:
            arg_name: the name of the argument

        Keyword Args:
            location: where these arguments will be used.  If ``'method'``, then
                we obey both the boto3 operation definition and the botocraft
                method definition.  If ``'operation'``, then we only obey the
                boto3 operation definition.

        Returns:
            If this argument is required, return ``True``, otherwise return
            ``False``.

        """
        if self.input_shape is None:
            return False
        mapping = self.method_def.args
        if location == "method":
            return arg_name in self.input_shape.required_members or (
                arg_name in mapping and mapping[arg_name].required
            )
        return arg_name in self.input_shape.required_members

    def serialize(self, arg: str) -> str:
        """
        Figure out how to serialize the given argument.

        Args:
            arg: the name of the method argument

        Returns:
            A string that is either the argument name, or the argument name
            wrapped in a call to ``self.serialize()``.

        """
        mapping = self.method_def.args
        arg_def = mapping.get(arg, MethodArgumentDefinition())
        _arg = arg
        if arg_def.value:
            return arg_def.value
        if arg_def.source_arg:
            _arg = arg_def.source_arg
        if not arg_def.raw_value:
            return f"self.serialize({_arg})"
        return _arg

    def _args(  # noqa: PLR0912
        self,
        kind: Literal["args", "kwargs"],
        location: Literal["method", "operation"] = "method",
    ) -> OrderedDict[str, str]:
        """
        Used to generate the arguments for the botocraft method signature.

        If kind == 'args', then we generate the positional arguments, but if
        kind == 'kwargs', then we generate the keyword arguments.

        Args:
            kind: what kind of method arguments to generate.

        Keyword Args:
            location: where these arguments will be used.  If ``'method'``, then
                we only generate the arguments that are required for the method
                signature.  If ``'operation'``, then we generate all the arguments
                that are required for the boto3 operation call.

        Returns:
            An ordered dictionary of argument names to types.

        """
        args: OrderedDict[str, str] = OrderedDict()
        if self.input_shape is None:
            return args
        mapping = self.method_def.args
        for arg_name, arg_shape in self.input_shape.members.items():
            arg_def = mapping.get(arg_name, MethodArgumentDefinition())
            _arg_name = arg_name
            if location == "method" and arg_def.rename:
                _arg_name = arg_def.rename
            if arg_def.attribute and location == "operation":
                # The attribute name is different from the argument name
                _arg_name = arg_def.attribute
            if arg_def.hidden:
                # This is a hidden argument, so we don't want to expose it
                # in the method signature or the boto3 call.
                continue
            if location == "method" and arg_def.value:
                # This argument has a specific value, so we don't want to
                # expose it in the method signature
                continue
            if arg_def.python_type:
                python_type = cast(str, arg_def.python_type)
            else:
                python_type = self.shape_converter.convert(arg_shape, quote=True)
            if kind == "args":
                if self.is_required(arg_name, location=location):
                    args[_arg_name] = python_type
            elif not self.is_required(arg_name, location=location):
                default: Optional[str] = arg_def.default if arg_def.default else "None"
                if default == "None":
                    args[_arg_name] = f"Optional[{python_type}] = None"
                else:
                    args[_arg_name] = f"{python_type} = {default}"
        return args

    @property
    def explicit_args(self) -> OrderedDict[str, str]:
        """
        Return the explicit positional arguments for the given method.   These
        are arguments that are not part of the model, but are required in the
        boto3 operation call.

        Returns:
            A dictionary of argument names to types.

        """
        args: OrderedDict[str, str] = OrderedDict()
        if not self.input_shape:
            return args
        for arg_name in self.method_def.explicit_args:
            if arg_name in self.input_shape.required_members:
                args[arg_name] = self.shape_converter.convert(
                    self.input_shape.members[arg_name], quote=True
                )
        return args

    @property
    def explicit_kwargs(self) -> OrderedDict[str, str]:
        """
        Return the explicit positional arguments for the given method.   These
        are arguments that are not part of the model, but can be supplied in the
        boto3 operation call.

        Returns:
            A dictionary of argument names to types.

        """
        args: OrderedDict[str, str] = OrderedDict()
        if not self.input_shape:
            return args
        for arg_name in self.method_def.explicit_kwargs:
            if arg_name not in self.input_shape.required_members:
                args[arg_name] = self.shape_converter.convert(
                    self.input_shape.members[arg_name], quote=True
                )
                arg_def = self.method_def.args.get(arg_name, MethodArgumentDefinition())
                if arg_def.default in [None, "None"]:
                    args[arg_name] = f"Optional[{args[arg_name]}]"
        return args

    def args(
        self, location: Literal["method", "operation"] = "method"
    ) -> OrderedDict[str, str]:
        """
        Return the keyword arguments for the given method.  The positional
        arguments are the arguments are required.  They will include a type.

        Example:
            ..code-block:: python

                {
                    'arg1': 'str'
                    'arg2': 'List[str]'
                }

        Keyword Args:
            location: where these arguments will be used.  If ``'method'``, then
                we only generate the arguments that are required for the method
                signature.  If ``'operation'``, then we generate all the arguments
                that are required for the boto3 operation call.

        Returns:
            A dictionary of argument names to types.

        """
        return self._args("args", location=location)

    def kwargs(
        self, location: Literal["method", "operation"] = "method"
    ) -> OrderedDict[str, str]:
        """
        Return the keyword arguments for the given method.  These apply to both
        the method signature and to the boto3 operation call.

        Keyword arguments are the arguments that are not required.  They will
        include a type and a default value.

        Example:
            ..code-block:: python

                {
                    'arg1': 'str = "default"',
                    'arg2': 'Optional[str] = None'
                }

        Keyword Args:
            location: where these arguments will be used.  If ``'method'``, then
                we only generate the arguments that are required for the method
                signature.  If ``'operation'``, then we generate all the arguments
                that are required for the boto3 operation call.

        Returns:
            A dictionary of argument names to types/defaults.

        """
        return self._args("kwargs", location=location)

    @property
    def operation_args(self) -> str:
        """
        Return the argument string for the boto3 call.  We use the
        output of :py:meth:`args` and :py:meth:`kwargs` to generate
        this string.

        Example:
            ``name=name, description=description``

        """
        args = self.args(location="operation")
        kwargs = self.kwargs(location="operation")
        arg_str = ", ".join([f"{arg}={self.serialize(arg)}" for arg in args])
        if args and kwargs:
            arg_str += ", "
        arg_str += ", ".join([f"{arg}={self.serialize(arg)}" for arg in kwargs])
        return f"args: Dict[str, Any] = dict({arg_str})"

    @property
    def operation_call(self) -> str:
        """
        A body snippet that does the actual boto3 call.  and assigns the
        response to ``_response``.  It then uses response to instantiate
        :py:meth:`response_class`.

        Example:
            ..code-block:: python

                _response = self.client.create(name=name, description=description)
                response = ResponseModel(**_response)

        Returns:
            The code for the boto3 call.

        """
        call = self.operation_args
        call = f"self.client.{self.boto3_name}(**{{k: v for k, v in args.items() if v is not None}})"  # noqa: E501
        if self.return_type in ("None", '"None"'):
            return call
        call = "_response = " + call
        call += f"\n        response = {self.response_class}(**_response)"
        return call

    @property
    def response_class(self) -> str:
        """
        Create the response class, add it to the list of response classes, and
        return the type string.  The response class is the class that we use to
        deserialize the boto3 response into a pydantic model.

        If there is no output shape defined in botocore for the boto3 operation, then
        we return ``None``.

        Returns:
            The name of the response class.

        """
        if self.output_shape is None:
            return "None"
        model_name = self.output_shape.name
        self.model_generator.generate_model(
            model_name, model_shape=self.operation_model.output_shape
        )
        return model_name

    @property
    def response_attr(self) -> Optional[str]:
        """
        Deduce the name of the attribute in the boto3 response that we want to
        return from the method.  This is either some variation of the name of
        the model itself, or whatever the botocraft config for the method
        specifies.

        Returns:
            The name of the attribute in the boto3 response that we want to
            return from the method.

        """
        response_attr: Optional[str] = None
        if self.output_shape is None:
            return None
        if not hasattr(self.output_shape, "members"):
            return None
        if self.method_def.response_attr:
            if self.method_def.response_attr == "None":
                return None
            return self.method_def.response_attr
        potential_names = [
            self.model_name.lower(),
            self.model_name_plural.lower(),
        ]
        # We need to take into account when we rename an attribute on a response
        # shape, e.g. ``CreateLaunchTemplateResult`` has an attribute
        # ``LaunchTemplate`` that we rename to ``LaunchTemplateInstance``.
        # Searching through the shape.members dictionary doesn't work in this
        # case, because the attribute name is different
        response_attrs = {attr.lower(): attr for attr in self.output_shape.members}
        response_model_def = self.model_generator.get_model_def(self.output_shape.name)
        for field_data in response_model_def.fields.values():
            if field_data.rename:
                response_attrs[field_data.rename.lower()] = field_data.rename
        for attr in response_attrs:
            if attr in potential_names:
                response_attr = response_attrs[attr]
                break
        attrs = ", ".join([f'"{attr}"' for attr in self.output_shape.members])
        if response_attr:
            # What we're doing here is trying to figure out if the response_attr is
            # references a specific key or index in a list or dictionary.  If it does,
            # strip that off so we can see if the attribute is actually a field on the
            # response class.
            test_attr = re.split(r"\[|\.", response_attr)[0]
            if test_attr not in self.output_shape.members:
                msg = (
                    f"{self.model_name}Manager.{self.method_name}: {test_attr} "
                    f"is not a field on the response class {self.output_shape.name}: "
                    f"{attrs}"
                )
                raise KeyError(msg)
            return response_attr
        msg = (
            f"Can't deduce response attribute for response class "
            f"{self.output_shape.name}: {attrs}"
        )
        raise ValueError(msg)

    @property
    def response_attr_multiplicity(self) -> Literal["one", "many"]:
        """
        Determine if the response attribute is a list or not.

        Returns:
            ``'one'`` if the response attribute is not a list, ``'many'`` if it
            is a list.

        """
        if self.output_shape is None:
            return "one"
        if not hasattr(self.output_shape, "members"):
            return "one"
        if self.response_attr is None:
            return "one"
        # What we're doing here is trying to figure out if the response_attr is
        # references a specific key or index in a list or dictionary.  If it does,
        # strip that off so we can see if the attribute is actually a field on the
        # response class.
        test_attr = re.split(r"\[|\.", self.response_attr)[0]
        try:
            shape = self.output_shape.members[test_attr]
        except KeyError:
            response_model_def = self.model_generator.get_model_def(
                self.output_shape.name
            )
            for field, field_data in response_model_def.fields.items():
                if field_data.rename == self.response_attr:
                    shape = self.output_shape.members[field]
                    break
            else:
                raise
            # Maybe we're dealing with a renamed field
        if hasattr(shape, "type") and shape.type == "list":
            return "many"
        if hasattr(shape, "type_name") and shape.type_name == "list":
            return "many"
        return "one"

    @property
    def return_type(self) -> str:
        """
        Set the type hint for the return type of the method.  This is either the
        response class, or whatever class the botocraft config for the method
        specifies.

        Returns:
            The type hint for the return type of the method.

        """
        if self.method_def.return_type:
            return self.method_def.return_type
        # If our output shape has no members, then we return None
        output_shape = cast(botocore.model.StructureShape, self.output_shape)
        if (
            not hasattr(output_shape, "members")
            or hasattr(output_shape, "members")
            and not output_shape.members
        ):
            return "None"
        if self.response_attr is None:
            if self.output_shape is None:
                return "None"
            return self.shape_converter.convert(self.output_shape, quote=True)
        if self.output_shape is not None:
            try:
                response_attr_shape = self.output_shape.members[
                    cast(str, self.response_attr)
                ]
            except KeyError:
                response_model_def = self.model_generator.get_model_def(
                    self.output_shape.name
                )
                for field, field_data in response_model_def.fields.items():
                    if field_data.rename == self.response_attr:
                        response_attr_shape = self.output_shape.members[
                            cast(str, field)
                        ]
                        break
                else:
                    raise
        return_type = self.shape_converter.convert(response_attr_shape, quote=True)
        # Deal with the primary model itself having an alternate name
        if self.model_def.alternate_name:
            if f'"{self.model_name}"' in return_type:
                return_type = return_type.replace(
                    f'"{self.model_name}"', f'"{self.model_def.alternate_name}"'
                )
        return return_type

    @property
    def decorators(self) -> Optional[str]:
        """
        Return the decorators for the method, if any.

        Returns:
            Decorators for the method, or ``None`` if there are none.

        """
        if not self.method_def.decorators:
            return None
        code = ""
        for decorator in self.method_def.decorators:
            code += f"    @{decorator.name}\n"
            if decorator.import_path:
                self.imports.add(
                    f"from {decorator.import_path} import {decorator.name}"
                )
        return code + "\n"

    @property
    def signature(self) -> str:
        """
        Create the method signature for the method.

        Example:

            .. code-block:: python

                def create(self, name: str, *, description: str) -> Model:

        Returns:
            The method signature for the method.

        """
        args = self.args()
        kwargs = self.kwargs()
        args_str = ", ".join([f"{arg}: {arg_type}" for arg, arg_type in args.items()])
        kwargs_str = ", ".join(
            [f"{arg}: {arg_type}" for arg, arg_type in kwargs.items()]
        )
        signature = f"    def {self.method_name}(self, "
        if args_str:
            signature += args_str
        if args_str and kwargs_str:
            signature += ", "
        if kwargs_str:
            signature += f"*, {kwargs_str}"
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
        _arg_name = arg
        arg_def = MethodArgumentDefinition()
        for arg_name, _arg_def in self.method_def.args.items():
            if arg_name == arg:
                arg_def = _arg_def
                break
            if _arg_def.rename == arg:
                arg_def = _arg_def
                _arg_name = arg_name
                break
        if arg_def.docstring:
            return arg_def.docstring
        if self.input_shape is not None:
            if _arg_name in self.input_shape.members:
                return self.input_shape.members[_arg_name].documentation
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
            self.method_def.docstring
            if self.method_def.docstring
            else self.operation_model.documentation
        )
        for arg in self.args():
            docstrings.args[arg] = self.get_arg_docstring(arg)
        for arg in self.kwargs():
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
        code = ""
        if decorators := self.decorators:
            code += decorators
        code += self.signature
        if docstring := self.docstring:
            code += docstring
        code += self.body
        return code
