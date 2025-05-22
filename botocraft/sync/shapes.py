from typing import TYPE_CHECKING, Dict, Final, Type, cast

import botocore.model

from .exceptions import (
    NoConverterError,
    WrongConverterError,
)

if TYPE_CHECKING:
    from botocraft.sync.service import ModelGenerator, ServiceGenerator


class AbstractShapeConverter:
    """
    The base class for all shape converters.
    """

    def __init__(self, shape_converter: "PythonTypeShapeConverter") -> None:
        self.service_generator = shape_converter.service_generator
        self.model_generator = shape_converter.model_generator
        self.shape_converter = shape_converter

    def model_exists(self, model_name: str) -> bool:
        """
        If we've already generated this model, return ``True``,
        else return ``False``.

        Args:
            model_name: the name of the model to check

        """
        model_def = self.model_generator.get_model_def(model_name)
        if model_def.alternate_name:
            model_name = model_def.alternate_name
        if model_name in self.model_generator.classes:
            # We generated this model earlier in this phase of service
            # generation
            return True
        if model_name in self.service_generator.classes:
            # We generated generated this model in a previous phase of service
            # generation
            return True
        if model_name in self.service_generator.service_def.models:
            # This model is belongs to this service, but we haven't generated it
            # yet.  Do so now.
            return False
        if model_name in self.service_generator.interface.models:  # noqa: SIM103
            # models we've generated so far in other services
            return True
        # This is some dependent model for this service. We'll generate it now.
        return False

    def import_line(self, model_name: str) -> str | None:
        """
        Given ``model_name``, determine whether we've already
        generated this model somewhere else in the service, and
        """
        if model_name in self.service_generator.service_def.models:
            # This model is belongs to this service, but we haven't generated it
            # yet.  We don't need an import line, because the model lives
            # in this service.
            return None
        for model in self.service_generator.service_def.models.values():
            # We've generated this model in a previous phase of service
            # generation and it has an alternate name
            if model.alternate_name == model_name:
                return None
        if model_name in self.service_generator.interface.models:
            import_path = self.service_generator.interface.models[model_name]
            return f"from {import_path} import {model_name}"
        return None

    def to_python(
        self, shape: botocore.model.Shape, quote: bool = False, name_only: bool = False
    ) -> str:
        """
        Converts the given shape ``shape`` to a python type,
        possibly using the model generator to generate
        pydantic models for nested structures.

        Args:
            shape: the botocore shape to convert

        Keyword Args:
            quote: if ``True``, we will quote the string in the
                return value.  This is used when we're generating
                manager methods, because the manager classes appear
                in the file before the models, so we need to quote
                the model names to avoid mypy errors.
            name_only: if ``True``, we will return the name of the model
                and not create the model in the model generator, if this
                is a structure shape.

        Returns:
            the python type for the shape

        """
        raise NotImplementedError


class StringShapeConverter(AbstractShapeConverter):
    def to_python(
        self,
        shape: botocore.model.Shape,
        quote: bool = False,  # noqa: ARG002
        name_only: bool = False,  # noqa: ARG002
    ) -> str:
        if shape.type_name == "string" or shape.name == "String":
            value = cast("botocore.model.StringShape", shape)
            if value.enum:
                contents = ", ".join([f"'{value}'" for value in value.enum])
                python_type = f"Literal[{contents}]"
            else:
                python_type = "str"
            return python_type
        raise WrongConverterError(shape, self)


class BooleanShapeConverter(AbstractShapeConverter):
    def to_python(
        self,
        shape: botocore.model.Shape,
        quote: bool = False,  # noqa: ARG002
        name_only: bool = False,  # noqa: ARG002
    ) -> str:
        if shape.type_name == "boolean":
            return "bool"
        raise WrongConverterError(shape, self)


class IntegerShapeConverter(AbstractShapeConverter):
    def to_python(
        self,
        shape: botocore.model.Shape,
        quote: bool = False,  # noqa: ARG002
        name_only: bool = False,  # noqa: ARG002
    ) -> str:
        if shape.type_name in ["integer", "long"]:
            return "int"
        raise WrongConverterError(shape, self)


