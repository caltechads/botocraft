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
        return_type = f'Union[PrimaryBoto3ModelQuerySet, "{self.response_class}"]'
        if (
            self.response_attr
            and self.response_attr not in self.output_shape.required_members
        ):
            return_type = f"Optional[{return_type}]"
        if self.method_def.return_type:
            return_type = self.method_def.return_type
        return return_type

    @property
    def body(self) -> str:
        self.imports.add("from .abstract import PrimaryBoto3ModelQuerySet")
        code = f"""
        {self.operation_args}
        {self.operation_call}
"""
        if self.response_attr is not None:
            code += f"""
        if response.{self.response_attr}:
            self.sessionize(response.{self.response_attr})
            return PrimaryBoto3ModelQuerySet(response.{self.response_attr})
        return PrimaryBoto3ModelQuerySet([])
"""
        else:
            code += """
        self.sessionize(response)
        return response
"""
        return code
