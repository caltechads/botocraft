from collections import OrderedDict
from typing import cast

from botocraft.sync.models import OperationArgumentDefinition

from .base import MethodGenerator, MethodDocstringDefinition


class CreateMethodGenerator(MethodGenerator):
    """
    Handle the generation of a create method.
    """

    operation: str = 'create'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operation_def.args.update(
            self.get_explicit_args_from_request()
        )

    @property
    def signature(self) -> str:
        """
        For create methods, we add the model as the only argument.

        Returns:
            The method signature for the operation.
        """
        signature = f'    def {self.operation}(self, model: "{self.model_name}"'
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
        mapping = self.operation_def.args
        _args: OrderedDict[str, str] = OrderedDict()
        for arg in self.args:
            if arg in self.explicit_args:
                _arg = self.serialize(arg)
            else:
                if arg in mapping:
                    if mapping[arg].hidden:
                        continue
                _arg = f"data['{arg}']"
                if arg in mapping:
                    if mapping[arg].source_arg:
                        _arg = self.serialize(cast(str, mapping[arg].source_arg))
                    elif mapping[arg].attribute:
                        _arg = f"data['{mapping[arg].attribute}']"
            _args[arg] = _arg
        return ", ".join(
            [f"{arg}={_arg}" for arg, _arg in _args.items()]
        )

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
        mapping = self.operation_def.args
        _args = OrderedDict()
        for arg in self.kwargs:
            if arg in self.explicit_kwargs:
                _arg = self.serialize(arg)
            else:
                if arg in mapping:
                    if mapping[arg].hidden:
                        continue
                _arg = f"data['{arg}']"
                if arg in mapping:
                    if mapping[arg].source_arg:
                        _arg = self.serialize(cast(str, mapping[arg].source_arg))
                    elif mapping[arg].attribute:
                        _arg = f"data['{mapping[arg].attribute}']"
            _args[arg] = _arg
        return ", ".join(
            [f"{arg}={_arg}" for arg, _arg in _args.items()]
        )

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
        if args := self.operation_args:
            call += args
        if self.args and self.kwargs:
            call += ", "
        if kwargs := self.operation_kwargs:
            call += kwargs
        call += ")"
        call += f"\n        response = {self.response_class}.model_construct(**_response)"
        return call

    @property
    def docstrings_def(self) -> MethodDocstringDefinition:
        """
        Return the docstring for the method.
        """
        docstrings: MethodDocstringDefinition = MethodDocstringDefinition()
        docstrings.method = (
            self.operation_def.docstring
            if self.operation_def.docstring
            else self.operation_model.documentation
        )
        docstrings.args['model'] = f'The :py:class:`{self.model_name}` to create.'
        for arg in self.explicit_args:
            docstrings.args[arg] = self.get_arg_docstring(arg)
        for arg in self.explicit_kwargs:
            docstrings.kwargs[arg] = self.get_arg_docstring(arg)
        return docstrings

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
        return_type = f'"{self.model_name}"'
        if self.operation_def.return_type:
            return_type = self.operation_def.return_type
        return return_type