class DoubleShapeConverter(AbstractShapeConverter):
    def to_python(
        self,
        shape: botocore.model.Shape,
        quote: bool = False,  # noqa: ARG002
        name_only: bool = False,  # noqa: ARG002
    ) -> str:
        if shape.type_name == "double":
            return "float"
        raise WrongConverterError(shape, self)


class ListShapeConverter(AbstractShapeConverter):
    def to_python(
        self,
        shape: botocore.model.Shape,
        quote: bool = False,  # noqa: ARG002
        name_only: bool = False,
    ) -> str:
        """
        Convert a list shape to a python type.  If the list members are not
        strings, we will generate a pydantic model for the list members

        Args:
            shape: the botocore shape to convert

        Keyword Args:
            quote: if ``True``, we will quote the string in the
                return value.  This is used when we're generating
                manager methods, because the manager classes appear
                in the file before the models, so we need to quote
                the model names to avoid mypy errors.
            name_only: if ``True``, we will return the name of the model
                and not create the model in the model generator, if this
                is a structure shape.

        Raises:
            WrongConverterError: this is not a list shape

        Returns:
            a python type for the list

        """
        if shape.type_name != "list":
            raise WrongConverterError(shape, self)
        element_shape = cast("botocore.model.ListShape", shape).member
        inner_model_name = self.shape_converter.convert(
            element_shape, quote=True, name_only=name_only
        )
        return f"List[{inner_model_name}]"


class MapShapeConverter(AbstractShapeConverter):
    def to_python(
        self,
        shape: botocore.model.Shape,
        quote: bool = False,  # noqa: ARG002
        name_only: bool = False,
    ) -> str:
        """
        Convert a map shape to a python type.  We're assuming that
        the map key is always a string, and the value is always a
        string -- I haven't seen any other different examples.

        Args:
            shape: the botocore shape to convert

        Keyword Args:
            quote: if ``True``, we will quote the string in the
                return value.  This is used when we're generating
                manager methods, because the manager classes appear
                in the file before the models, so we need to quote
                the model names to avoid mypy errors.
            name_only: if ``True``, we will return the name of the model
                and not create the model in the model generator, if this
                is a structure shape.

        Raises:
            WrongConverterError: this is not a map shape

        Returns:
            the python type for the map

        """
        if shape.type_name != "map":
            raise WrongConverterError(shape, self)
        shape = cast("botocore.model.MapShape", shape)
        value_type = self.shape_converter.convert(
            shape.value, quote=True, name_only=name_only
        )
        key_type = self.shape_converter.convert(
            shape.key, quote=True, name_only=name_only
        )
        return f"Dict[{key_type}, {value_type}]"


class StructureShapeConverter(AbstractShapeConverter):
    def to_python(
        self, shape: botocore.model.Shape, quote: bool = False, name_only: bool = False
    ) -> str:
        """
        Convert a structure shape to a python type.  This ends up always being a
        pydantic model.

        Side Effects:
            Might add a new pydantic class to the service python module.

        Args:
            shape: the botocore shape to convert

        Keyword Args:
            quote: if ``True``, we will quote the string in the
                return value.  This is used when we're generating
                manager methods, because the manager classes appear
                in the file before the models, so we need to quote
                the model names to avoid mypy errors.
            name_only: if ``True``, we will return the name of the model
                and not create the model in the model generator.

        Raises:
            WrongConverterError: this is not a structure shape

        Returns:
            the python type for the structure

        """
        if shape.type_name != "structure":
            raise WrongConverterError(shape, self)
        import_path: str | None = None
        shape = cast("botocore.model.StructureShape", shape)
        model_def = self.model_generator.get_model_def(shape.name)
        model_name = shape.name
        if model_def.alternate_name:
            model_name = model_def.alternate_name
        if not name_only:
            if not self.model_exists(model_name):
                # We have not yet generated this model as a pydantic class
                model_name = self.model_generator.generate_single_model(
                    shape.name, model_shape=shape
                )
            else:  # noqa: PLR5501
                # We've already generated the model, so we just need to import it
                # if it's in another service, otherwise we can just use it

                # TODO: we have a problem here that if we want to import the model
                # from another service, but the model has an alternate name, we
                # won't find it this way because ``model_name`` here will just be
                # ``shape.name``
                if import_path := self.import_line(model_name):
                    self.model_generator.imports.add(import_path)
            if quote and not import_path:
                return f'"{model_name}"'
        elif quote:
            return f'"{model_name}"'
        return model_name


