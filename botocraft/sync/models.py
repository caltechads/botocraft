import re
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from textwrap import indent
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from botocraft.sync.docstring import DocumentationFormatter

DATA_DIR = Path(__file__).parent.parent / "data"
SERVICES_DIR = Path(__file__).parent.parent / "services"
DOCS_DIR = Path(__file__).parent.parent.parent / "doc" / "source"


# ------
# Models
# ------


class Importable(BaseModel):
    """
    A configuration object for a mixin class to add to a model.
    """

    #: The name of the mixin class
    name: str
    #: The botocraft import path
    import_path: str


class RegexTransformer(BaseModel):
    """
    Used when generating a property on a model that is a regular expression
    transformation of an attribute on the model.

    If the regular expression has named groups, we'll return a dictionary
    of the named groups.  Otherwise, we'll return the value of the first
    group.
    """

    #: The name of the attribute on our model to use as
    #: the input to the regular expression.
    attribute: str
    #: Use this regular expression to transform the attribute value.
    regex: str

    @field_validator("regex")
    @classmethod
    def check_valid_regexp(
        cls,
        v: Optional[str],
        info: ValidationInfo,
    ) -> Optional[str]:
        """
        Validate that the transformer is a valid regular expression.

        Args:
            v: the value of field
            info: pydantic field validation info

        Raises:
            ValueError: if the transformer is not a valid regular expression

        Returns:
            The value of the field

        """
        if v is not None:
            try:
                re.compile(v)
            except re.error as exc:
                msg = f"{info.field_name} must be a valid regular expression"
                raise ValueError(msg) from exc
        return v


class AttributeTransformerDefinition(BaseModel):
    #: If specified, use this regular expression to build the
    #: property output
    regex: Optional[RegexTransformer] = None
    #: If specified, use this mapping of attribute values to
    #: output keys to generate the output
    mapping: Optional[Dict[str, str]] = None
    #: If specified, use this property as an alias for this
    #: attribute.  This may be an alias on another related
    #: model
    alias: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def check_transformer(cls, data: Any) -> Any:
        """
        Validate that only one of a regex, a mapping or an alias is specified,
        but not more than one.

        Args:
            data: the input data for this model

        Raises:
            ValueError: both a regex and a mapping are specified

        Returns:
            The input data for this model

        """
        transformers = [data.get("regex"), data.get("mapping"), data.get("alias")]
        if transformers.count(None) < 2:  # noqa: PLR2004
            msg = "Only one of regex, mapping or alias can be specified"
            raise ValueError(msg)
        if transformers.count(None) == 3:  # noqa: PLR2004
            msg = "One of regex, mapping, or alias must be specified"
            raise ValueError(msg)
        return data


class ModelPropertyDefinition(BaseModel):
    """
    The definition of a single property on a :py:class:`ModelDefinition`.

    One of ``regex``, ``mapping`` or ``alias`` must be specified.

    If :py:attr:`cached` is ``True``, we'll cache the value of this property
    using :py:func:`functools.cached_property`.
    """

    #: The docstring for this property
    docstring: Optional[str] = None
    #: If ``True``, make this property be cached
    cached: bool = False
    #: If specified, use this definition to build the property
    #: output from the model fields
    transformer: AttributeTransformerDefinition


class ModelRelationshipDefinition(BaseModel):
    """
    Defines a property on a model that is a relationship to another model.
    """

    #: The docstring for this property
    docstring: Optional[str] = None
    #: If ``True``, make this property be cached
    cached: bool = True
    #: If specified, use this definition to build the primary key
    #: for the related model from data from this model
    #:
    #: .. important::
    #:
    #:     If you are using a regex transformer, you must use named groups.
    #:
    #:     Example::
    #:         r'arn:aws:ecs:(?P<region>[^:]+):(?P<account_id>[^:]+):(?P<resource_type>[^:]+)/(?P<resource_id>[^:]+)'  # noqa: E501
    transformer: AttributeTransformerDefinition
    #: The name of the botocraft primary model to use for this relationship
    #:
    #: .. important::
    #:
    #:     This needs to be the name of a primary model, not a secondary model.
    #:     Only primary models have managers.
    primary_model_name: str
    #: If ``True``, force this to be a many-to-many relationship.  Otherwise,
    #: try to figure it out from our transformer.
    many: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def check_regex_transformer(cls, data: Any) -> Any:
        """
        If we have a regex transformer, make sure that it only uses
        named groups.

        Args:
            data: the input data for this model

        Raises:
            ValueError: if the regex transformer has no named groups
                or has unnamed groups

        Returns:
            The input data for this model

        """
        transformer = data["transformer"]
        regex_transformer = transformer.get("regex")
        if regex_transformer is not None:
            pattern = regex_transformer["regex"]
            regex = re.compile(rf"{pattern}")
            if not regex.groupindex:
                msg = "Regex transformer must have named groups"
                raise ValueError(msg)
            if len(regex.groupindex.keys()) != regex.groups:
                msg = "Regex transformer must have no unnamed groups"
                raise ValueError(msg)
        return data

    @model_validator(mode="before")
    @classmethod
    def check_alias_transformer(cls, data: Any) -> Any:
        """
        Don't allow alias transformers for relations -- we need to know
        the argument name for the related model, and alias types don't
        support that.

        Args:
            data: the input data for this model

        Raises:
            ValueError: an alias transformer is specified

        Returns:
            The input data for this model

        """
        if data["transformer"].get("alias") is not None:
            msg = (
                "Alias transformers are not supported for relations. Use a regex "
                "or mapping transformer instead."
            )
            raise ValueError(msg)
        return data


