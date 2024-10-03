from .base import ManagerMethodGenerator


class GetManyMethodGenerator(ManagerMethodGenerator):
    """
    Generate the code for the ``get_many`` method.  This differs from the
    ``list`` method in that sometimes the boto3 operation that handles listing
    does not actually return all the data we need to create our model.  In those
    cases, there is usually a separate boto3 operation that returns lists of
    objects that we can use to get the full data we need.

    When this happens, the ``get_many`` boto3 operation typically cannot be
    paginated, otherwise we would have used it as the ``list`` method.
    """

    method_name: str = "get_many"

    @property
    def return_type(self) -> str:
        """
        For get_many methods, we return a list of model instances, not the response
        model, unless it's overriden in our botocraft method config, in which
        case we return that.

        Thus we need to change the return type to a list of the model.

        Returns:
            The name of the return type class.

        """
        _ = self.response_class
        return_type = f'List["{self.model_name}"]'
        if self.method_def.return_type:
            return_type = self.method_def.return_type
        return return_type

    @property
    def body(self) -> str:
        # This is a hard attribute to guess. Sometimes it's CamelCase, sometimes
        # it's camelCase, sometimes it's snake_case.  We'll just assume it's a
        # lowercase plural of the model name.
        code = f"""
        {self.operation_args}
        {self.operation_call}
"""
        if self.response_attr is not None:
            code += f"""
        if response.{self.response_attr} is not None:
            if hasattr(response.{self.response_attr}[0], "session"):
                objs = []
                for obj in response.{self.response_attr}:
                    obj.session = self.session
                    objs.append(obj)
                return objs
            else:
                return response.{self.response_attr}
"""
        else:
            code += """
        if response is not None:
            if hasattr(response[0], "session"):
                objs = []
                for obj in response:
                    obj.session = self.session
                    objs.append(obj)
                return objs
            else:
                return response
"""
        code += """
        return []
"""
        return code
