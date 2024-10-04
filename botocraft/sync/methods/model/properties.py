import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from botocraft.sync.service import ModelGenerator


class ModelPropertyGenerator:
    """
    Base class for all model method properties.  This is used to generate
    the code for a single method on a manager class.

    To use this, you subclass it and implement the :py:meth:`body`
    property, which is the body of the method.  You can also override
    any of the following properties to customize the method:

    * :py:meth:`decorator`: The method decorators.
    * :py:meth:`signature`: The method signature.
    * :py:meth:`docstring`: The method docstring.
    * :py:meth:`return_type`: The return type annotation.

    Args:
        generator: The generator that is creating the model class
        model_name: The name of the model we're generating the property for.

    """

    def __init__(
        self,
        generator: "ModelGenerator",
        model_name: str,
        property_name: str,
    ) -> None:
        #: The generator that is creating the service classes for an AWS Service.
        self.generator = generator
        #: The name of the model we're generating the property for.
        self.model_name = model_name
        #: The definition of the model we're generating the property for.
        self.model_def = self.generator.get_model_def(model_name)
        #: The name of the property we're generating.
        self.property_name = property_name
        #: The definition of the property we're generating.
        self.property_def = self.model_def.properties[self.property_name]

    @property
    def decorator(self) -> str:
        """
        The decorator for the method.  If the property definition has
        :py:attr:`botocraft.sync.models.ModelPropertyDefinition.cached`` equal
        to ``True``, this is ``@cached_property``, otherwise use ``@property``.

        Returns:
            The decorator for the method.

        """
        if self.property_def.cached:
            self.generator.imports.add("from functools import cached_property")
            return "    @cached_property"
        return "    @property"

    @property
    def return_type(self) -> str:
        """
        Return the return type annotation for the method.
        """
        if self.property_def.transformer.regex:
            return_type = "Optional[str]"
            num_groups = re.compile(self.property_def.transformer.regex.regex).groups
            if num_groups > 1:
                return_type = "Optional[Dict[str, str]]"
        elif self.property_def.transformer.mapping:
            # TODO: it'd be nice to do something like a typed dict here
            return_type = "OrderedDict[str, Any]"
            self.generator.imports.add("from collections import OrderedDict")
        elif self.property_def.transformer.alias:
            fields = self.generator.fields(self.model_name)
            assert (
                self.property_def.transformer.alias in fields
            ), f"Alias: attribute {self.property_def.transformer.alias} not found in model {self.model_name}"  # noqa: E501
            return_type = self.generator.field_type(
                self.model_name,
                self.property_def.transformer.alias,
                field_shape=fields[self.property_def.transformer.alias].botocore_shape,
            )
        return return_type

    @property
    def docstring(self) -> str:
        """
        Return the docstring for the method.
        """
        if self.property_def.docstring:
            return f'''
        """
        {self.property_def.docstring}

        """
'''
        return ""

    @property
    def signature(self) -> str:
        """
        Return the method signature.

        Returns:
            The method signature.

        """
        return f"    def {self.property_name}(self) -> {self.return_type}:"

    @property
    def _regex_body(self) -> str:
        """
        Render the body of the method for use with the regex transformer.

        Returns:
            The method body.

        """
        assert (
            self.property_def.transformer.regex
        ), f"Property {self.property_name} does not have a regex transformer"
        return f"""
        return self.transform(
            "{self.property_def.transformer.regex.attribute}",
            r"{self.property_def.transformer.regex.regex}"
        )
"""

    @property
    def _mapping_body(self) -> str:
        """
        Render the body of the method for use with the mapping transformer.

        Returns:
            The method body.

        """
        assert (
            self.property_def.transformer.mapping
        ), f"Property {self.property_name} does not have a mapping transformer"
        code = """        return OrderedDict({
"""
        for key, value in self.property_def.transformer.mapping.items():
            code += f"""
            "{key}": self.{value},
"""
        code += """
        })
"""
        return code

    @property
    def _alias_body(self) -> str:
        """
        Render the body of the method for use with the alias transformer.

        Returns:
            The method body.

        """
        assert (
            self.property_def.transformer.alias
        ), f"Property {self.property_name} does not have an alias transformer"
        return f"""
        return self.{self.property_def.transformer.alias}
"""

    @property
    def body(self) -> str:
        """
        Return the method body.

        Returns:
            The method body.

        """
        if self.property_def.transformer.regex:
            return self._regex_body
        if self.property_def.transformer.mapping:
            return self._mapping_body
        if self.property_def.transformer.alias:
            return self._alias_body
        msg = f"Property {self.property_name} does not have a transformer"
        raise RuntimeError(msg)

    @property
    def code(self) -> str:
        """
        Return the code for the method.

        Returns:
            The code for the method.

        """
        return f"""

{self.decorator}
{self.signature}
{self.docstring}
{self.body}
"""