class ModelManagerMethodArgDefinition(BaseModel):
    #: The name of the argument
    name: str
    #: The value of the argument.  If ``None``, we'll use the value of the
    #: attribute on the model with the same name.
    value: Optional[str] = None
    #: The type of the argument
    attr_type: Optional[str] = None


class ModelManagerMethodKwargDefinition(BaseModel):
    #: The name of the argument
    name: str
    #: The value of the argument.  if ``None``, we'll use the value of the
    #: attribute on the model with the same name.
    value: Optional[str] = None
    #: The type of the argument
    attr_type: Optional[str] = None
    #: The default value for the argument
    default: Optional[Any] = None


class ModelManagerMethodDefinition(BaseModel):
    """
    Used to provide methods on a model that call methods on the manager for the
    model.
    """

    # The name of the method on the manager
    manager_method: str
    #: If ``True``, make this result from this cached
    cached: bool = False
    #: The docstring for the method
    docstring: Optional[str] = None
    #: The arguments for the method.  These should refer to attributes : on the
    #: model and map them to args on the manager method in the proper : order.
    #: The key is the position of the argument in the manager method signature,
    #: value is the name of the attribute on the model.
    args: Dict[int, ModelManagerMethodArgDefinition] = Field(default_factory=dict)
    #: Args the users must supply.  The key is the position of the argument in
    #: the manager method signature, and the value is the name of the argument
    #: to add to the model method signature.
    user_args: Dict[int, ModelManagerMethodArgDefinition] = Field(default_factory=dict)
    #: The keyword arguments for the method.  These should refer to attributes
    #: on the model and map them to kwargs on the manager method with the proper
    #: keyword.
    keyword_args: List[ModelManagerMethodKwargDefinition] = Field(default_factory=list)
    #: Keyword arguments the users can supply
    user_keyword_args: List[ModelManagerMethodKwargDefinition] = Field(
        default_factory=list
    )
    #: A list of decorators to wrap the method in
    decorators: List[Importable] = Field(default_factory=list)


class ModelAttributeDefinition(BaseModel):
    """
    The definition of a single attribute on a :py:class:`ModelDefinition`.

    We use this to override the default configuration of a model attribute
    that we generate from the botocore model.
    """

    #: If specified, use this as the name of the field in the model.
    #: Set the original name of the field as a pydantic field alias.
    rename: Optional[str] = None
    #: If ``True``, make this field immutable.
    readonly: bool = False
    #: If ``True``, force the field to be required, even if the underlying
    #: botocore field is not required.
    required: bool = False
    #: If specified, set this as the default value for the field.
    default: Optional[Any] = None
    #: If specified, use this as the docstring for the field.
    docstring: Optional[str] = None
    #: If specified, use this as the python type for the field.
    python_type: Optional[str] = None
    #: If specified, the list of imports to add to the top of the
    #: to support the python type.
    imports: List[str] = []
    #: This is not defined in the YAML file, but is set by
    #: :py:meth:`ModelGenerator.fields` during generation.
    botocore_shape: Optional[Any] = None


