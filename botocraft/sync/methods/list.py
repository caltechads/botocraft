from .base import MethodGenerator


class ListMethodGenerator(MethodGenerator):

    operation: str = 'list'

    @property
    def return_type(self) -> str:
        """
        For list methods, we return a list of model instances, not the response
        model, unless it's overriden in our botocraft operation config, in which
        case we return that.

        Thus we need to change the return type to a list of the model.

        Returns:
            The name of the return type class.
        """
        _ = self.response_class
        return_type = f'List[{self.model_name}]'
        if self.operation_def.return_type:
            return_type = self.operation_def.return_type
        return return_type

    @property
    def body(self) -> str:
        response_attr = self.model_name_plural.lower()
        if self.operation_def.response_attr:
            response_attr = self.operation_def.response_attr
        code = f"""
        {self.operation_call}
        return response.{response_attr}
"""
        return code
