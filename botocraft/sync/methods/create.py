from collections import OrderedDict
from typing import cast

from botocraft.sync.models import OperationArgumentDefinition

from .base import MethodGenerator


class CreateMethodGenerator(MethodGenerator):
    """
    Handle the generation of a create method.
    """

    operation: str = 'create'

    @property
    def signature(self) -> str:
        """
        For create methods, we add the model as the only argument.

        Returns:
            The method signature for the operation.
        """
        signature = f"    def {self.operation}(self, model: {self.model_name}"
        if self.explicit_args or self.explicit_kwargs:
            signature += ", "
        signature += ", ".join([f"{arg}: {arg_type}" for arg, arg_type in self.explicit_args.items()])
        if self.explicit_args and self.explicit_kwargs:
            signature += ", "
        signature += ", ".join([
            f"{arg}: {arg_type} = {self.operation_def.args.get(arg, OperationArgumentDefinition()).default}"
            for arg, arg_type in self.explicit_kwargs.items()
        ])
        signature += f") -> {self.return_type}:"
        return signature

    @property
    def operation_args(self) -> OrderedDict[str, str]:
        """
        Get the map of argument name to value of arguments for the boto3 operation call.

        Returns:
            The map of argument name to value of arguments for the boto3 operation call.
        """
        mapping = self.operation_def.args
        _args: OrderedDict[str, str] = OrderedDict()
        for arg in self.args:
            if arg in self.explicit_args:
                _arg = arg
            else:
                if arg in mapping:
                    if mapping[arg].hidden:
                        continue
                _arg = f"data['{arg}']"
                if arg in mapping:
                    if mapping[arg].source_arg:
                        _arg = cast(str, mapping[arg].source_arg)
                    elif mapping[arg].attribute:
                        _arg = f"data['{mapping[arg].attribute}']"
            _args[arg] = _arg
        return _args

    @property
    def operation_kwargs(self) -> OrderedDict[str, str]:
        mapping = self.operation_def.args
        _args = OrderedDict()
        for arg in self.kwargs:
            if arg in self.explicit_kwargs:
                _arg = arg
            else:
                if arg in mapping:
                    if mapping[arg].hidden:
                        continue
                _arg = f"data['{arg}']"
                if arg in mapping:
                    if mapping[arg].source_arg:
                        _arg = cast(str, mapping[arg].source_arg)
                    elif mapping[arg].attribute:
                        _arg = f"data['{mapping[arg].attribute}']"
            _args[arg] = _arg
        return _args

    @property
    def operation_call(self) -> str:
        """
        This is a body snippet that does the actual boto3 call.  and assigns the
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
        call = "data = model.model_dump()"
        call += f"\n        _response = self.client.{self.boto3_name}("
        call += ", ".join(
            [f"{arg}={_arg}" for arg, _arg in self.operation_args.items()]
        )
        if self.args and self.kwargs:
            call += ", "
        call += ", ".join(
            [f"{arg}={_arg}" for arg, _arg in self.operation_kwargs.items()]
        )
        call += ")"
        call += f"\n        response = {self.response_class}.model_construct(**_response)"
        return call

    @property
    def body(self) -> str:
        response_attr = self.model_name.lower()
        if self.operation_def.response_attr:
            response_attr = self.operation_def.response_attr
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
        return_type = self.model_name
        if self.operation_def.return_type:
            return_type = self.operation_def.return_type
        return return_type
