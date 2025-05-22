from collections import OrderedDict
from copy import copy
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
            try:
                response_attr_shape = self.output_shape.members[
                    cast("str", self.response_attr)
                ]
            except KeyError:
                response_model_def = self.model_generator.get_model_def(
                    self.output_shape.name
                )
                for field, field_data in response_model_def.fields.items():
                    if field_data.rename == self.response_attr:
                        response_attr_shape = self.output_shape.members[
                            cast("str", field)
                        ]
                        break
                else:
                    raise
        return_type = self.shape_converter.convert(response_attr_shape, quote=True)
        if self.model_def.alternate_name:
            if f'"{self.model_name}"' in return_type:
                return_type = return_type.replace(
                    f'"{self.model_name}"', f'"{self.model_def.alternate_name}"'
                )
        return return_type

    @property
    def body(self) -> str:
        """
        Generate the method body for a general method.

        .. note::

            This is a complicated one because we have to deal with:

                1. Methods that can paginate.
                2. Methods that return a single response.
                3. Methods that can't paginate but return a list of responses.
                4. Methods that return ``None``

        Returns:
            The method body.

        """

        def generate_paginator_code() -> str:
            code: str = f"""
        paginator = self.client.get_paginator('{self.boto3_name}')
        {self.operation_args}
        response_iterator = paginator.paginate(**{{k: v for k, v in args.items() if v is not None}})
"""  # noqa: E501
            return_type = copy(self.return_type)
            if not return_type.startswith("Optional["):
                return_type = f"Optional[{return_type}]"
            code += f"""
        results: {self.return_type} = []
"""
            if self.response_attr is not None:
                code += f"""
        for _response in response_iterator:
            response = {self.response_class}(**_response)
            if response.{self.response_attr} is not None:
                results.extend(response.{self.response_attr})
            else:
                break
"""
            else:
                code += f"""
        for _response in response_iterator:
            response = {self.response_class}(**_response)
            results.append(response)
"""
            return code

        def handle_response() -> str:
            code = ""
            if self.return_type in ("None", '"None"'):
                return ""
            return_type = copy(self.return_type)
            if not return_type.startswith("Optional["):
                return_type = f"Optional[{return_type}]"
            code += f"""
        results: {self.return_type} = None
        if response is not None:"""
            if self.response_attr is not None:
                code += f"""
            results = response.{self.response_attr}
"""
            else:
                code += """
            results = response
"""
            return code

        if self.client.can_paginate(self.boto3_name):
            code = generate_paginator_code()
        else:
            code = f"""
        {self.operation_args}
        {self.operation_call}
        {handle_response()}
"""
        if self.return_type not in ("None", '"None"'):
            code += f"""
        self.sessionize(results)
        return cast({self.return_type}, results)
"""
        return code
