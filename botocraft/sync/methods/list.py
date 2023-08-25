from collections import OrderedDict

from .base import MethodGenerator


class ListMethodGenerator(MethodGenerator):

    operation: str = 'list'

    @property
    def kwargs(self) -> OrderedDict[str, str]:
        """
        Override the kwargs to exclude the pagination arguments if
        the operation can paginate.
        """
        if self.client.can_paginate(self.boto3_name):
            _args: OrderedDict[str, str] = OrderedDict()
            for _arg, arg_type in super().kwargs.items():
                if _arg not in ['nextToken', 'maxResults', 'Marker', 'MaxRecords']:
                    _args[_arg] = arg_type
        return _args

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
        return_type = f'List["{self.model_name}"]'
        if self.operation_def.return_type:
            return_type = self.operation_def.return_type
        return return_type

    @property
    def body(self) -> str:
        # This is a hard attribute to guess. Sometimes it's CamelCase, sometimes
        # it's camelCase, sometimes it's snake_case.  We'll just assume it's a
        # lowercase plural of the model name.
        response_attr = self.model_name_plural.lower()
        if self.operation_def.response_attr:
            response_attr = self.operation_def.response_attr
        if self.client.can_paginate(self.boto3_name):
            code = f"""
        paginator = self.client.get_paginator('{self.boto3_name}')
        response_iterator = paginator.paginate({self.operation_args})
        results: {self.return_type} = []
        for _response in response_iterator:
            response = {self.response_class}(**_response)
            if response.{response_attr}:
                results.extend(response.{response_attr})
            else:
                break
        return results
"""
        else:
            code = f"""
        {self.operation_call}
        return response.{response_attr}
"""
        return code