class TimestampShapeConverter(AbstractShapeConverter):
    def to_python(
        self,
        shape: botocore.model.Shape,
        quote: bool = False,  # noqa: ARG002
        name_only: bool = False,  # noqa: ARG002
    ) -> str:
        """
        Convert a timestamp shape to a python type.   This
        ends up always being a ``datetime.datetime`` object.

        Side Effects:
            This adds the ``datetime`` import to the model generator.

        Args:
            shape: the botocore shape to convert

        Keyword Args:
            quote: if ``True``, we will quote the string in the
                return value.  This is used when we're generating
                manager methods, because the manager classes appear
                in the file before the models, so we need to quote
                the model names to avoid mypy errors.
            name_only: if ``True``, we will return the name of the model
                and not create the model in the model generator.

        Raises:
            WrongConverterError: this is not a timestamp shape

        Returns:
            the python type for the timestamp

        """
        if shape.type_name == "timestamp":
            return "datetime"
        self.model_generator.imports.add("from datetime import datetime")
        raise WrongConverterError(shape, self)


class BinaryShapeConverter(AbstractShapeConverter):
    def to_python(
        self,
        shape: botocore.model.Shape,
        quote: bool = False,  # noqa: ARG002
        name_only: bool = False,  # noqa: ARG002
    ) -> str:
        """
        Convert a binary shape to a python type.  This
        ends up always being a ``bytes`` object.

        Args:
            shape: the botocore shape to convert

        Keyword Args:
            quote: if ``True``, we will quote the string in the
                return value.  This is used when we're generating
                manager methods, because the manager classes appear
                in the file before the models, so we need to quote
                the model names to avoid mypy errors.
            name_only: if ``True``, we will return the name of the model
                and not create the model in the model generator.

        Raises:
            WrongConverterError: this is not a binary shape

        Returns:
            the python type for the shape

        """
        if shape.type_name == "blob":
            return "bytes"
        raise WrongConverterError(shape, self)


class PythonTypeShapeConverter:
    CONVERTERS: Final[Dict[str, Type[AbstractShapeConverter]]] = {
        "string": StringShapeConverter,
        "boolean": BooleanShapeConverter,
        "integer": IntegerShapeConverter,
        "structure": StructureShapeConverter,
        "timestamp": TimestampShapeConverter,
        "double": DoubleShapeConverter,
        "list": ListShapeConverter,
        "map": MapShapeConverter,
        "blob": BinaryShapeConverter,
    }

    def __init__(
        self, service_generator: "ServiceGenerator", model_generator: "ModelGenerator"
    ) -> None:
        #: The service generator.  We use this for accessing the
        #: model generator in case we need to build pydantic
        #: models out of a structure shape
        self.service_generator = service_generator
        self.model_generator = model_generator
        self.converters: Dict[str, AbstractShapeConverter] = {
            key: converter_class(self)
            for key, converter_class in self.CONVERTERS.items()
        }

    def convert(
        self, shape: botocore.model.Shape, quote: bool = False, name_only: bool = False
    ) -> str:
        """
        Convert a botocore shape to the appropriate python type.

        Args:
            shape: the botocore shape to convert

        Keyword Args:
            quote: if ``True``, we will quote the string in the return value.
            name_only: if ``True``, we will return the name of the model and not
                create the model in the model generator.

        Raises:
            NoConverterError: Could not find a converter for the shape

        Returns:
            The python type for the shape to be used in type hints

        """
        for converter in self.converters.values():
            try:
                return converter.to_python(shape, quote=quote, name_only=name_only)
            except WrongConverterError:  # noqa: PERF203
                pass
        raise NoConverterError(shape)
