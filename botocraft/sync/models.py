from pathlib import Path
from typing import Optional, Dict, Literal, List, Any

import yaml

from pydantic import BaseModel

DATA_DIR = Path(__file__).parent.parent / 'data'
SERVICES_DIR = Path(__file__).parent.parent / 'services'

Operation = Literal['create', 'update', 'delete', 'get', 'get_many', 'list']

# ------
# Models
# ------


class ModelAttributeDefinition(BaseModel):
    """
    The definition of a single field on a :py:class:`ModelDefinition`.
    """

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


class ModelDefinition(BaseModel):

    #: The botocore model name
    name: str
    #: The name of the base class for this model.  If not specified, we'll
    #: use the default base class for the use case.
    base_class: Optional[str] = None
    #: Our replacement model name.  We use this if some submodels have the
    #: same name as a model in another service.
    alternate_name: Optional[str] = None
    #: The primary key for this model.  This is the field that will be used
    #: to determine whether we need to create a new model instance or update
    #: an existing one.
    primary_key: Optional[str] = None
    #: The ``ARN`` key for this model attribute if any.  Some AWS models
    #: have an ARN, a name, and an ID.  Some have no ARN.
    arn_key: Optional[str] = None
    #: The ``name`` key for this model attribute if any.  Some AWS models
    #: have an ARN, a name, and an ID.
    name_key: Optional[str] = None
    #: A list of field overrides for this model.  If a field name is not
    #: specified in this list, it will be generated verbatim from the
    #: botocore model.
    fields: Dict[str, ModelAttributeDefinition] = {}
    #: A list of extra fields for this model.  These are fields that are
    #: not in the botocore model, but are either:
    #:
    #: * returned by boto3 create/update/get/list methods as part of the
    #:   response payload.
    #: * or are needed at create time because they turn into something
    #:   else in the response.  Or We need to add them to the model so that we can load the model
    #: successfully from the API response.  Typically these are fields that
    #: will be readonly because they are
    extra_fields: Dict[str, ModelAttributeDefinition] = {}
    #: If ``True``, make this model immutable.
    readonly: bool = False


# --------
# Managers
# --------

class OperationArgumentDefinition(BaseModel):

    #: If specified, in the operation call invocation, set the value
    #: of this argument to the value of the model attribute specified
    #: here.  This is only useful for operations that take a model instance
    #: as an argument.
    attribute: Optional[str] = None
    #: If specified, in the operation call invocation, set the value
    #: of this argument to the value of this method argument
    source_arg: Optional[str] = None
    #: If ``True``, force the argument to be in in the method
    #: signature.  This is only useful for operations that take a model
    #: instance as an argument.
    explicit: bool = False
    #: If ``True``, make this a postional argument.
    required: bool = False
    #: If specified, set this as the default value for the argument.
    default: Optional[Any] = None
    #: If ``True``, don't include this argument in the method signature.
    #: or in the operation call invocation.
    hidden: bool = False
    #: If specified, use this as the docstring for the argument.  Otherwise,
    #: we'll use the docstring from the botocore operation.
    docstring: Optional[str] = None
    #: If this argument is a model instance, exclude any attributes that
    #: are ``None`` from the serialized output we send to boto3.
    exclude_none: bool = False


