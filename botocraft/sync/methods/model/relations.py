from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from botocraft.sync.service import ModelGenerator


class ModelRelationGenerator:
    """
    The base class for all model relation method properties.  This is used to
    generate the code for a single relation method on a manager class.

    To use this, you subclass it and implement the :py:meth:`body`
    property, which is the body of the method.  You can also override
    any of the following properties to customize the method:

    * :py:meth:`decorator`: The method decorators.
    * :py:meth:`signature`: The method signature.
    * :py:meth:`docstring`: The method docstring.
    * :py:meth:`return_type`: The return type annotation.

    Args:
        generator: The model generator that is creating the model class
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
        self.property_def = self.model_def.relations[self.property_name]

        model_path = self.generator.service_generator.interface.models[
            self.property_def.primary_model_name
        ]
        if not model_path.endswith(self.generator.service_generator.aws_service_name):
            # The relation is not to one of our models, so we need to import it
            manager_model_name = f"{self.property_def.primary_model_name}Manager"
            self.generator.imports.add(
                f"from {model_path} import {self.property_def.primary_model_name}, {manager_model_name}"  # noqa: E501
            )

    @property
    def returns_many(self) -> bool:
        """
        Determine whether this is a foreign key or a many-to-many relation.

        Returns:
            ``True`` if this is a many-to-many relation, ``False`` otherwise.

        """
        if self.property_def.many is not None:
            return self.property_def.many
        many = False
        fields = self.generator.fields(self.model_name)
        if self.property_def.transformer.regex or self.property_def.transformer.alias:
            if self.property_def.transformer.regex:
                field_name = self.property_def.transformer.regex.attribute
            else:
                field_name = cast(str, self.property_def.transformer.alias)
            attr_python_type = self.generator.field_type(
                self.model_name,
                field_name,
                field_shape=fields[field_name].botocore_shape,
            )
            if "List[" in attr_python_type:
                many = True
        return many

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
        related_model_name = self.property_def.primary_model_name
        if self.returns_many:
            return f'Optional[List["{related_model_name}"]]'
        return f'Optional["{related_model_name}"]'

    @property
    def docstring(self) -> str:
        """
        Return the docstring for the method.
        """
        code: str = ""
        if self.property_def.docstring:
            code = f'''
        """
        {self.property_def.docstring}
'''
        if self.property_def.cached:
            code += """

        .. note::

            The output of this property is cached on the model instance, so
            calling this multiple times will not result in multiple calls to the
            AWS API.   If you need a fresh copy of the data, you can re-get the
            model instance from the manager.
"""
        code += '        """'
        return code

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
        Return the method body for a regex transformer.
        """
        assert (
            self.property_def.transformer.regex is not None
        ), f"Regex: no regex defined for property {self.property_name} on model {self.model_name}"  # noqa: E501
        if self.returns_many:
            code = f"""
        if self.{self.property_def.transformer.regex.attribute} is None:
            return []
        pks = [
            self.transform(value, r"{self.property_def.transformer.regex.regex}")
            for value in self.{self.property_def.transformer.regex.attribute}
        ]
        return {self.property_def.primary_model_name}.objects.using(self.session).list(**pks)
"""  # noqa: E501
        else:
            code = f"""
        if self.{self.property_def.transformer.regex.attribute} is None:
            return None
        pk = self.transform(value, r"{self.property_def.transformer.regex.regex}")
        return {self.property_def.primary_model_name}.objects.using(self.session).get(**pk)
"""  # noqa: E501
        return code

    @property
    def _mapping_body(self) -> str:
        """
        Return the method body for a mapping transformer.
        """
        assert (
            self.property_def.transformer.mapping is not None
        ), f"Mapping: no mapping defined for property {self.property_name} on model {self.model_name}"  # noqa: E501
        self.generator.imports.add("from collections import OrderedDict")
        code = """
        try:
            pk = OrderedDict({
"""
        for key, value in self.property_def.transformer.mapping.items():
            _value = value
            if "self." not in _value and not value.startswith('"'):
                _value = f"self.{_value}"
            code += f"""
            "{key}": {_value},
"""
        if self.returns_many:
            code += f"""
            }})
        except AttributeError:
            return []
        return {self.property_def.primary_model_name}.objects.using(self.session).list(**pk)
"""  # noqa: E501
        else:
            code += f"""
        }})
        except AttributeError:
            return None
        return {self.property_def.primary_model_name}.objects.using(self.session).get(**pk)
"""  # noqa: E501
        return code

    @property
    def body(self) -> str:
        """
        Return the method body.

        Returns:
            The method body.

        """
        if self.property_def.transformer.regex:
            body = self._regex_body
        elif self.property_def.transformer.mapping:
            body = self._mapping_body
        return body

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