class ModelDefinition(BaseModel):
    """
    The definition of a single model for a :py:class:`ServiceDefinition`.
    """

    #: The botocore model name
    name: str
    #: A list of mixin classes to add to the model
    mixins: List[Importable] = []
    #: If ``True``, make this model immutable.
    readonly: bool = False
    #: The plural form of our model name, if different from
    #: what the inflect library would generate.
    plural: Optional[str] = None
    #: The name of the base class for this model.  If not specified, we'll
    #: use the default base class for the use case.
    base_class: Optional[str] = None
    #: If defined, use this as the model name instead of what botocore supplies.
    #: We use this if some submodels have a ame conflict with a model in
    #: another service or an attribute on a model in this service.
    alternate_name: Optional[str] = None
    #: The primary key for this model.  This is the field that will be used
    #: to determine whether we need to create a new model instance or update
    #: an existing one.  This can be the name of a property.
    primary_key: Optional[str] = None
    #: The ``ARN`` key for this model attribute if any.  Some AWS models
    #: have an ARN, a name, and an ID.  Some have no ARN.
    arn_key: Optional[str] = None
    #: The ``name`` key for this model attribute if any.  Some AWS models
    #: have an ARN, a name, and an ID.  Some have no name.
    name_key: Optional[str] = None
    #: A list of field overrides for this model.  If a field name is not
    #: specified in this list, it will be generated verbatim from the
    #: botocore model attribute definition.
    fields: Dict[str, ModelAttributeDefinition] = {}
    #: A list of extra fields for this model.  These are fields that are
    #: not in the botocore model, but are either are needed at create time
    #: or because they turn into something else in the response.  This is
    #: pretty rarely used.
    extra_fields: Dict[str, ModelAttributeDefinition] = {}
    #: The name of the output shape for the get method for this model.  We use
    #: this to add to the model any fields that appear in the get method
    #: response, but which are not present in the create method response.
    output_shape: Optional[str] = None
    #: The names of the request shapes for the writable methods for this model.
    #: We use these to determine which fields on the model are writable.
    input_shapes: Optional[List[str]] = None
    #: Computed properties.  These are all defined by us in the botocraft
    #: config.
    properties: Dict[str, ModelPropertyDefinition] = {}
    #: Relationships to other models.  These are all defined by us in the
    #: botocraft config.
    relations: Dict[str, ModelRelationshipDefinition] = {}
    #: Methods on the model that call methods on the manager for the model.
    manager_methods: Dict[str, ModelManagerMethodDefinition] = {}

    def unalias_field_name(self, field_name: str) -> str:
        """
        Get the botocore field name for a field name that may be an alias.

        Args:
            field_name: the field name or alias to look up

        Raises:
            KeyError: no such field name or alias

        Returns:
            The botocore field name

        """
        if field_name in self.fields:
            return field_name
        for botocore_name, field_def in self.fields.items():
            if field_def.rename == field_name:
                return botocore_name
        msg = f'{self.name}: No field or alias named "{field_name}"'
        raise KeyError(msg)


# --------
# Managers
# --------


class MethodArgumentDefinition(BaseModel):
    """
    The definition of a single argument on a :py:class:`ManagerMethodDefinition`.

    Example:

        .. code-block:: yaml
            :emphasize-lines: 6,7

            Repository:
                methods:
                    create:
                        boto3_name: create_repository
                        args:
                            repositoryName:
                                required: true

    """

    #: If specified, when constructing the boto3 call invocation, set the value
    #: of this argument to the value of the model attribute specified
    #: here.  This is only useful for methods that take a model instance
    #: as an argument.
    attribute: Optional[str] = None
    #: If specified, in the method signature, use this as the argument
    #: name.  Otherwise, we'll use the name of the boto3 argument.
    rename: Optional[str] = None
    #: If specified, when constructing the boto3 call invocation, set the value
    #: of this argument to the value of this method argument
    source_arg: Optional[str] = None
    #: If specified, in the boto3 call invocation, set the value
    #: of this argument to this specifically.  If this is set, we hide
    #: the argument from the method signature.
    value: Optional[Any] = None
    #: If ``True``, take value as the raw value to pass to the boto3 call
    #: instead of wrapping it in self.serialize()
    raw_value: bool = False
    #: If ``True``, force the argument to be in in the method
    #: signature.  This is only useful for methods that take a model
    #: instance as an argument.
    explicit: bool = False
    #: If ``True``, make this a postional argument.
    required: bool = False
    #: If specified, set this as the default value for the argument.
    default: Optional[Any] = None
    #: If ``True``, don't include this argument in the method signature.
    #: or in the boto3 call invocation.
    hidden: bool = False
    #: If specified, use this as the docstring for the argument.  Otherwise,
    #: we'll use the docstring from the botocore operation.
    docstring: Optional[str] = None
    #: If supplied, use this as the python type for the argument.
    python_type: Optional[str] = None


