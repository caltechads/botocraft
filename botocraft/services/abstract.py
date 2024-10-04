import re
from typing import Any, ClassVar, Optional, Type

import boto3
from pydantic import BaseModel, ConfigDict, Field


class TransformMixin:
    def transform(
        self,
        attribute: str,
        transformer: Optional[str],
    ) -> Any:
        """
        Transform an attribute using a regular expression into something else
        before it is returned.

        .. important::
            This only makes sense for attributes that are strings.

        ``transformer`` is a regular expression that will be used to transform
        the value of the attribute.

        * If the attribute is ``None``, it will be returned verbatim.
        * If ``transformer`` is ``None``, the attribute will be returned verbatim.
        * If ``transformer`` has no named groups, the attribute will be replaced
          with the value of the first group.
        * If ``transformer`` has named groups, the attribute will be replaced
          with a dictionary of the named groups.

        Raises:
            ValueError: If the attribute does not exist on the model.
            RuntimeError: If the transformer fails to match the attribute value.

        Args:
            attribute: The attribute to transform.
            transformer: The regular expression to use to transform the attribute.

        Returns:
            The transformed attribute.

        """
        if not hasattr(self, attribute):
            msg = f"Invalid attribute: {self.__class__.__name__}.{attribute}"
            raise ValueError(msg)
        if transformer is None:
            return getattr(self, attribute)
        value = getattr(self, attribute)
        if value is None:
            return None
        if match := re.search(transformer, value):
            if match.groupdict():
                return match.groupdict()
            return match.group(1)
        msg = (
            f"Transformer failed to match: transformer=r'{transformer}', "
            f"value='{getattr(self, attribute)}'"
        )
        raise RuntimeError(msg)


class Boto3Model(TransformMixin, BaseModel):
    """
    The base class for all boto3 models.
    """

    model_config = ConfigDict(validate_assignment=True)


class ReadonlyBoto3Model(Boto3Model):
    """
    The base class for all boto3 models that are readonly.
    """

    model_config = ConfigDict(frozen=True, validate_assignment=True, extra="allow")


class Boto3ModelManager(TransformMixin):
    #: The name of the boto3 service.  Example: ``ec2``, ``s3``, etc.
    service_name: str

    def __init__(self) -> None:
        #: The boto3 client for the AWS service
        self.client = boto3.client(self.service_name)  # type: ignore[call-overload]
        #: The boto3 session to use for this manager.
        self.session = boto3.session.Session()

    def using(self, session: boto3.session.Session) -> "Boto3ModelManager":
        """
        Use a different boto3 session for this manager.

        Args:
            session: The boto3 session to use.

        """
        # TODO: this is a bad way to do this -- it means that whatever session
        # was last set with .using() will be transparently used by all other
        # calls to the manager.  This is not good.  We need som way to make
        # it like a context manager, so that the session is only used for the
        # duration of the actual method call.
        self.session = session
        self.client = session.client(self.service_name)  # type: ignore[call-overload]
        return self

    def serialize(self, arg: Any) -> Any:
        """
        Some of our botocraft methods use :py:class:`Boto3Model` objects as
        arguments (e.g. ``create``, ``update``), but boto3 methods expect simple
        Python types.  This method will serialize the model into a set of types
        that boto3 will understand if it is a :py:class:`Boto3Model` object.

        While serializing, we always exclude ``None`` values, because boto3
        doesn't like them.

        If ``arg`` is not a :py:class:`Boto3Model` object, it will be returned
        verbatim.

        Args:
            arg: the botocraft method argument to serialize.

        Returns:
            A properly serialized argument.

        """
        if arg is None:
            return None
        if isinstance(arg, Boto3Model):
            return arg.model_dump(exclude_none=True)
        if isinstance(arg, list):
            # Oop, this is a list.  We need to serialize each item in the list.
            return [self.serialize(a) for a in arg]
        return arg

    def get(self, *args, **kwargs):
        raise NotImplementedError

    def list(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, model, **kwargs):
        raise NotImplementedError

    def update(self, model, **kwargs):  # noqa: ARG002
        # Some models cannot be updated, so instead of raising a
        # NotImplementedError, we raise a RuntimeError.
        msg = "This model cannot be updated."
        raise RuntimeError(msg)

    def delete(self, pk: str, **kwargs):
        raise NotImplementedError

    def get_waiter(self, name: str) -> Any:
        """
        Get a boto3 waiter object for this service.

        Args:
            name: The name of the waiter to get.

        Returns:
            The boto3 waiter object.

        """
        return self.client.get_waiter(name)


