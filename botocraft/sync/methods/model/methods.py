from collections import OrderedDict
from typing import TYPE_CHECKING, Dict, List, Optional, cast

from botocraft.sync.models import MethodArgumentDefinition, MethodDocstringDefinition

if TYPE_CHECKING:
    from botocraft.sync.models import ModelManagerMethodArgDefinition
    from botocraft.sync.service import DocumentationFormatter, ServiceGenerator


class ModelManagerMethodGenerator:
    """
    The base class for all model manager methods.  These all methods
    that transparently interact with the manager class on the object's
    behalf so that you don't have to do things like.

    .. code-block:: python

        image = Image.objects.get(pk="my-image")
        scan_results = Image.objects.scan_results(imageIds=[ImageIdentifier(image.imageId)])

    And can instead do:

    .. code-block:: python

        image = Image.objects.get(pk="my-image")
        scan_results = image.scan_results()

    To use this, you subclass it and implement the :py:meth:`body`
    property, which is the body of the method.  You can also override
    any of the following properties to customize the method:

    * :py:meth:`decorator`: The method decorators.
    * :py:meth:`signature`: The method signature.
    * :py:meth:`docstring`: The method docstring.
    * :py:meth:`return_type`: The return type annotation.

    Args:
        generator: The model generator that is creating the model class
        model_name: The name of the model we're generating the property for.

    """  # noqa: E501

    def __init__(
        self,
        generator: "ServiceGenerator",
        model_name: str,
        method_name: str,
    ) -> None:
        #: The generator that is creating the service classes for an AWS Service.
        self.generator = generator
        #: The model generator that is creating the model class
        self.model_generator = self.generator.model_generator
        #: The name of the model we're generating the property for.
        self.model_name = model_name
        #: The definition of the model we're generating the property for.
        self.model_def = self.generator.model_generator.get_model_def(model_name)
        #: The name of the method_name we're generating.
        self.method_name = method_name
        #: The definition of the method we're generating.
        self.method_def = self.model_def.manager_methods[self.method_name]
        #: The definition of the manager whose method we're accessing
        self.manager_def = self.generator.service_def.managers[model_name]

        # Validate that the manager method is valid
        if self.method_def.manager_method not in self.manager_def.methods:
            msg = (
                f"{self.model_name}.{self.method_name}: The manager method "
                f"{self.method_def.manager_method} is not a valid method for the "
                f"manager {model_name}Manager."
            )
            raise ValueError(msg)
        # Validate that the manager method is not one that we've already implemented
        if self.method_def.manager_method in ["create", "update"]:
            msg = (
                f"{self.model_name}.{self.method_name}: The model method "
                f"{self.model_name}.save() already implements "
                f'"{self.method_def.manager_method}".'
            )
            raise ValueError(msg)
        if self.method_def.manager_method == "delete":
            msg = (
                f"{self.model_name}.{self.method_name}: The model method "
                f"{self.model_name}.delete() already implements "
                f'"{self.method_def.manager_method}".'
            )
            raise ValueError(msg)
        #: The manager generator for the model
        self.manager_method_def = self.manager_def.methods[
            self.method_def.manager_method
        ]
        #: The botocore service model for the service we're generating.
        self.service_model = generator.manager_generator.service_model  # type: ignore[has-type]
        #: The AWS API method for the operation we're generating.  This is
        #: something like ``DescribeInstances``.
        botocore_name = generator.manager_generator.client._PY_TO_OP_NAME[  # type: ignore[has-type]  # noqa: SLF001
            self.manager_method_def.boto3_name
        ]
        #: The botocore operation model for the operation we're generating.
        self.operation_model = self.service_model.operation_model(botocore_name)
        #: The input shape for the boto3 operation
        self.input_shape = self.operation_model.input_shape
        self.method_generator = self.generator.manager_generator.get_method_generator(
            self.model_name,
            self.method_def.manager_method,
            self.manager_method_def,
        )
        self.docformatter = cast(
            "DocumentationFormatter",
            generator.manager_generator.docformatter,  # type: ignore[has-type]
        )

    @property
    def decorators(self) -> Optional[str]:
        """
        The decorators for the method.  If the method definition has decorators
        defined, add those first.

        If :py:attr:`botocraft.sync.models.ModelManagerMethodDefinition.cached``
        is to ``True``, also add the ``@lru_cache`` decorator.

        Returns:
            The decorators for the method, or ``None`` if there are none.

        """
        decorators: List[str] = []
        if self.method_def.decorators:
            for decorator in self.method_def.decorators:
                decorators.append(f"    @{decorator.name}")
                if decorator.import_path:
                    self.generator.imports.add(
                        f"from {decorator.import_path} import {decorator.name}"
                    )
        if self.method_def.cached:
            self.generator.imports.add("from functools import lru_cache")
            decorators.append("    @lru_cache")
        if decorators:
            return "\n".join(decorators)
        return None

    @property
    def return_type(self) -> str:
        """
        Return the return type annotation for the method.  We should read
        the return type from the manager method definition.
        """
        if self.manager_method_def.return_type is not None:
            return self.manager_method_def.return_type
        if self.method_generator.output_shape is not None:
            output_shape = self.method_generator.output_shape
            response_attr = self.method_generator.response_attr
            _return_shape = None
            if response_attr is not None:
                try:
                    response_attr_shape = output_shape.members[cast(str, response_attr)]
                except KeyError:
                    response_model_def = self.model_generator.get_model_def(
                        output_shape.name
                    )
                    for field, field_data in response_model_def.fields.items():
                        if field_data.rename == response_attr:
                            response_attr_shape = output_shape.members[cast(str, field)]
                            break
                    else:
                        raise
                _return_shape = response_attr_shape
            _return_shape = output_shape
            return self.model_generator.shape_converter.convert(
                _return_shape, quote=True, name_only=True
            )
        return "None"

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
        for arg_name, _arg_def in self.manager_method_def.args.items():
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
        if self.method_def.docstring:
            docstrings.method = self.method_def.docstring
        elif self.manager_method_def.docstring:
            docstrings.method = self.manager_method_def.docstring
        else:
            docstrings.method = self.operation_model.documentation
        for arg in self.method_def.user_args.values():
            docstrings.args[arg.name] = self.get_arg_docstring(arg.name)
        for kwarg in self.method_def.user_keyword_args:
            docstrings.kwargs[kwarg.name] = self.get_arg_docstring(kwarg.name)
        return docstrings

    @property
    def docstring(self) -> Optional[str]:
        """
        Return the docstring for the method.
        """
        return self.docstrings_def.render(self.docformatter)

    @property
    def signature(self) -> str:
        """
        Return the method signature.

        Returns:
            The method signature.

        """
        sig: str = f"    def {self.method_name}(self"
        # First get the args and kwargs we know are on the manager method
        manager_args = self.method_generator.args("method")
        manager_kwargs = self.method_generator.kwargs("method")
        if self.method_def.user_args:
            # Deal with the user_args.  These are arguments that the user of this
            # method still need to supply, rather than getting the value from the
            # object
            user_args = OrderedDict(sorted(self.method_def.user_args.items()))
            for arg in user_args.values():
                if arg.name not in manager_args:
                    # If the argument name is one of the manager method arguments, then
                    # raise an error
                    msg = (
                        f"{self.model_name}.{self.method_name}: The argument {arg.name}"
                        " is not a valid argument for "
                        f"the manager method {self.method_def.manager_method}."
                    )
                    raise ValueError(msg)
                attr_type: Optional[str] = arg.attr_type
                if arg.attr_type is None:
                    # If the argument type is not specified, then use the type
                    # from the manager method
                    attr_type = manager_args[arg.name]
                sig += f", {arg.name}: {attr_type}"
        if self.method_def.user_keyword_args:
            # Deal with the user_keyword_args.  These are keyword arguments that the
            # user of this method still need to supply, rather than getting the value
            # from the object
            for kwarg in self.method_def.user_keyword_args:
                if kwarg.name not in manager_kwargs:
                    # If the keyword argument name is not in the manager method, then
                    # raise an error
                    msg = (
                        f"{self.model_name}.{self.method_name}: The keyword argument"
                        f" {kwarg.name} is not a valid keyword argument for the "
                        f"manager method {self.method_def.manager_method}."
                    )
                    raise ValueError(msg)
                # Building the argument here is a bit more complicated because
                # we need to handle the default value.
                if not kwarg.default:
                    # A manager kwarg string will look like "type = default", so
                    # we need to split it on the " = " and take the second half
                    # to get the default value
                    default = manager_kwargs[kwarg.name].split(" = ")[1]
                else:
                    # We're overriding the default value
                    default = kwarg.default
                attr_type = kwarg.attr_type
                if attr_type is None:
                    # A manager kwarg string will look like "type = default", so
                    # we need to split it on the " = " and take the first half
                    # to get the type
                    attr_type = manager_kwargs[kwarg.name].split(" = ")[0]
                attr_type_default = f"{attr_type} = {default}"
                sig += f", {kwarg.name}: {attr_type_default}"
        return_type = self.return_type
        if '"' not in return_type:
            return_type = f'"{return_type}"'
        sig += f") -> {return_type}:"
        return sig

    @property
    def args(self) -> str:
        """
        Return the method arguments from the method definition only.  These
        are the ones that the user must supply when calling the method.  The other
        arguments are supplied by the object.

        Returns:
            The method arguments.

        """
        args_dict: Dict[int, "ModelManagerMethodArgDefinition"] = (  # noqa: UP037
            self.method_def.args | self.method_def.user_args
        )
        if not args_dict:
            return ""
        # The keys in args_dict are positions (zero-based), and the values are the
        # argument names.  We need to validate that the positions are sequential,
        # and that 0 is in the args_dict.
        if 0 not in args_dict:
            msg = (
                f"{self.model_name}.{self.method_name}: There is no "
                "argument in the 0th position."
            )
            raise ValueError(msg)
        # Validate that we're not missing any argument posiions
        for i in range(1, len(args_dict)):
            if i not in args_dict:
                msg = (
                    f"{self.model_name}.{self.method_name}: Argument at "
                    f"position {i} is missing."
                )
                raise ValueError(msg)
        args: OrderedDict[int, str] = OrderedDict()
        for i in range(len(args_dict)):  # pylint: disable=consider-using-enumerate
            if i in self.method_def.args:
                if args_dict[i].value is not None:
                    args[i] = cast(str, args_dict[i].value)
                else:
                    value = args_dict[i].name
                    if "self." not in value:
                        value = f"self.{value}"
                    args[i] = value
            else:
                args[i] = args_dict[i].name
        return ", ".join([f"{arg}, " for arg in args.values()])

    @property
    def kwargs(self) -> str:
        """
        Return the method keyword arguments from the method definition only.  These
        are the ones that the user must supply when calling the method.  The other
        arguments are supplied by the object.

        Returns:
            The method keyword arguments.

        """
        if not self.method_def.keyword_args and not self.method_def.user_keyword_args:
            return ""
        kwargs: List[str] = []
        if self.method_def.keyword_args:
            for arg in self.method_def.keyword_args:
                if arg.value is not None:
                    kwargs.append(f"{arg.name}={arg.value}")
                else:
                    kwargs.append(f"{arg.name}=self.{arg.name}")
        if self.method_def.user_keyword_args:
            kwargs = [
                f"{arg.name}={arg.name}" for arg in self.method_def.user_keyword_args
            ]
        return ", ".join(kwargs)

    @property
    def body(self) -> str:
        """
        Return the method body.

        Returns:
            The method body.

        """
        args = self.args
        kwargs = self.kwargs
        code = f"""
        return cast({self.model_name}Manager, self.objects).using(self.session).{self.method_def.manager_method}({args}{kwargs})
"""  # noqa: E501
        return code  # noqa: RET504

    @property
    def code(self) -> str:
        """
        Return the code for the method.

        Returns:
            The code for the method.

        """
        code = """

"""
        decorators = self.decorators
        if decorators is not None:
            code += f"""
{decorators}
"""
        code += f"""
{self.signature}
{self.docstring}
{self.body}
"""
        return code
