from collections import OrderedDict
import re

from .base import MethodGenerator


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
        return_type = f'Optional[{self.model_name}]'
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
        response_attr = self.model_name_plural.lower()
        if self.operation_def.response_attr:
            response_attr = self.operation_def.response_attr
        code = f"""
        {self.operation_call}
        if response.{response_attr}:
            return response.{response_attr}[0]  # type: ignore # pylint: disable=unsubscriptable-object
        return None
"""
        return code
