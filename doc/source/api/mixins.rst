.. _api_mixins:

Model and Manager extensions
============================

``botocraft`` provides a number of mixins and decorators that are used to extend
the functionality of the model and manager classes which are generated from
the ``botocore`` definitions and ``botocraft`` definitions.  These mixins and
decorators are used to:

- provide additional methods to those classes that are not provided by the AWS API
- implement those methods in a more useful way
- translate between what the AWS API provides and what we want to provide to the user.

.. note::

   The mixins and decorators are not intended to be used directly by the user.
   They are intended to be used by the botocraft code generator to generate the
   service and manager classes.


Models
------

.. autoclass:: botocraft.mixins.tags.TagsDict
   :members:
   :show-inheritance:

.. autopydantic_model:: botocraft.mixins.ecr.ImageInfo
   :members:
   :show-inheritance:
   :exclude-members: update_forward_refs, model_extra, model_fields_set, validate, schema_json, model_rebuild, model_post_init, model_parametrized_name, model_json_schema, copy, from_orm, dict, json, schema, schema_json


Decorators
----------

Application autoscaling
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: botocraft.mixins.autoscaling.scaling_policy_only

.. autofunction:: botocraft.mixins.autoscaling.scalable_target_only

.. autofunction:: botocraft.mixins.autoscaling.scheduled_action_only

EC2
~~~

.. autofunction:: botocraft.mixins.ec2.ec2_instances_only

.. autofunction:: botocraft.mixins.ec2.ec2_instance_only

ECR
~~~

.. autofunction:: botocraft.mixins.ecr.repo_list_images_ecr_images_only

.. autofunction:: botocraft.mixins.ecr.image_list_images_ecr_images_only

ECS
~~~

.. autofunction:: botocraft.mixins.ecs.ecs_services_only

.. autofunction:: botocraft.mixins.ecs.ecs_clusters_only

.. autofunction:: botocraft.mixins.ecs.ecs_task_definitions_only

.. autofunction:: botocraft.mixins.ecs.ecs_container_instances_only

.. autofunction:: botocraft.mixins.ecs.ecs_task_populate_taskDefinition

.. autofunction:: botocraft.mixins.ecs.ecs_task_populate_taskDefinitions

.. autofunction:: botocraft.mixins.ecs.ecs_tasks_only


Manager Mixins
--------------

EC2
~~~

.. autoclass:: botocraft.mixins.ec2.AMIManagerMixin
   :members:

.. autoclass:: botocraft.mixins.ec2.EC2TagsManagerMixin
   :members:


Model Mixins
------------

Any
~~~

.. autoclass:: botocraft.mixins.tags.TagsDictMixin
   :members:

Application AutoScaling
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: botocraft.mixins.autoscaling.ScalableTargetModelMixin
   :members:

AutoScaling
~~~~~~~~~~~

.. autoclass:: botocraft.mixins.autoscaling.AutoScalingGroupModelMixin
   :members:

EC2
~~~

.. autoclass:: botocraft.mixins.ec2.InstanceModelMixin
   :members:

.. autoclass:: botocraft.mixins.ec2.AMIModelMixin
   :members:

.. autoclass:: botocraft.mixins.ec2.SecurityGroupModelMixin
   :members:

ECR
~~~

.. autoclass:: botocraft.mixins.ecr.RepositoryMixin
   :members:

.. autoclass:: botocraft.mixins.ecr.ECRImageMixin
   :members:

ECS
~~~

.. autoclass:: botocraft.mixins.ecs.ECSServiceModelMixin
   :members:

.. autoclass:: botocraft.mixins.ecs.ECSContainerInstanceModelMixin
   :members:
