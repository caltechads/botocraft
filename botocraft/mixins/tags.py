from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union, cast

if TYPE_CHECKING:
    from botocraft.services.abstract import Boto3Model


class TagsDict(dict):
    """
    A dict subclass that allows python dictionary style access to the
    ``Tags`` attribute for a model instance.   Normally ``Tags`` is a list of
    dictionaries, but this class allows you to treat tags like a dictionary
    where the keys are the tag names and the values are the tag values.

    This subclass does the following additional things:

    * overrides the ``__setitem__`` method to set the the appropriate key
      and value in the ``Tags`` attribute of the model instance.
    * overrides the ``__delitem__`` method to delete the appropriate key
      and value in the ``Tags`` attribute of the model instance.
    * overrides the ``pop`` method to delete the appropriate key
      and value in the ``Tags`` attribute of the model instance.
    """

    def __init__(self, *args, **kwargs) -> None:
        #: The model instance that we are setting tags for.
        self.instance: Optional["Boto3Model"] = None  # noqa: UP037
        #: The boto3 tag class.  This has to be configurable because once
        #: again boto3 has different tag classes for different services.
        self.tag_class: Optional[Type] = None
        #: The name of the key attribute in the tag class.
        self.tag_Key: Optional[str] = None
        #: The name of the value attribute in the tag class.
        self.tag_Value: Optional[str] = None
        super().__init__(*args, **kwargs)

    def check(self) -> None:
        """
        Check if we have been configured properly.

        This means:

        * the ``instance`` attribute must be set.
        * ``self.instance`` must have an attribute named ``Tags``.
        * the ``tag_class`` attribute must be set.
        * the ``tag_Key`` attribute must be set.
        * the ``tag_Value`` attribute must be set.

        Returns:
            True if we have been configured, False otherwise.

        """
        assert (
            self.instance is not None
        ), "The instance attribute must be set before setting tags."
        assert hasattr(
            self.instance, "Tags"
        ), f"The {self.instance.__class__.__name__} does not have a Tags attribute."
        assert (
            self.tag_class is not None
        ), "The tag_class attribute must be set before setting tags."
        assert (
            self.tag_Key is not None
        ), "The tag_Key attribute must be set before setting tags."
        assert (
            self.tag_Value is not None
        ), "The tag_Value attribute must be set before setting tags."

    def __setitem__(self, key: str, value: str) -> None:
        """
        Set the tags in ourselves and in the ``Tags`` attribute of the model
        instance.

        Args:
            key: the key to set.
            value: the value to set.

        """
        self.check()
        found: bool = False
        instance = cast("Boto3Model", self.instance)
        if instance.Tags is None:  # type: ignore[attr-defined]
            instance.Tags = []  # type: ignore[attr-defined]
        for tag in instance.Tags:  # type: ignore[attr-defined]
            if getattr(tag, cast(str, self.tag_Key)) == key:
                setattr(tag, cast(str, self.tag_Value), value)
                found = True
                break
        if not found:
            tag = cast(Type, self.tag_class)(
                **{self.tag_Key: key, self.tag_Value: value}
            )
            instance.Tags.append(tag)  # type: ignore[attr-defined]
        super().__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        """
        Delete the tags in ourselves and in the ``Tags`` attribute of the model
        instance.

        Args:
            key: the key to delete.

        """
        self.check()
        instance = cast("Boto3Model", self.instance)
        for tag in instance.Tags:  # type: ignore[attr-defined]
            if getattr(tag, cast(str, self.tag_Key)) == key:
                instance.Tags.remove(tag)  # type: ignore[attr-defined]
                break
        super().__delitem__(key)

    def pop(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Override the ``pop`` method to delete the tags in ourselves and in the
        ``Tags`` attribute of the model instance.

        Args:
            key: the key to delete.

        Keyword Args:
            default: the default value to return if the key is not found.

        Returns:
            Returns the value of the key if it exists, otherwise the default

        """
        self.check()
        instance = cast("Boto3Model", self.instance)
        for tag in instance.Tags:  # type: ignore[attr-defined]
            if getattr(tag, cast(str, self.tag_Key)) == key:
                instance.Tags.remove(tag)  # type: ignore[attr-defined]
                break
        return super().pop(key, default)


class TagsDictMixin:
    """
    A mixin that adds a ``tags`` property to a model instance.  This
    is intended to be used with :py:class:`Boto3Model` classes that have
    a ``Tags`` attribute.

    The attribute that has the AWS tags list **must** be named ``Tags``.  If
    your model stores them in another attribute (for example, ECS objects use
    ``tags`` instead), you will need to override the attribute name by setting
    the :py:attr:`botocraft.sync.models.ModelAttributeDefinition.rename`
    attribute to be ``Tags`` for that attribute.

    .. important::
        One important assumption this mixin makes is the caller modifies tags
        via either self.tags or self.Tags, but not both at the same time.  If
        you do use both at the same time, you will get unexpected results.
    """

    #: The boto3 tag class.  This has to be configurable because once
    #: again boto3 has different tag classes for different services.
    tag_class: Optional[Type] = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.tag_class is None:
            from botocraft.services.common import Tag

            self.tag_class = Tag

    @cached_property
    def __tag_Key(self) -> str:  # noqa: N802
        """
        The name of the key attribute in the tag class.
        """
        assert (
            self.tag_class is not None
        ), "The tag_class class attribute must be set before using tags."
        instance = self.tag_class()
        candidates = ["key", "Key"]
        for candidate in candidates:
            if hasattr(instance, candidate):
                return candidate
        msg = f"Could not find a key attribute in {self.tag_class.__name__}"
        raise RuntimeError(msg)

    @cached_property
    def __tag_Value(self) -> str:  # noqa: N802
        """
        The name of the value attribute in the tag class.
        """
        assert (
            self.tag_class is not None
        ), "The tag_class class attribute must be set before using tags."
        instance = self.tag_class()
        candidates = ["value", "Value"]
        for candidate in candidates:
            if hasattr(instance, candidate):
                return candidate
        msg = f"Could not find a value attribute in {self.tag_class.__name__}"
        raise RuntimeError(msg)

    @property
    def tags(self) -> TagsDict:
        """
        Get the tags for the model instance.

        Returns:
            The tags for the model instance.

        """
        assert hasattr(
            self, "Tags"
        ), f"The {self.__class__.__name__} does not have a Tags attribute."
        if self.Tags is None:
            _tags = TagsDict()
        else:
            _tags = TagsDict(
                **{
                    getattr(tag, self.__tag_Key): getattr(tag, self.__tag_Value)
                    for tag in self.Tags
                }
            )
        _tags.instance = cast("Boto3Model", self)
        _tags.tag_class = self.tag_class
        _tags.tag_Key = self.__tag_Key
        _tags.tag_Value = self.__tag_Value
        return _tags

    @tags.setter
    def tags(self, value: Union[Dict[str, str], TagsDict]) -> None:
        """
        Set the tags for the model instance.

        Args:
            value: the tags to set for the model instance.

        """
        assert (
            self.tag_class is not None
        ), "The tag_class class attribute must be set before setting tags."
        assert hasattr(
            self, "Tags"
        ), f"The {self.__class__.__name__} does not have a Tags attribute."
        self.Tags = []
        for key, _value in value.items():
            tag = self.tag_class(**{self.__tag_Key: key, self.__tag_Value: _value})
            self.Tags.append(tag)