class ManagerMethodDefinition(BaseModel):
    """
    The definition of a single method on a :py:class:`ManagerDefinition`.

    Example:

        .. code-block:: yaml
            :emphasize-lines: 3,4,5,6,7

            Repository:
                methods:
                    create:
                        boto3_name: create_repository
                        args:
                            repositoryName:
                                required: true

    """

    #: The name of the boto3 operation to call in the method body
    boto3_name: str
    #: A list of argument overrides for this method.  If an argument name
    #: is not specified as a key in this dict, it will be generated as is
    #: appropriate for the operation type
    args: Dict[str, MethodArgumentDefinition] = {}
    #: The attribute name on the response class to use in building our
    #: method return object(s).  If not specified, we'll use the lowercased
    #: model name, pluralizing if necessary.
    #:
    #: If you want to just return the whole response from the boto3 call,
    #: set this to literal ``"None"``.
    #:
    #: .. important::
    #:     If you've renamed the model attribute you want to use on the response class
    #:     using :py:attr:`ModelAttributeDefinition.rename`, put the name of
    #:     the botocore here, not the value of the ``rename`` attribute.
    response_attr: Optional[str] = None
    #: If specified, use this as the docstring for the method itself (not
    #: the args, kwargs or return type).  If not specified, we'll use the
    #: docstring from the botocore operation.
    docstring: Optional[str] = None
    #: If specified, use this as the return type for the method.  If not
    #: set, we'll use the model name, pluralizing if necessary.
    return_type: Optional[str] = None
    #: Extra arguments for the method call
    extra_args: Dict[str, MethodArgumentDefinition] = {}
    #: Decorators to wrap the method in
    decorators: List[Importable] = []

    @property
    def explicit_args(self) -> List[str]:
        """
        Return a list of positional arguments that should be explicitly
        included in the method signature.  This is useful for methods
        that take a model instance as an argument, but some of the
        arguments are not model attributes.

        Returns:
            A list of explicit positional arguments

        """
        if not self.args:
            return []
        positional_args = []
        for arg_name, arg_def in self.args.items():
            if arg_def.hidden:
                continue
            if arg_def.explicit and arg_def.required:
                positional_args.append(arg_name)
        return positional_args

    @property
    def explicit_kwargs(self) -> List[str]:
        """
        Return a list of keyword arguments that should be explicitly
        included in the method signature.  This is useful for methods
        that take a model instance as an argument, but some of the
        arguments are not model attributes.

        Returns:
            A list of explicit keyword arguments

        """
        if not self.args:
            return []
        positional_args = []
        for arg_name, arg_def in self.args.items():
            if arg_def.hidden:
                continue
            if arg_def.explicit and not arg_def.required:
                positional_args.append(arg_name)
        return positional_args


@dataclass
class MethodDocstringDefinition:
    """
    A class to hold the different parts of the docstring for a method, and
    render them into a single sphinx-napoleon style docstring.
    """

    #: The main method docstring.  This is the description of the method.
    method: Optional[str] = None
    #: The docstrings for our positional arguments
    args: OrderedDict[str, Optional[str]] = field(default_factory=OrderedDict)
    #: The docstrings for our keyword arguments
    kwargs: OrderedDict[str, Optional[str]] = field(default_factory=OrderedDict)
    #: The docstring for our return value
    return_value: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        """
        Return ``True`` if the docstring is empty, ``False`` otherwise.
        """
        return (
            self.method is None
            and not self.args
            and not self.kwargs
            and self.return_value is None
        )

    def Args(self, formatter: DocumentationFormatter) -> str:  # noqa: N802
        """
        Return the docstring for the positional arguments.
        """
        assert self.args, "No kwargs"
        docstring = """
        Args:
"""
        for arg_name, arg_docstring in self.args.items():
            docstring += formatter.format_argument(arg_name, arg_docstring)
            docstring += "\n"

        return docstring

    def Keyword_Args(self, formatter: DocumentationFormatter) -> str:  # noqa: N802
        """
        Return the docstring for the keyword arguments.
        """
        assert self.kwargs, "No args"
        docstring = """
        Keyword Args:
"""
        for arg_name, arg_docstring in self.kwargs.items():
            docstring += formatter.format_argument(arg_name, arg_docstring)
            docstring += "\n"
        return docstring

    def render(self, formatter: DocumentationFormatter) -> Optional[str]:
        """
        Return the entire method docstring.
        """
        if self.is_empty:
            return None

        docstring = '''
        """
'''
        if self.method:
            method_str = formatter.clean(self.method, max_lines=1).strip()
            docstring += indent(method_str, "        ")
            docstring += "\n"
        if self.args:
            docstring += self.Args(formatter)
        if self.kwargs:
            docstring += self.Keyword_Args(formatter)
        docstring += '\n        """'
        return docstring


