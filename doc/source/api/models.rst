.. _api__models:


Models
======

These models are used to parse and validate the YAML files in our data directory
and generate the service and manager classes that are used by the botocraft
library.

.. important::

   These models are not intended to be used directly in your code.  They are
   intended to be used by the botocraft code generator to generate the service
   and manager classes.

Utility models
--------------

These models may be used as types for the fields in other models on this page.

.. autopydantic_model:: botocraft.sync.models.Importable
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autoclass:: botocraft.sync.models.MethodDocstringDefinition
   :members:
   :show-inheritance:
   :inherited-members:


Service related models
----------------------

A service represents an AWS service, like ``ec2``, ``ecs``, ``s3``, etc.

.. autopydantic_model:: botocraft.sync.models.ServiceDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

Manager related models
----------------------

A manager is a class that provides CRUDL functionality for a service resource,
as well as any additional methods that are needed to interact with the resource.

Only resources that have at least some of the CRUDL functionality are given a
manager.  For example, the :py:class:`botocraft.service.ecs.Service` resource
has a manager, but the :py:class:`botocraft.service.ecs.LoadBalancerConfiguration` class,
which is used to compose the :py:class:`botocraft.service.ecs.Service` resource,
does not.

.. hint::

   :py:class:`botocraft.service.ecs.ServiceManager` is a manager for the
   :py:class:`botocraft.service.ecs.Service` resource in the ``ecs`` service.

.. autopydantic_model:: botocraft.sync.models.ManagerDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.ManagerMethodDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.MethodArgumentDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

Model related models
--------------------

A Model is either a resource that can be managed in the AWS API, or a model that
is necessary to compose a resource (like a tag, or a sub-structure of a
resource).

Primary models
   Primary models are the models that represent the resources that can be
   managed in the AWS API.

Secondary models
   Secondary models are the models that are necessary to compose a primary
   model, but are not themselves resources that can be managed in the AWS API.
   Secondary models may also be the Request/Response models for an AWS API
   operation.

.. hint::

   :py:class:`botocraft.service.ecs.Service` is a primary model for the
   ``AWS::ECS::Service`` resource in the ``ecs`` service, and
   :py:class:`botocraft.service.ecs.LoadBalancerConfiguration` is a secondary
   model used to compose the :py:class:`botocraft.service.ecs.Service` resource.


.. autopydantic_model:: botocraft.sync.models.ModelDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.ModelAttributeDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.ModelPropertyDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.ModelRelationshipDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.ModelManagerMethodDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.ModelManagerMethodArgDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.ModelManagerMethodKwargDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


.. autopydantic_model:: botocraft.sync.models.AttributeTransformerDefinition
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json

.. autopydantic_model:: botocraft.sync.models.RegexTransformer
   :show-inheritance:
   :inherited-members:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json
