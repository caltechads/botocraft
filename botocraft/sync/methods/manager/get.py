from collections import OrderedDict
from typing import Literal, cast

from .base import ManagerMethodGenerator


class GetMethodGenerator(ManagerMethodGenerator):
    """
    Generate the code for the ``get`` method.

    There typically is no boto3 operation that gets a single object, so we'll
    have to find the boto3 operation that returns the all the data
    we need for our model and then filter it down to the single object we're
    looking for.

    This also means changing the method signature to prevent people from
    asking for multiple objects.
    """

    method_name: str = "get"

    def kwargs(
        self, location: Literal["method", "operation"] = "method"
    ) -> OrderedDict[str, str]:
        """
        Override the kwargs to exclude the pagination arguments if the boto3
        operation can paginate.  We should only ever be returning one object, so
        we don't need to paginate.
        """
        _args: OrderedDict[str, str] = OrderedDict()
        for _arg, arg_type in super().kwargs(location=location).items():
            if _arg not in self.PAGINATOR_ARGS:
                _args[_arg] = arg_type
        return _args

    @property
    def return_type(self) -> str:
        """
        For get methods, we return the model itself, not the response model,
        unless it's overriden in our botocraft method config, in which case
        we return that.

        Returns:
            The name of the return type class.

        """
        _ = super().return_type
        if self.method_def.return_type:
            return_type = self.method_def.return_type
        elif self.model_def.alternate_name:
            return_type = f'"{self.model_def.alternate_name} | None"'
        else:
            return_type = f'"{self.model_name} | None"'
        return return_type

    @property
    def response_class(self) -> str:
        """
        For ``get`` methods without a nested response attribute, hydrate the
        primary model directly instead of the botocore output wrapper, unless
        the method explicitly declares a different response model.

        Returns:
            The response class to instantiate from the boto3 payload.

        """
        if self.output_shape is None:
            return "None"
        if self.response_attr is None:
            if self.method_def.return_type:
                explicit_return_type = self.method_def.return_type.strip('"')
                primary_return_types = {
                    self.real_model_name,
                    f"{self.real_model_name} | None",
                }
                if explicit_return_type not in primary_return_types:
                    return super().response_class
            self.model_generator.generate_single_model(self.model_name)
            return self.real_model_name
        return super().response_class

    @property
    def body(self) -> str:
        """
        Generate the code for the get method.

        Returns:
            The code for the get method.

        """
        code = f"""
        {self.operation_args}
        {self.operation_call}
"""
        # Assume the response attribute is a string and not None in this case,
        # since we definitely want to return something
        response_attr = cast("str", self.response_attr)
        # Since this is a get method, we can assume that the response will
        # always be a StructureShape
        if response_attr:
            if self.response_attr_multiplicity == "many":
                code += f"""
        if response and response.{response_attr}:
            self.sessionize(response.{response_attr}[0])
            return response.{response_attr}[0]
        return None
"""
            else:
                code += f"""
        if response and response.{response_attr}:
            self.sessionize(response.{response_attr})
            return response.{response_attr}
        return None
"""
        else:
            code += """
        if response:
            self.sessionize(response)
            return response
        return None
"""
        return code