class OperationDefinition(BaseModel):

    #: The name of the boto3 operation to call in the method body
    boto3_name: str
    #: A list of argument overrides for this operation.  If an argument name
    #: is not specified as a key in this dict, it will be generated as is
    #: appropriate for the operation type
    args: Dict[str, OperationArgumentDefinition] = {}
    #: The attribute name to use on the response object to  use to build our
    #: method return object(s).  If not specified, we'll use the lowercased
    #: model name, pluralizing if necessary.
    response_attr: Optional[str] = None
    #: If specified, use this as the docstring for the method itself (not
    #: the args, kwargs or return type).  If not specified, we'll use the
    #: docstring from the botocore operation.
    docstring: Optional[str] = None
    #: If specified, use this as the return type for the method.  If not
    #: set, we'll use the model name, pluralizing if necessary.
    return_type: Optional[str] = None

    @property
    def explicit_args(self) -> List[str]:
        """
        Return a list of positional arguments that should be explicitly
        included in the method signature.  This is useful for operations
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
        Return a list of positional arguments that should be explicitly
        included in the method signature.  This is useful for operations
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
            if arg_def.explicit and not arg_def.required:
                positional_args.append(arg_name)
        return positional_args


class ManagerDefinition(BaseModel):

    #: The name of the model this manager is for
    name: str
    #: The operations to generate on this manager
    operations: Dict[Operation, OperationDefinition] = {}
    #: If ``True``, make this manager use the :py:class:`ReadonlyBoto3ModelManager` superclass
    readonly: bool = False


# --------
# Services
# --------

class ServiceDefinition(BaseModel):
    """
    Our definition of a single AWS service, e.g. ``ecs``, ``ec2``, etc.
    """

    #: The global botocraft inteface model
    interface: 'BotocraftInterface'
    #: The name of the botocore service
    name: str
    #: The models to generate for this service.  These are specifically models
    #: that have managers.
    primary_models: Dict[str, ModelDefinition] = {}
    #: These are models that are used as attributes on other models, or as
    #response : or request classes.
    secondary_models: Dict[str, ModelDefinition] = {}
    #: The managers to generate for this service
    managers: Dict[str, ManagerDefinition] = {}

    @classmethod
    def load(cls, name: str, interface: 'BotocraftInterface') -> 'ServiceDefinition':
        """
        Load a service definition from its YAML files.

        Args:
            name: The name of the AWS service to load

        Returns:
            The loaded service definition
        """
        managers: Optional[Dict[str, ManagerDefinition]] = None
        model_path = DATA_DIR / name / 'models.yml'
        manager_path = DATA_DIR / name / 'managers.yml'
        with open(model_path, encoding='utf-8') as f:
            models = yaml.safe_load(f)
        if manager_path.exists():
            with open(manager_path, encoding='utf-8') as f:
                managers = {
                    name: ManagerDefinition(name=name, **defn)
                    for name, defn in yaml.safe_load(f).items()
                }
        return cls(
            name=name,
            primary_models={
                name: ModelDefinition(name=name, **defn)
                for name, defn in models.get('primary', {}).items()
            },
            secondary_models={
                name: ModelDefinition(name=name, **defn)
                for name, defn in models.get('secondary', {}).items()
            },
            managers=managers,
            interface=interface,
        )


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
        'Tag': 'botocraft.services.tagging',
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

    def add_model(self, name: str, service: str) -> None:
        """
        Save a model name to import path mapping.

        Args:
            name: the model name
            service: the AWS service name
        """
        if name in self.models:
            raise ValueError(f'Model {name} already defined by service "{service}"')
        self.models[name] = f'botocraft.services.{service}'

    def populate_init_py(self):
        """
        Populate the ``__init__.py`` file in the ``botocraft.models``
        package with import statements for all of our models.
        """
        init_path = SERVICES_DIR / '__init__.py'
        with open(init_path, 'w', encoding='utf-8') as f:
            for service in self.services:
                f.write(f'from .{service} import *  # noqa: F401,F403\n')

    def update_init_py(self, service: str) -> None:
        """
        Update the ``__init__.py`` file in the ``botocraft.models``
        package with import statements for the given service.

        Args:
            service: The name of the service to update the ``__init__.py``
                file for.
        """
        init_path = SERVICES_DIR / '__init__.py'
        import_line = f'from .{service} import *  # noqa: F401,F403'
        with open(init_path, 'r', encoding='utf-8') as f:
            contents = f.read()
        if import_line not in contents:
            with open(init_path, 'a', encoding='utf-8') as f:
                f.write(f'{import_line}\n')

    def generate(self, service: Optional[str] = None) -> None:
        """
        Generate all our service interfaces.

        Keyword Args:
            service: If specified, only generate the interface for the given
                service.  Otherwise, generate all interfaces.
        """
        from .service import ServiceGenerator  # pylint: disable=import-outside-toplevel
        if service:
            assert service in self.services, f'No service definition for AWS Service "{service}"'
            print(f'Generating {service} service interface')
            generator = ServiceGenerator(self.services[service])
            generator.generate()
            self.update_init_py(service)
        else:
            for service_name, _service in self.services.items():
                print(f'Generating {service_name} service interface')
                generator = ServiceGenerator(_service)
                generator.generate()
            self.populate_init_py()
