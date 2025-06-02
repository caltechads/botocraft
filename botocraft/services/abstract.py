from functools import cached_property
import re
import inspect
from collections import OrderedDict
from datetime import datetime, time, timezone as dt_timezone
from zoneinfo import ZoneInfo
from typing import (
    Any,
    ClassVar,
    Type,
    Callable,
    Iterator,
    cast,
    Union,
    Optional,
    Dict,
    Set,
)

import boto3
from pydantic import BaseModel, ConfigDict, Field

from .exceptions import NotUpdatableError


class TransformMixin:
    def transform(
        self,
        attribute: str,
        transformer: str | None,
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

    #: The boto3 session to use for this model.  This is set by the manager,
    #: and is used in relationships.  We have to use ``Any`` here because we
    #: pydantic complains vociferously if we use ``boto3.session.Session``.
    #: We exclude it from the model dump because it's not something that should
    #: be serialized.
    session: Any | None = Field(default=None, exclude=True)

    def set_session(self, session: boto3.session.Session) -> None:
        """
        Set the boto3 session for this model.

        Args:
            session: The boto3 session to use.

        Returns:
            The model instance.

        """
        if self.model_config.get("frozen"):
            self.model_config["frozen"] = False
            self.session = session
            self.model_config["frozen"] = True
        else:
            self.session = session


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

    def using(self, session: boto3.session.Session | None) -> "Boto3ModelManager":
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
        if session is not None:
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

    def sessionize(self, response: Any) -> None:
        """
        Look through ``response`` for any object with ``set_session`` as
        an attribute and set the session on that object.

        .. note::

            I'm making an assumption here that the only PrimaryBoto3Model
            or ReadonlyPrimaryBoto3Model objects that will be in the response
            will be at the top level.  If they are nested, we'll miss the ones
            that are nested.

        Args:
            response: The response to search.
        """
        if response:
            if isinstance(response, BaseModel):
                # Pydantic models are ALWAYS iterable, so we can't use
                # iter(response) to check if it's a list.
                # We get the fields on the model, excluding our special
                # fields and then try to sessionize them.
                if isinstance(response, PrimaryBoto3Model | ReadonlyPrimaryBoto3Model):
                    response.set_session(self.session)
                    return
                attrs = [
                    attr
                    for attr in response.__fields__
                    if attr not in ["session", "objects"]
                ]
                for attr in attrs:
                    _attr = getattr(response, attr)
                    if _attr is not None:
                        self.sessionize(_attr)
            else:
                # This is NOT a pydantic model, now we test for iterability, because
                # it could be a list of pydantic models.
                try:
                    iter(response)
                except TypeError:
                    # This is not iterable, so we can't sessionize it.
                    pass
                else:
                    if not response:
                        return
                    # Test for a dict
                    if isinstance(response, dict):
                        for value in response.values():
                            self.sessionize(value)
                    # This is a list or tuple
                    elif hasattr(response[0], "set_session"):
                        [self.sessionize(obj) or obj for obj in response]  # type: ignore[func-returns-value]

    def get(self, *args, **kwargs):
        raise NotImplementedError

    def list(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, model, **kwargs):
        raise NotImplementedError

    def update(self, model, **kwargs):
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


class ReadonlyBoto3ModelManager(Boto3ModelManager):
    def create(self, model, **kwargs):
        msg = "This model cannot be created."
        raise RuntimeError(msg)

    def update(self, model, **kwargs):
        msg = "This model cannot be updated."
        raise RuntimeError(msg)

    def delete(self, pk: str, **kwargs):
        msg = "This model cannot be deleted."
        raise RuntimeError(msg)


class ModelIdentityMixin:
    @property
    def pk(self) -> str | OrderedDict | None:
        """
        Get the primary key of the model instance.

        Returns:
            The primary key of the model instance.

        """
        raise NotImplementedError

    @property
    def arn(self) -> str | None:
        """
        Get the ARN of the model instance.

        Returns:
            The ARN of the model instance.

        """
        msg = "The model does not have an ARN."
        raise ValueError(msg)

    @property
    def name(self) -> str | None:
        """
        Get the name of the model instance.

        Returns:
            The name of the model instance.

        """
        msg = "The model does not have a name."
        raise ValueError(msg)


class classproperty:  # noqa: N801
    """
    This is useful for defining properties that are not instance-specific,
    but rather class-specific.

    Example:
        .. code-block:: python

            class MyClass:
                @classproperty
                def my_property(cls):
                    return "Hello, world!"
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return self.func(owner)


class ReadonlyPrimaryBoto3Model(  # pylint: disable=abstract-method
    ModelIdentityMixin, ReadonlyBoto3Model
):
    #: The manager for this model
    manager_class: ClassVar[Type[Boto3ModelManager]]

    #: Get the manager for this model, and set it as a class property
    objects: ClassVar[classproperty] = classproperty(lambda cls: cls.manager_class())

    def save(self, **kwargs):
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


class PrimaryBoto3Model(  # pylint: disable=abstract-method
    ModelIdentityMixin, Boto3Model
):
    """
    The base class for all boto3 models that get returned as the primary object
    from a boto3 operation.
    """

    #: The manager for this model
    manager_class: ClassVar[Type[Boto3ModelManager]]

    #: Get the manager for this model, and set it as a class property
    objects: ClassVar[classproperty] = classproperty(lambda cls: cls.manager_class())

    def save(self, **kwargs):
        """
        Save the model.
        """
        if self.pk:
            if hasattr(self.objects, "update"):
                # If the model has a primary key, we assume it is already
                # created and we need to update it.
                # We also assume that the model has a manager.
                return self.objects.update(self, **kwargs)
            msg = f"Model {self.__class__.__name__} is not updatable."
            raise NotUpdatableError(msg)

        return self.objects.create(self, **kwargs)

    def delete(self):
        """
        Delete the model.
        """
        if not self.pk:
            msg = "Cannot delete a model that has not been saved."
            raise ValueError(msg)
        if isinstance(self.pk, OrderedDict):
            return self.objects.delete(**self.pk)
        return self.objects.delete(self.pk)


class PrimaryBoto3ModelQuerySet:
    def __init__(self, results: list[Boto3Model]) -> None:
        """
        Initialize the queryset with a list of results.

        Args:
            results: List of Boto3Model objects
        """
        self.results = results
        if not self.results:
            self.results = []
        self._relationship_cache: Dict[str, Dict[int, Any]] = {}

    def first(self) -> Boto3Model | None:
        """
        Get the first model in the queryset.

        Returns:
            The first Boto3Model object or None if the queryset is empty
        """
        if self.results:
            return self.results[0]
        return None

    def __len__(self) -> int:
        """
        Get the number of models in the queryset.

        Returns:
            The count of Boto3Model objects in the queryset
        """
        return len(self.results)

    def __bool__(self) -> bool:
        """
        Check if the queryset contains any models.

        Returns:
            True if there are models in the queryset, False otherwise
        """
        return bool(self.results)

    def count(self) -> int:
        """
        Get the count of models in the queryset.

        Returns:
            The count of Boto3Model objects in the queryset
        """
        return len(self.results)

    def exists(self) -> bool:
        """
        Check if the queryset contains any models.

        Returns:
            True if there are models in the queryset, False otherwise
        """
        return bool(self.results)

    def order_by(self, field_spec: str) -> "PrimaryBoto3ModelQuerySet":
        """
        Order the queryset by the specified field.

        Args:
            field_spec: Field to order by, can include '__' for nested fields.
                        Prefix with '-' for descending order.

        Returns:
            The ordered queryset
        """
        if not self.results:
            return self

        reverse = False
        if field_spec.startswith("-"):
            reverse = True
            field_spec = field_spec[1:]

        # Use the same field accessor as the filter to get nested fields
        def get_field_value(model):
            filter_obj = Boto3ModelManagerFilter(
                [model], dummy=True, relationship_cache=self._relationship_cache
            )
            try:
                value = filter_obj._get_field_value(model, field_spec)  # noqa: SLF001
            except AttributeError:
                # If the field doesn't exist, return (False, None) so it sorts first
                return (False, None)
            # Handle lists by taking the first value if present
            if isinstance(value, list):
                if value:
                    return (True, value[0])
                # If the list is empty, return (False, None) so it sorts first
                return (False, None)
            if isinstance(value, dict):
                # If it's a dict, we can sort by the first key's value
                keys = list(value.keys())
                if keys:
                    return (True, value[keys[0]])
                # If the dict is empty, return (False, None) so it sorts first
                return (False, None)
            # Return None for missing values so they sort at the beginning
            return (True, value) if value is not None else (False, value)

        self.results = sorted(self.results, key=get_field_value, reverse=reverse)
        return self

    def filter(self, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        """
        Filter the model using the manager's filter method.

        Args:
            **kwargs: The filter criteria.

        Returns:
            A filter object that can be used to filter the model.

        """
        if not self.results:
            msg = "No results to filter"
            raise ValueError(msg)

        # Create a new relationship cache for this filter operation
        self._relationship_cache = {}
        filter_obj = Boto3ModelManagerFilter(
            self.results, relationship_cache=self._relationship_cache, **kwargs
        )
        self.results = filter_obj()
        return self

    def values(self, *fields) -> list[dict]:
        """
        Return a list of dictionaries containing the specified fields.

        Similar to Django's values() method, but returns a list directly instead of a queryset.
        Each dictionary contains the requested fields as keys with their values.

        Args:
            *fields: The field names to include in the output dictionaries.
                     If no fields are specified, all fields will be included.

        Returns:
            A list of dictionaries with the requested fields.
        """
        if not self.results:
            return []

        result_list = []
        for obj in self.results:
            if not fields:
                # If no fields specified, convert the entire object to a dict
                result_list.append(
                    obj.model_dump() if hasattr(obj, "model_dump") else vars(obj)
                )
            else:
                # Extract only the specified fields
                result = {}
                filter_obj = Boto3ModelManagerFilter(
                    [obj], dummy=True, relationship_cache=self._relationship_cache
                )
                for field in fields:
                    try:
                        result[field] = filter_obj._get_field_value(obj, field)  # noqa: SLF001
                    except (AttributeError, KeyError):  # noqa: PERF203
                        result[field] = None
                result_list.append(result)

        return result_list

    def values_list(self, *fields, flat=False) -> list:
        """
        Return a list of tuples containing the values for the specified fields.

        Similar to Django's values_list() method, but returns a list directly instead of a queryset.
        Each tuple contains the values for the requested fields.

        Args:
            *fields: The field names to include in the output tuples.
                     At least one field must be specified.
            flat: If True and only one field is specified, return flat values
                  instead of tuples. Default is False.

        Returns:
            A list of tuples (or flat values if flat=True) with the requested field values.

        Raises:
            ValueError: If flat=True is used with multiple fields or if no fields are specified.
        """
        if not fields:
            msg = "values_list() requires at least one field name"
            raise ValueError(msg)

        if flat and len(fields) > 1:
            msg = "flat=True is only valid when values_list() is called with a single field"
            raise ValueError(msg)

        if not self.results:
            return []

        result_list = []
        for obj in self.results:
            filter_obj = Boto3ModelManagerFilter(
                [obj], dummy=True, relationship_cache=self._relationship_cache
            )
            if flat:
                # Return single values for flat=True
                try:
                    result_list.append(filter_obj._get_field_value(obj, fields[0]))  # noqa: SLF001
                except (AttributeError, KeyError):
                    result_list.append(None)
            else:
                # Return tuples of values
                result = []
                for field in fields:
                    try:
                        result.append(filter_obj._get_field_value(obj, field))  # noqa: SLF001
                    except (AttributeError, KeyError):  # noqa: PERF203
                        result.append(None)
                result_list.append(tuple(result))

        return result_list

    def __iter__(self) -> Iterator[Boto3Model]:
        """
        Enable iteration over the filtered results.

        Returns:
            Iterator over filtered models or values if values()/values_list() was called
        """
        return iter(self.results)

    def all(self) -> list[Boto3Model]:
        """
        Return all models in the queryset.

        Returns:
            A list of Boto3Model objects in the queryset
        """
        return self.results

    def __getitem__(self, index) -> Union["PrimaryBoto3ModelQuerySet", Boto3Model]:
        """
        Enable indexed access to the filtered results.

        Args:
            index: Index or slice to retrieve

        Raises:
            IndexError: If the index is out of range.

        Returns:
            Either a new queryset if a slice is used, or a single model instance
            if a single index is used.
        """
        new_results = self.results[index]
        if not isinstance(new_results, list):
            return new_results
        return self.__class__(new_results)


class Boto3ModelManagerFilter:
    """
    A filter class for Boto3Model objects that provides Django-like filtering capabilities.

    This class allows you to filter a list of :py:class:`Boto3Model` objects
    using familiar Django ORM-style keyword arguments. It supports basic field
    lookups as well as more complex lookups using the ``field__lookup`` syntax.

    Examples:
        # Filter instances where name equals "my-instance"
        filtered = Boto3ModelManagerFilter(instances, name="my-instance")

        # Filter instances where name contains "web" (case-insensitive)
        filtered = Boto3ModelManagerFilter(instances, name__icontains="web")

        # Filter instances where status is "running" AND type is "t2.micro"
        filtered = Boto3ModelManagerFilter(instances, status="running", type="t2.micro")

        # Filter on nested attributes
        filtered = Boto3ModelManagerFilter(instances, tags__Name="web-server")

        # Filter on deeply nested attributes
        filtered = Boto3ModelManagerFilter(instances, network_interfaces__private_ip_address="10.0.0.1")

        # Filter on list field values (automatically searches all items in the list)
        filtered = Boto3ModelManagerFilter(instances, security_groups__group_name="web-sg")

        # Filter on dictionary keys
        filtered = Boto3ModelManagerFilter(instances, metadata__has_key="region")

        # Filter on date/time components
        filtered = Boto3ModelManagerFilter(instances, created_at__date="2023-01-01")
        filtered = Boto3ModelManagerFilter(instances, created_at__year=2023)
        filtered = Boto3ModelManagerFilter(instances, created_at__quarter=2)  # Q2

        # Filter using regular expressions
        filtered = Boto3ModelManagerFilter(instances, name__regex=r"web-[0-9]+")
        filtered = Boto3ModelManagerFilter(instances, name__iregex=r"WEB-[0-9]+")  # Case-insensitive

    Args:
        models: List of Boto3Model objects to filter

    Keyword Args:
        **filters: Django-style keyword arguments for filtering, e.g. name="value", status__exact="running"
    """

    @staticmethod
    def _ensure_utc_datetime(dt_value: Any) -> datetime | None:
        """Convert a value to UTC datetime if it's a datetime with tzinfo."""
        if not isinstance(dt_value, datetime):
            return None

        # Create a copy to avoid modifying the original
        dt_copy = dt_value

        # If it has a timezone, convert to UTC
        if dt_copy.tzinfo is not None:
            return dt_copy.astimezone(ZoneInfo("UTC"))

        # No timezone info, assume it's UTC
        return dt_copy.replace(tzinfo=ZoneInfo("UTC"))

    #: Map of supported lookups to their filter functions
    LOOKUPS: ClassVar[dict[str, Callable[[Any, Any], bool]]] = {
        # String lookups
        "exact": lambda field_val, filter_val: field_val == filter_val,
        "iexact": lambda field_val, filter_val: str(field_val).lower()
        == str(filter_val).lower(),
        "contains": lambda field_val, filter_val: str(filter_val) in str(field_val),
        "icontains": lambda field_val, filter_val: str(filter_val).lower()
        in str(field_val).lower(),
        "startswith": lambda field_val, filter_val: str(field_val).startswith(
            str(filter_val)
        ),
        "istartswith": lambda field_val, filter_val: str(field_val)
        .lower()
        .startswith(str(filter_val).lower()),
        "endswith": lambda field_val, filter_val: str(field_val).endswith(
            str(filter_val)
        ),
        "iendswith": lambda field_val, filter_val: str(field_val)
        .lower()
        .endswith(str(filter_val).lower()),
        # Regular expression lookups
        "regex": lambda field_val, filter_val: re.search(filter_val, str(field_val))
        is not None,
        "iregex": lambda field_val, filter_val: re.search(
            filter_val, str(field_val), re.IGNORECASE
        )
        is not None,
        # Collection lookups
        "in": lambda field_val, filter_val: field_val in filter_val,
        # Comparison lookups
        "gt": lambda field_val, filter_val: field_val > filter_val,
        "gte": lambda field_val, filter_val: field_val >= filter_val,
        "lt": lambda field_val, filter_val: field_val < filter_val,
        "lte": lambda field_val, filter_val: field_val <= filter_val,
        # Null lookups
        "isnull": lambda field_val, filter_val: (field_val is None) == filter_val,
        # Dictionary lookups
        "has_key": lambda field_val, filter_val: isinstance(field_val, dict)
        and filter_val in field_val,
        # Date/time lookups
        "date": lambda field_val, filter_val: (
            isinstance(field_val, datetime)
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).date()  # type: ignore[union-attr]
            == filter_val
        ),
        "year": lambda field_val, filter_val: (
            isinstance(field_val, datetime)
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).year  # type: ignore[union-attr]
            == filter_val
        ),
        "iso_year": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).isocalendar()[0]  # type: ignore[union-attr]
            == filter_val
        ),
        "month": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).month  # type: ignore[union-attr]
            == filter_val
        ),
        "day": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).day  # type: ignore[union-attr]
            == filter_val
        ),
        "week": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).isocalendar()[1]  # type: ignore[union-attr]
            == filter_val
        ),
        "week_day": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and (Boto3ModelManagerFilter._ensure_utc_datetime(field_val).weekday() + 1)  # type: ignore[union-attr]
            == filter_val
        ),
        "iso_week_day": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).isocalendar()[2]  # type: ignore[union-attr]
            == filter_val
        ),
        "quarter": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and (
                (Boto3ModelManagerFilter._ensure_utc_datetime(field_val).month - 1) // 3  # type: ignore[union-attr]
                + 1
            )
            == filter_val
        ),
        "time": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).time()  # type: ignore[union-attr]
            == filter_val
        ),
        "hour": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).hour  # type: ignore[union-attr]
            == filter_val
        ),
        "minute": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).minute  # type: ignore[union-attr]
            == filter_val
        ),
        "second": lambda field_val, filter_val: (
            Boto3ModelManagerFilter._ensure_utc_datetime(field_val) is not None
            and Boto3ModelManagerFilter._ensure_utc_datetime(field_val).second  # type: ignore[union-attr]
            == filter_val
        ),
    }

    def __init__(
        self,
        models: list[Boto3Model],
        relationship_cache: dict[str, dict[int, Any]] | None = None,
        **filters: Any,
    ) -> None:
        """
        Initialize a filter with a list of models and filter criteria.

        Args:
            models: List of Boto3Model objects to filter
            relationship_cache: Optional shared cache for relationship objects
            **filters: Django-style keyword arguments for filtering
        """
        self.models = models
        self.filters = filters
        self._result: list[Boto3Model] | None = None
        self._relationship_cache = relationship_cache or {}
        # Flag to indicate we're just using this instance for field access
        self.dummy = filters.pop("dummy", False)

    def _is_property_method(self, obj: Any, attr_name: str) -> bool:
        """
        Check if the attribute is a property or cached_property method.

        Args:
            obj: The object to check
            attr_name: The attribute name to check

        Returns:
            True if it's a property or cached_property, False otherwise
        """
        if not hasattr(obj.__class__, attr_name):
            return False

        attr = getattr(obj.__class__, attr_name)
        return isinstance(attr, (property, cached_property))

    def _get_property_value(self, obj: Any, attr_name: str) -> Any:
        """
        Get the value of a property method, with caching for the current filter operation.

        Args:
            obj: The object containing the property
            attr_name: The name of the property

        Returns:
            The value of the property
        """
        # Create a cache key based on object id and property name
        cache_key = f"{obj.__class__.__name__}.{attr_name}"
        obj_id = id(obj)

        # Check if we've already cached this property value
        if (
            cache_key in self._relationship_cache
            and obj_id in self._relationship_cache[cache_key]
        ):
            return self._relationship_cache[cache_key][obj_id]

        # If not cached, get the property value
        value = getattr(obj, attr_name)

        # Cache the result
        if cache_key not in self._relationship_cache:
            self._relationship_cache[cache_key] = {}
        self._relationship_cache[cache_key][obj_id] = value

        return value

    def _get_field_value(self, model: Boto3Model, field_name: str) -> Any:  # noqa: PLR0911, PLR0912, PLR0915
        """
        Get a field value from a model, supporting nested attribute access.
        This method handles complex nested structures including lists, dictionaries,
        and relationship properties.

        Args:
            model: The Boto3Model instance
            field_name: The field name, can include various access patterns:
                        - Simple attribute: "name"
                        - Nested attribute: "tags__Name"
                        - Relationship traversal: "cluster__name"
                        - When accessing lists, all items will be searched automatically

        Returns:
            The field value or list of values when traversing through lists

        Raises:
            AttributeError: If the field doesn't exist on the model
        """
        parts = field_name.split("__")
        value = model

        for i, part in enumerate(parts):
            if value is None:
                return None

            # Handle relationship properties
            if i == 0 and self._is_property_method(value, part):
                # Get the relationship property value with caching
                related_obj = self._get_property_value(value, part)

                # If this is the last part, return the related object(s)
                if i == len(parts) - 1:
                    return related_obj

                # If there are more parts, continue traversing
                if related_obj is None:
                    return None

                # Handle both single objects and lists of related objects
                if isinstance(related_obj, list):
                    # Recursively process each related object with the remaining path
                    remaining_path = "__".join(parts[i + 1 :])
                    results = []
                    for item in related_obj:
                        if item is not None:
                            try:
                                result = self._get_field_value(item, remaining_path)
                                if result is not None:
                                    if isinstance(result, list):
                                        results.extend(result)
                                    else:
                                        results.append(result)
                            except (AttributeError, KeyError, TypeError, IndexError):
                                pass
                    return results or None
                # Continue with the next part using the related object
                value = related_obj
                continue

            # Special case for handling dictionary access with nested paths
            if i == 0 and hasattr(value, part) and len(parts) > 1:
                # Get the top-level attribute
                attr_value = getattr(value, part)
                if isinstance(attr_value, dict):
                    # If it's a dictionary, handle the nested parts
                    nested_parts = parts[1:]
                    nested_value = attr_value
                    for nested_part in nested_parts:
                        if nested_value is None or not isinstance(nested_value, dict):
                            return None
                        nested_value = cast(
                            "dict[str, Any]", nested_value.get(nested_part)
                        )
                    return nested_value

            # Handle lists - automatically traverse all items
            if isinstance(value, (list, tuple)) and value:
                # Get the remaining path to check
                remaining_path = "__".join([part] + parts[i + 1 :])

                # If this is the last part and all items have this attribute
                if i == len(parts) - 1 and all(
                    hasattr(item, part) for item in value if item is not None
                ):
                    return [getattr(item, part) for item in value if item is not None]

                # Get values from all items in the list that have this path
                results = []
                for item in value:
                    if item is not None:
                        try:
                            result = self._get_field_value(item, remaining_path)
                            if result is not None:
                                if isinstance(result, list):
                                    results.extend(result)
                                else:
                                    results.append(result)
                        except (AttributeError, KeyError, TypeError, IndexError):
                            # Skip items that don't have this attribute
                            pass
                return results or None

            # Handle dictionary access
            if isinstance(value, dict):
                value = value.get(part)
            # Handle model attribute access
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                # Try dictionary-style access for dynamic fields
                try:
                    if hasattr(value, "__getitem__"):
                        value = value[part]
                    else:
                        msg = f"Cannot access {part} on {type(value).__name__}"
                        raise AttributeError(msg)
                except (KeyError, TypeError, IndexError) as e:
                    msg = f"Cannot access {part} on {type(value).__name__}"
                    raise AttributeError(msg) from e

        return value

    def _apply_filter(
        self, model: Boto3Model, field_spec: str, filter_value: Any
    ) -> bool:
        """
        Apply a single filter to a model.

        Args:
            model: The Boto3Model instance
            field_spec: The field specifier (field_name or field_name__lookup)
            filter_value: The value to filter against

        Returns:
            True if the model passes the filter, False otherwise
        """
        # Parse the field specifier into field name and lookup type
        parts = field_spec.split("__")
        field_name = "__".join(parts[0:-1])

        # Default lookup is exact match
        lookup = "exact"
        if len(parts) > 1 and parts[-1] in self.LOOKUPS:
            lookup = parts[-1]
        else:
            # The part after __ might be part of the field path, not a lookup
            field_name = field_spec

        try:
            field_value = self._get_field_value(model, field_name)

            # Handle list values - if any item in the list matches, return True
            if isinstance(field_value, list):
                return any(
                    self.LOOKUPS[lookup](val, filter_value)
                    for val in field_value
                    if val is not None
                )

            # Apply the appropriate lookup filter
            return self.LOOKUPS[lookup](field_value, filter_value)
        except (AttributeError, TypeError):
            # If the field doesn't exist or can't be compared, it doesn't match
            return False

    def all(self) -> list[Boto3Model]:
        """
        Return all models without any filtering.

        Returns:
            List of all Boto3Model objects, after applying any
            :py:class:`Boto3ModelManagerFilter` operations.
        """
        return self()

    def __call__(self) -> list[Boto3Model]:
        """
        Apply all filters and return the filtered list of models.

        Returns:
            List of Boto3Model objects that pass all filters
        """
        if self._result is not None:
            return self._result

        result: list[Boto3Model] = []
        for model in self.models:
            # A model must pass all filters to be included
            if all(
                self._apply_filter(model, field, value)
                for field, value in self.filters.items()
            ):
                result.append(model)  # noqa: PERF401

        self._result = result
        return result

    def __iter__(self) -> Iterator[Boto3Model]:
        """
        Enable iteration over the filtered results.

        Returns:
            Iterator over filtered models
        """
        return iter(self())

    def __len__(self) -> int:
        """
        Get the number of models that passed the filter.

        Returns:
            Number of filtered models
        """
        return len(self())

    def __getitem__(self, index) -> Boto3Model | list[Boto3Model]:
        """
        Enable indexed access to the filtered results.

        Args:
            index: Index or slice to retrieve

        Returns:
            The model at the given index or a slice of models
        """
        return self()[index]

    def __bool__(self) -> bool:
        """
        Check if any models passed the filter.

        Returns:
            True if any models passed the filter, False otherwise
        """
        return bool(self())
