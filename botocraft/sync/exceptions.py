from typing import TYPE_CHECKING

import botocore

if TYPE_CHECKING:
    from botocraft.sync.shapes import AbstractShapeConverter


class ModelHasNoMembersError(Exception):
    """Exception raised when a model has no members."""

    def __init__(self, model_name: str):
        super().__init__(f"Model '{model_name}' has no fields.")
        self.model_name = model_name
        self.message = f"Model '{model_name}' has no fields."


class NoPythonTypeError(Exception):
    """Exception raised when a model has no Python type."""

    def __init__(self, field_name: str, model_name: str):
        super().__init__(
            f"Field '{field_name}' on model '{model_name}' has no Python type."
        )
        self.model_name = model_name
        self.field_name = field_name
        self.message = (
            f"Field '{field_name}' on model '{model_name}' has no Python type."
        )


class WrongConverterError(Exception):
    """Exception raised when a shape converter is not the right one for a shape."""

    def __init__(
        self, shape: botocore.model.Shape, converter: "AbstractShapeConverter"
    ):
        self.shape_name = shape.name
        self.converter_name = converter.__class__.__name__
        super().__init__(
            f"Shape '{self.shape_name}' cannot be converted by {self.converter_name}."
        )
        self.message = (
            f"Shape '{self.shape_name}' cannot be converted by {self.converter_name}."
        )


class NoConverterError(Exception):
    """Exception raised when a shape converter is not found."""

    def __init__(self, shape: botocore.model.Shape):
        self.shape_name = shape.name
        self.type_name = shape.type_name
        super().__init__(
            f"No converter found for shape '{self.shape_name}' [{self.type_name}]."
        )
        self.message = (
            f"No converter found for shape '{self.shape_name}' [{self.type_name}]."
        )
