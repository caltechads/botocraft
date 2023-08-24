from .base import MethodGenerator


class DeleteMethodGenerator(MethodGenerator):
    """
    Generate the code for the delete method.

    boto3 delete methods typically return the dict of the full object that was
    deleted, so we'll convert that to the model we're working with and return
    that instead.
    """

    operation: str = 'delete'

    @property
    def return_type(self) -> str:
        """
        For delete methods, we return the model itself, not the response model,
        unless it's overriden in our botocraft operation config, in which case
        we return that.

        Returns:
            The name of the return type class.
        """
        _ = self.response_class
        return_type = f'"{self.model_name}"'
        if self.operation_def.return_type:
            return_type = self.operation_def.return_type
        return return_type

    @property
    def body(self) -> str:
        """
        Generate the method body code for the delete method.
        """
        response_attr = self.model_name.lower()
        if self.operation_def.response_attr:
            response_attr = self.operation_def.response_attr
        code = f"""
        {self.operation_call}
"""
        if not self.return_type == 'None':
            code += f"        return cast({self.model_name}, response.{response_attr})"
        return code
