from typing import Optional

from .base import ManagerMethodGenerator


class DeleteMethodGenerator(ManagerMethodGenerator):
    """
    Generate the code for the delete method.

    boto3 delete methods typically return the dict of the full object that was
    deleted, so we'll convert that to the model we're working with and return
    that instead.
    """

    method_name: str = "delete"

    @property
    def response_attr(self) -> Optional[str]:
        """
        Override our superclass here to not throw an error if we can't find the
        response attribute.  This is because sometimes delete methods return
        nothing, so we'll just return None.

        Returns:
            The response attribute name, or ``None``.

        """
        try:
            return super().response_attr
        except ValueError:
            return None

    @property
    def return_type(self) -> str:
        """
        For delete methods, we return the model itself, not the response model,
        unless it's overriden in our botocraft method config, in which case
        we return that.

        Returns:
            The name of the return type class.

        """
        # Leave this here because the response_class property creates the
        # response class code if it doesn't exist.
        _ = self.response_class
        return_type = super().return_type
        if return_type != "None":
            return_type = f'"{self.model_name}"'
            if self.method_def.return_type:
                return_type = self.method_def.return_type
        return return_type

    @property
    def body(self) -> str:
        """
        Generate the method body code for the delete method.
        """
        code = f"""
        {self.operation_args}
        {self.operation_call}
"""
        if self.return_type != "None":
            if self.response_attr is None:
                code += "        return response"
            else:
                code += f"        return cast({self.model_name}, response.{self.response_attr})"  # noqa: E501
        return code