class ManagerDefinition(BaseModel):
    """
    The definition of a single manager on a :py:class:`ServiceDefinition`.

    Example:
        .. code-block:: yaml

            Repository:
                methods:
                    create:
                        boto3_name: create_repository
                        args:
                            repositoryName:
                                required: true
                    delete:
                        boto3_name: delete_repository
                        args:
                            repositoryName:
                                required: true
                            force:
                                default: false

    """

    #: The name of the model this manager is for
    name: str
    #: The methods to generate on this manager
    methods: Dict[str, ManagerMethodDefinition] = {}
    #: If ``True``, make this manager use the :py:class:`ReadonlyBoto3ModelManager`
    #: superclass
    readonly: bool = False
    #: Mixin classes to add to the manager
    mixins: List[Importable] = []


# --------
# Services
# --------


class ServiceDefinition(BaseModel):
    """
    Our definition of a single AWS service, e.g. ``ecs``, ``ec2``, etc.
    """

    #: The global botocraft interface model
    interface: "BotocraftInterface"
    #: The name of the botocore service
    name: str
    #: The models to generate for this service.  These are specifically models
    #: that have managers.
    primary_models: Dict[str, ModelDefinition] = {}
    #: These are models that are used as attributes on other models, or as
    #: response or request classes.  These models don't have managers, but
    #: we sometimes define them to override the default botocore model
    #: configuration, making them readonly or to rename them, for instance.
    secondary_models: Dict[str, ModelDefinition] = {}
    #: The managers to generate for this service
    managers: Dict[str, ManagerDefinition] = {}

    @property
    def models(self) -> Dict[str, ModelDefinition]:
        """
        Return all of the models we've specifically named in the definition for
        this service, both primary and secondary.

        .. important::

            This does not include models that we generate on the fly, like
            dependent models for primary models, or models for the request and
            response classes for methods on managers.
        """
        return {**self.primary_models, **self.secondary_models}

    @classmethod
    def load(cls, name: str, interface: "BotocraftInterface") -> "ServiceDefinition":
        """
        Load a service definition from its YAML files.

        Args:
            name: The name of the AWS service to load
            interface: The global botocraft interface model

        Returns:
            The loaded service definition

        """
        managers: Optional[Dict[str, ManagerDefinition]] = None
        model_path = DATA_DIR / name / "models.yml"
        manager_path = DATA_DIR / name / "managers.yml"
        with model_path.open(encoding="utf-8") as f:
            models = yaml.safe_load(f)
        if manager_path.exists():
            with manager_path.open(encoding="utf-8") as f:
                managers = {
                    name: ManagerDefinition(name=name, **defn)
                    for name, defn in yaml.safe_load(f).items()
                }
        return cls(
            name=name,
            primary_models={
                name: ModelDefinition(name=name, **defn)
                for name, defn in models.get("primary", {}).items()
            },
            secondary_models={
                name: ModelDefinition(name=name, **defn)
                for name, defn in models.get("secondary", {}).items()
            },
            managers=managers,
            interface=interface,
        )

    def resolve_model_name(self, model_name: str) -> str:
        """
        Resolve a model name to its botocore shape name.  We need to
        do this because we can define :py:attr:`ModelDefinition.alternate_name`
        to change the botocraft name for a model.

        Args:
            model_name: The botocraft model name

        Raises:
            KeyError: If the model name is not defined in this service

        Returns:
            The botocore shape name

        """
        known_models = {**self.primary_models, **self.secondary_models}
        if model_name in known_models:
            return model_name
        for name, model in known_models.items():
            if model.alternate_name == model_name:
                return name
        msg = f'Unknown model name "{model_name}"'
        raise KeyError(msg)


# ------
# Global
# ------


