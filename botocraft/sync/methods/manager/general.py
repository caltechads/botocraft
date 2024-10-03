from collections import OrderedDict
from typing import Literal, cast

from .base import ManagerMethodGenerator


class GeneralMethodGenerator(ManagerMethodGenerator):
    method_name: str = "general"

    def kwargs(
        self, location: Literal["method", "operation"] = "method"
    ) -> OrderedDict[str, str]:
        """
        Just in case this ends up being used for a method that can paginate,
        we'll exclude the pagination arguments.
        """
        args = super().kwargs(location=location)
        if self.client.can_paginate(self.boto3_name):
            _args: OrderedDict[str, str] = OrderedDict()
            for _arg, arg_type in super().kwargs(location=location).items():
                if _arg not in self.PAGINATOR_ARGS:
                    _args[_arg] = arg_type
            return _args
        return args

    @property
    def return_type(self) -> str:
        """
        For generic methods:

        * If :py:attr:`ManagerMethodDefinition.return_type` is set, use that.
        * If :py:attr:`ManagerMethodDefinition.response_attr` is set, infer the
          return type from the response attribute.
        * Otherwise, return the response class name

        Returns:
            The name of the return type class.

        """
        response_class_name = self.response_class
        if self.method_def.return_type:
            return self.method_def.return_type
        if self.response_attr is None:
            return f'"{response_class_name}"'
        if self.output_shape is not None:
            response_attr_shape = self.output_shape.members[
                cast(str, self.response_attr)
            ]
        return_type = self.shape_converter.convert(response_attr_shape, quote=True)
        return return_type  # noqa: RET504

    @property
    def body(self) -> str:
        """
        Generate the method body for a general method.

        Returns:
            The method body.

        """
        if self.client.can_paginate(self.boto3_name):
            code = f"""
        paginator = self.client.get_paginator('{self.boto3_name}')
        {self.operation_args}
        response_iterator = paginator.paginate(**{{k: v for k, v in args.items() if v is not None}})
        results: {self.return_type} = []
        for _response in response_iterator:
            response = {self.response_class}(**_response)
"""  # noqa: E501
            if self.response_attr is not None:
                code += f"""
            if response.{self.response_attr}:
                if hasattr(response.{self.response_attr}, "session"):
                    objs = []
                    for obj in response.{self.response_attr}:
                        obj.session = self.session
                        objs.append(obj)
                    results.extend(objs)
                else:
                    results.extend(response.{self.response_attr})
"""
            else:
                code += """
            if response is not None:
                try:
                    # Test whether the response is iterable
                    iter(response)
                except TypeError:
                    if hasattr(response, "session"):
                        response.session = self.session
                    # If it not, append the response to the results list
                    results.append(response)  # type: ignore[arg-type]
                else:
                    # If it is, extend the results list with the response
                    if hasattr(response[0], "session"):
                        objs = []
                        for obj in response:
                            obj.session = self.session
                            objs.append(obj)
                        results.extend(objs)
                    else:
                        results.extend(response)  # type: ignore[arg-type]
"""
            code += """
            else:
                break
        return results
"""
        else:
            code = f"""
        {self.operation_args}
        {self.operation_call}
"""
            if self.return_type in ("None", '"None"'):
                pass
            elif self.response_attr is None:
                code += """
        return response
"""
            else:
                code += f"""
        return response.{self.response_attr}
"""
        return code
