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
        _args: OrderedDict[str, str] = OrderedDict()
        if self.client.can_paginate(self.boto3_name):
            for _arg, arg_type in super().kwargs(location=location).items():
                if _arg not in self.PAGINATOR_ARGS:
                    _args[_arg] = arg_type
        else:
            for _arg, arg_type in super().kwargs(location=location).items():
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
        if self.method_def.return_type:
            return self.method_def.return_type
        if self.output_shape is not None:
            response_attr_shape = self.output_shape.members[
                cast("str", self.response_attr)
            ]
        return_type = self.shape_converter.convert(response_attr_shape, quote=True)
        _return_type = return_type.lower()
        if _return_type.startswith("list["):
            _return_type = _return_type.replace("list[", "").replace("]", "")
        if _return_type.startswith("dict["):
            _return_type = _return_type.replace("dict[", "").replace("]", "")
            _return_type = _return_type.split(",")[1].strip()
        if _return_type in ("str", "int", "float", "bool", "None"):
            return return_type
        return "PrimaryBoto3ModelQuerySet"

    @property
    def body(self) -> str:
        # This is a hard attribute to guess. Sometimes it's CamelCase, sometimes
        # it's camelCase, sometimes it's snake_case.  We'll just assume it's a
        # lowercase plural of the model name.
        self.imports.add("from .abstract import PrimaryBoto3ModelQuerySet")
        if self.client.can_paginate(self.boto3_name):
            code = f"""
        paginator = self.client.get_paginator('{self.boto3_name}')
        {self.operation_args}
        response_iterator = paginator.paginate(**{{k: v for k, v in args.items() if v is not None}})
        results = []
        for _response in response_iterator:
            if list(_response.keys()) == ['ResponseMetadata']:
                break
            if 'ResponseMetadata' in _response:
                del _response['ResponseMetadata']
            response = {self.response_class}(**_response)
            if response.{self.response_attr}:
                results.extend(response.{self.response_attr})
            else:
                break
        self.sessionize(results)
        if results and isinstance(results[0], Boto3Model):
            return PrimaryBoto3ModelQuerySet(results)
        else:
            return results
"""  # noqa: E501
        else:
            code = f"""
        {self.operation_args}
        {self.operation_call}
        if response and response.{self.response_attr}:
            self.sessionize(response.{self.response_attr})
            return PrimaryBoto3ModelQuerySet(response.{self.response_attr})
        return PrimaryBoto3ModelQuerySet([])
"""
        return code