class BotocraftInterface(BaseModel):
    #: The services to generate
    services: Dict[str, ServiceDefinition] = {}
    #: The model name to import path mappings
    models: Dict[str, str] = {
        # Tag is defined in so many services that we manually
        # defined it in the botocraft.models.tagging module and
        # define it here so it doesn't get generated.
        "Tag": "botocraft.services.common",
        "Filter": "botocraft.services.common",
    }

    def load(self) -> None:
        """
        Load all known service definitions from their YAML files.

        Returns:
            The loaded interface.

        """
        for path in DATA_DIR.iterdir():
            service = path.name
            if path.is_dir():
                self.services[service] = ServiceDefinition.load(service, interface=self)
                for model in self.services[service].primary_models:
                    # Register the model name to import path mapping so that we can
                    # have them available when we're building our inter-model
                    # relationships.
                    self.models[model] = f"botocraft.services.{service}"
                for manager in self.services[service].managers:
                    # Register the manager name to import path mapping so that we can
                    # have them available when we're building our inter-model
                    # relationships.
                    self.models[manager] = f"botocraft.services.{service}"

    def add_model(self, name: str, service: str) -> None:
        """
        Save a model name to import path mapping.

        Args:
            name: the model name
            service: the AWS service name

        """
        if name in self.models:
            if (
                name in self.services[service].primary_models
                and self.models[name] == f"botocraft.services.{service}"
            ):
                # We already registered this model during :py:meth:`load`
                return
            msg = f'Model {name} already defined in "{self.models[name]}"'
            raise ValueError(msg)
        self.models[name] = f"botocraft.services.{service}"

    def populate_init_py(self):
        """
        Populate the ``__init__.py`` file in the ``botocraft.models``
        package with import statements for all of our models.
        """
        init_path = SERVICES_DIR / "__init__.py"
        with init_path.open("w", encoding="utf-8") as f:
            for service in self.services:
                f.write(f"from .{service} import *  # noqa: F401,F403\n")

    def populate_services_toc(self):
        """
        Populate the ``_services_index.rst`` file in the ``doc/source``
        folder with the ``.. toctree::`` directive for all of our services.
        """
        index_path = DOCS_DIR / "_services_index.rst"
        code = """
.. toctree::
   :caption: AWS Services
   :hidden:

"""
        for service in sorted(self.services.keys()):
            code += f"   api/services/{service}\n"
        with index_path.open("w", encoding="utf-8") as f:
            f.write(code)

    def populate_services_list(self):
        """
        Populate the ``_services_list.rst`` file in the ``doc/source``
        folder with links to all of our services.
        """
        index_path = DOCS_DIR / "overview" / "_services_list.rst"
        code = ""
        for service in sorted(self.services.keys()):
            code += f"- :doc:`/api/services/{service}`\n"
        with index_path.open("w", encoding="utf-8") as f:
            f.write(code)

    def update_init_py(self, service: str) -> None:
        """
        Update the ``__init__.py`` file in the ``botocraft.models``
        package with import statements for the given service.

        Args:
            service: The name of the service to update the ``__init__.py``
                file for.

        """
        init_path = SERVICES_DIR / "__init__.py"
        import_line = f"from .{service} import *  # noqa: F401,F403"
        with init_path.open(encoding="utf-8") as f:
            contents = f.read()
        if import_line not in contents:
            with init_path.open("a", encoding="utf-8") as f:
                f.write(f"{import_line}\n")

    def purge_docs(self) -> None:
        """
        Purge all the previously generated documentation.
        """
        path = DOCS_DIR / "api" / "services"
        for service in self.services:
            service_path = path / f"{service}.rst"
            if service_path.exists():
                service_path.unlink()
        path = DOCS_DIR / "_services_index.rst"
        if path.exists():
            path.unlink()
        path = DOCS_DIR / "overview" / "_services_list.rst"
        if path.exists():
            path.unlink()

    def generate(self, service: Optional[str] = None) -> None:
        """
        Generate all our service interfaces.

        Keyword Args:
            service: If specified, only generate the interface for the given
                service.  Otherwise, generate all interfaces.

        """
        from .service import ServiceGenerator

        # First purge all the previously generated documentation
        self.purge_docs()
        if service:
            assert (
                service in self.services
            ), f'No service definition for AWS Service "{service}"'
            print(f"Generating {service} service interface")
            generator = ServiceGenerator(self.services[service])
            generator.generate()
            self.update_init_py(service)
        else:
            for service_name, _service in self.services.items():
                print(f"Generating {service_name} service interface")
                generator = ServiceGenerator(_service)
                generator.generate()
            self.populate_init_py()
            self.populate_services_toc()
            self.populate_services_list()
