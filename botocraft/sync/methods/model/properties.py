from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from botocraft.sync.service import ModelGenerator


class ModelPropertyGenerator:
    """
    The base class for all model method properties.  This is used to generate
    the code for a single method on a manager class.

    To use this, you subclass it and implement the :py:meth:`body`
    property, which is the body of the method.  You can also override
    any of the following properties to customize the method:

    * :py:meth:`decorator`: The method decorators.
    * :py:meth:`signature`: The method signature.
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
            self.generator.imports.add('from functools import cached_property')
            return '    @cached_property'
        return '    @property'

    @property
    def return_type(self) -> str:
        """
        Return the return type annotation for the method.
        """
        if self.property_def.regex:
            return_type = 'Optional[str]'
            num_groups = re.compile(self.property_def.regex.regex).groups
            if num_groups > 1:
                return_type = 'Optional[Dict[str, str]]'
        elif self.property_def.mapping:
            # FIXME: it'd be nice to do something like a typed dict here
            return_type = 'Dict[str, Any]'
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
        return ''

    @property
    def signature(self) -> str:
        """
        Return the method signature.

        Returns:
            The method signature.
        """
        return f'    def {self.property_name}(self) -> {self.return_type}:'

    @property
    def body(self) -> str:
        """
        Return the method body.

        Returns:
            The method body.
        """
        if self.property_def.regex:
            code = f"""
        return self.transform("{self.property_def.regex.attribute}", r"{self.property_def.regex.regex}")
"""
        elif self.property_def.mapping:
            code = """
        return {
"""
            for key, value in self.property_def.mapping.mapping.items():
                code += f"""
            "{key}": self.{value},
"""
            code += """
        }
"""
        elif self.property_def.alias:
            code = f"""
        return self.{self.property_def.alias.attribute}
"""
        return code

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