class ReadonlyBoto3ModelManager(Boto3ModelManager):  # pylint: disable=abstract-method
    def create(self, model, **kwargs):  # noqa: ARG002
        msg = "This model cannot be created."
        raise RuntimeError(msg)

    def update(self, model, **kwargs):  # noqa: ARG002
        msg = "This model cannot be updated."
        raise RuntimeError(msg)

    def delete(self, pk: str, **kwargs):  # noqa: ARG002
        msg = "This model cannot be deleted."
        raise RuntimeError(msg)


class ModelIdentityMixin:
    @property
    def pk(self) -> Optional[str]:
        """
        Get the primary key of the model instance.

        Returns:
            The primary key of the model instance.

        """
        raise NotImplementedError

    @property
    def arn(self) -> Optional[str]:
        """
        Get the ARN of the model instance.

        Returns:
            The ARN of the model instance.

        """
        msg = "The model does not have an ARN."
        raise ValueError(msg)

    @property
    def name(self) -> Optional[str]:
        """
        Get the name of the model instance.

        Returns:
            The name of the model instance.

        """
        msg = "The model does not have a name."
        raise ValueError(msg)


def classproperty(func):
    return classmethod(property(func))


class ReadonlyPrimaryBoto3Model(  # pylint: disable=abstract-method
    ModelIdentityMixin, ReadonlyBoto3Model
):
    #: The manager for this model
    manager_class: ClassVar[Type[Boto3ModelManager]]

    #: The boto3 session to use for this model.  This is set by the manager,
    #: and is used in relationships.  We have to use ``Any`` here because we
    #: pydantic complains vociferously if we use ``boto3.session.Session``.
    #: We exclude it from the model dump because it's not something that should
    #: be serialized.
    session: Optional[Any] = Field(default=None, exclude=True)

    @classproperty
    def objects(cls) -> Boto3ModelManager:  # noqa: N805
        """
        Get the manager for this model.

        Returns:
            The manager for this model.

        """
        return cls.manager_class()

    def save(self, **kwargs):  # noqa: ARG002
        """
        Save the model.
        """
        msg = "Cannot save a readonly model."
        raise RuntimeError(msg)

    def delete(self):
        """
        Delete the model.
        """
        msg = "Cannot delete a readonly model."
        raise RuntimeError(msg)

    def set_session(self, session: boto3.session.Session) -> None:
        """
        Set the boto3 session for this model.

        Args:
            session: The boto3 session to use.

        Returns:
            The model instance.

        """
        self.model_config["frozen"] = False
        self.session = session  # type: ignore[misc]
        self.model_config["frozen"] = True


class PrimaryBoto3Model(  # pylint: disable=abstract-method
    ModelIdentityMixin, Boto3Model
):
    """
    The base class for all boto3 models that get returned as the primary object
    from a boto3 operation.
    """

    #: The manager for this model
    manager_class: ClassVar[Type[Boto3ModelManager]]

    #: The boto3 session to use for this model.  This is set by the manager,
    #: and is used in relationships.  We have to use ``Any`` here because we
    #: pydantic complains vociferously if we use ``boto3.session.Session``.
    #: We exclude it from the model dump because it's not something that should
    #: be serialized.
    session: Optional[Any] = Field(default=None, exclude=True, frozen=False)

    @classproperty
    def objects(cls) -> Boto3ModelManager:  # noqa: N805
        """
        Get the manager for this model.

        Returns:
            The manager for this model.

        """
        return cls.manager_class()

    def save(self, **kwargs):
        """
        Save the model.
        """
        if self.pk:
            return self.objects.update(self, **kwargs)
        return self.objects.create(self, **kwargs)

    def delete(self):
        """
        Delete the model.
        """
        if not self.pk:
            msg = "Cannot delete a model that has not been saved."
            raise ValueError(msg)
        return self.manager.delete(self.pk)

    def set_session(self, session: boto3.session.Session) -> None:
        """
        Set the boto3 session for this model.

        Args:
            session: The boto3 session to use.

        Returns:
            The model instance.

        """
        self.session = session