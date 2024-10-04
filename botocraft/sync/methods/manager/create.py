import re
from collections import OrderedDict
from typing import cast

from botocraft.sync.models import MethodArgumentDefinition

from ...models import MethodDocstringDefinition
from .base import ManagerMethodGenerator


class CreateMethodGenerator(ManagerMethodGenerator):
    """
    Handle the generation of a create method.
    """

    method_name: str = "create"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method_def.args.update(self.get_explicit_args_from_request())

    @property
    def signature(self) -> str:
        """
        For create methods, we add the model as the only argument.

        Returns:
            The method signature for the method.

        """
        if self.model_def.alternate_name:
            model_name = self.model_def.alternate_name
        else:
            model_name = self.model_name
        signature = f'    def {self.method_name}(self, model: "{model_name}"'
        if self.explicit_args or self.explicit_kwargs:
            signature += ", "
        signature += ", ".join(
            [f"{arg}: {arg_type}" for arg, arg_type in self.explicit_args.items()]
        )
        if self.explicit_args and self.explicit_kwargs:
            signature += ", "
        signature += ", ".join(
            [
                f"{arg}: {arg_type} = {self.method_def.args.get(arg, MethodArgumentDefinition()).default}"  # noqa: E501
                for arg, arg_type in self.explicit_kwargs.items()
            ]
        )
        signature += f") -> {self.return_type}:"
        return signature

    @property
    def operation_args(self) -> str:
        """
        Get positional argument string for the boto3 operation call.

        Example:

            .. code-block:: python

                "arg1=data['arg1'], arg2=data['arg2']"

        We're overriding this because we need to map get most of our arguments
        for the boto3 call from the model attributes, not the method arguments,
        which is what
        :py:meth:`botocraft.sync.methods.base.MethodGenerator.operation_args`
        provides.

        Returns:
            The string to use to represent the boto3 operation positional
            arguments.

        """
        mapping = self.method_def.args
        _args: OrderedDict[str, str] = OrderedDict()
        for arg in self.args(location="operation"):
            arg_def = mapping.get(arg, MethodArgumentDefinition())
            if arg in self.explicit_args:
                _arg = self.serialize(arg)
            else:
                if arg_def.hidden:
                    continue
                _arg = f"data.get('{arg}')"
                if arg_def.value:
                    _arg = self.serialize(cast(str, arg_def.value))
                elif arg_def.source_arg:
                    _arg = self.serialize(cast(str, arg_def.source_arg))
                elif arg_def.attribute:
                    _arg = f"data['{arg_def.attribute}']"
            _args[arg] = _arg
        return ", ".join([f"{arg}={_arg}" for arg, _arg in _args.items()])

    @property
    def operation_kwargs(self) -> str:
        """
        Get keyword argument string for the boto3 operation call.

        Example:

            .. code-block:: python

                "arg1=data['arg1'], arg2=data['arg2']"

        We're overriding this because we need to map get most of our arguments
        for the boto3 call from the model attributes, not the method arguments,
        which is what
        :py:meth:`botocraft.sync.methods.base.MethodGenerator.operation_kwargs`
        provides.

        Returns:
            The string to use to represent the boto3 operation positional
            arguments.

        """
        mapping = self.method_def.args
        _args = OrderedDict()
        for arg in self.kwargs(location="operation"):
            arg_def = mapping.get(arg, MethodArgumentDefinition())
            if arg in self.explicit_kwargs:
                _arg = self.serialize(arg)
            else:
                if arg_def.hidden:
                    continue
                _arg = f"data.get('{arg}')"
                if arg_def.value:
                    if arg_def.raw_value:
                        _arg = arg_def.value
                    else:
                        _arg = self.serialize(cast(str, arg_def.value))
                elif arg_def.source_arg:
                    _arg = self.serialize(cast(str, arg_def.source_arg))
                elif arg_def.attribute:
                    _arg = f"data['{arg_def.attribute}']"
            _args[arg] = _arg
        return ", ".join([f"{arg}={_arg}" for arg, _arg in _args.items()])

    @property
    def operation_call(self) -> str:
        """
        A body snippet that does the actual boto3 call.  and assigns the
        response to ``_response``, then loads the ``_response`` into
        :py:meth:`response_class``.

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
        call = "data = model.model_dump(exclude_none=True, by_alias=True)"
        args = self.operation_args
        kwargs = self.operation_kwargs
        if args or kwargs:
            call += "\n        args = dict("
        if args:
            call += args
        if args and kwargs:
            call += ", "
        if kwargs:
            call += kwargs
        call += ")"
        if self.return_type == "None":
            call += f"\n        self.client.{self.boto3_name}(**{{k: v for k, v in args.items() if v is not None}})"  # noqa: E501
        else:
            call += f"\n        _response = self.client.{self.boto3_name}(**{{k: v for k, v in args.items() if v is not None}})"  # noqa: E501
            call += f"\n        response = {self.response_class}(**_response)"
        return call

    @property
    def docstrings_def(self) -> MethodDocstringDefinition:
        """
        Return the docstring for the method.
        """
        docstrings: MethodDocstringDefinition = MethodDocstringDefinition()
        docstrings.method = (
            self.method_def.docstring
            if self.method_def.docstring
            else self.operation_model.documentation
        )
        docstrings.args["model"] = f"The :py:class:`{self.model_name}` to create."
        for arg in self.explicit_args:
            docstrings.args[arg] = self.get_arg_docstring(arg)
        for arg in self.explicit_kwargs:
            docstrings.kwargs[arg] = self.get_arg_docstring(arg)
        return docstrings

    @property
    def body(self) -> str:
        response_attr = cast(str, self.response_attr)
        if self.response_attr_multiplicity == "many":
            response_attr = f"{response_attr}[0]"
        code = f"""
        {self.operation_call}
"""
        if self.return_type != "None":
            code += f"""
        if hasattr(response.{response_attr}, "session"):
            response.{response_attr}.set_session(self.session)
        return cast({self.return_type}, response.{response_attr})
"""
        return code

    @property
    def return_type(self) -> str:
        """
        For create, update and delete methods, we return the model itself, not
        the response model, unless it's overriden in our botocraft method
        config, in which case we return that.

        Returns:
            The name of the return type class.

        """
        return_type = super().return_type
        # Sometimes the return type is a list of the model, e.g.
        # ``elbv2:create_load_balancer``, so we need to strip the ``List`` part of the
        # return type, because we want to return just the model, if possible.
        if return_type.startswith("List["):
            return_type = re.sub(r"List\[(.*)\]", r"\1", return_type)
        return return_type
