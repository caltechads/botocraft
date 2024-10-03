import re
from typing import cast

from .base import ManagerMethodGenerator


class PartialUpdateMethodGenerator(ManagerMethodGenerator):
    """
    Handle the generation of a partial_update method.

    This is a special case of the update method, where we only update a subset
    of the model attributes.   In this case, we don't pass in a model instance,
    but just a pk and the attributes to update.  This allows us to do simple
    updates like ``scale`` without having to fetch the model first.
    """

    method_name: str = "partial_update"

    @property
    def body(self) -> str:
        response_attr = None
        if self.response_attr is not None:
            response_attr = cast(str, self.response_attr)
            if self.response_attr_multiplicity == "many":
                response_attr = f"{response_attr}[0]"
        code = f"""
        {self.operation_args}
        {self.operation_call}
"""
        if response_attr is not None:
            code += f"""
        if hasattr(response.{response_attr}, "session"):
            response.{response_attr}.session = self.session
        return cast({self.return_type}, response.{response_attr})
"""
        return code

    @property
    def return_type(self) -> str:
        """
        We want to return a single model instance, not a list of them, so we
        override the return type here.

        Returns:
            The name of the return type class.

        """
        return_type = super().return_type
        # Sometimes the return type is a list of the model, e.g.
        # ``elbv2:create_load_balancer``, so we need to strip the ``List`` part of the
        # return type, because we want to return just the model, if possible.
        if return_type.startswith("List["):
            return_type = re.sub(r"List\[(.*)\]", r"\1", return_type)
        return return_type
