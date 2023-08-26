from collections import OrderedDict
import re
from typing import cast

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

    operation: str = 'get'

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
        return_type = f'Optional["{self.model_name}"]'
        if self.operation_def.return_type:
            return_type = self.operation_def.return_type
        return return_type

    @property
    def body(self) -> str:
        """
        Generate the code for the get method.

        Returns:
            The code for the get method.
        """
        code = f"""
        {self.operation_call}
"""
        # Assume the response attribute is a string and not None in this case,
        # since we definitely want to return something
        response_attr = cast(str, self.response_attr)
        # Since this is a get method, we can assume that the response will
        # always be a StructureShape
        if self.response_attr_multiplicity == 'many':
            code += f"""
        if response.{response_attr}:
            return response.{response_attr}[0]
        return None
"""
        else:
            code += f"""
        return response.{response_attr}
"""
        return code
