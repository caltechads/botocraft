from ...models import MethodDocstringDefinition
from .create import CreateMethodGenerator


class UpdateMethodGenerator(CreateMethodGenerator):
    method_name: str = "update"

    @property
    def docstrings_def(self) -> MethodDocstringDefinition:
        """
        Return the docstring for the method.
        """
        docstrings_def = super().docstrings_def
        docstrings_def.args["model"] = f"The :py:class:`{self.model_name}` to update."
        return docstrings_def
