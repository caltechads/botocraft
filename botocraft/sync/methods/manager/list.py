from collections import OrderedDict
from typing import Literal, cast

from .base import ManagerMethodGenerator


class ListMethodGenerator(ManagerMethodGenerator):
    method_name: str = "list"

    def kwargs(
        self, location: Literal["method", "operation"] = "method"
    ) -> OrderedDict[str, str]:
        """
        Override the kwargs to exclude the pagination arguments if
        the boto3 operation can paginate.
        """
        if self.client.can_paginate(self.boto3_name):
            _args: OrderedDict[str, str] = OrderedDict()
            for _arg, arg_type in super().kwargs(location=location).items():
                if _arg not in self.PAGINATOR_ARGS:
                    _args[_arg] = arg_type
        return _args

    @property
    def return_type(self) -> str:
        """
        For list methods, we return a list of model instances, not the response
        model, unless it's overriden in our botocraft method config, in which
        case we return that.

        Thus we need to change the return type to a list of the model.

        Returns:
            The name of the return type class.

        """
        # We do this because :py:meth:`response_class` will create the response class
        # if it doesn't exist, and we need that to happen so we can use its attributes
        _ = self.response_class
        if self.output_shape is not None:
            response_attr_shape = self.output_shape.members[
                cast(str, self.response_attr)
            ]
        return_type = self.shape_converter.convert(response_attr_shape, quote=True)
        if self.method_def.return_type:
            return_type = self.method_def.return_type
        return return_type

    @property
    def body(self) -> str:
        # This is a hard attribute to guess. Sometimes it's CamelCase, sometimes
        # it's camelCase, sometimes it's snake_case.  We'll just assume it's a
        # lowercase plural of the model name.
        if self.client.can_paginate(self.boto3_name):
            code = f"""
        paginator = self.client.get_paginator('{self.boto3_name}')
        {self.operation_args}
        response_iterator = paginator.paginate(**{{k: v for k, v in args.items() if v is not None}})
        results: {self.return_type} = []
        for _response in response_iterator:
            response = {self.response_class}(**_response)
            if response.{self.response_attr}:
                if hasattr(response.{self.response_attr}[0], "session"):
                    for obj in response.{self.response_attr}:
                        obj.session = self.session
                        results.append(obj)
                else:
                    results.extend(response.{self.response_attr})
            else:
                break
        return results
"""  # noqa: E501
        else:
            code = f"""
        {self.operation_call}
        if response.{self.response_attr} is not None:
            if hasattr(response.{self.response_attr}[0], "session"):
                objs = []
                for obj in response.{self.response_attr}:
                    obj.session = self.session
                    objs.append(obj)
                return objs
        return response.{self.response_attr}
"""
        return code
