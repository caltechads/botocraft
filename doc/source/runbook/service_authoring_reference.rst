.. _runbook__service_authoring_reference:

Service authoring reference
===========================

This page is the detailed reference companion to
:doc:`authoring`.  It explains how ``botocraft/data`` is converted into
generated Python code and when to reach for the various configuration features.


Generation pipeline
-------------------

The high-level flow is:

.. code-block:: text

    botocraft/data/<service>/models.yml + managers.yml
        -> BotocraftInterface.load()
        -> ServiceDefinition / ModelDefinition / ManagerDefinition
        -> ServiceGenerator.generate()
            -> ModelGenerator
            -> ManagerGenerator
            -> ServiceSphinxDocBuilder
        -> botocraft/services/<safe_service_name>.py
        -> botocraft/services/__init__.py
        -> doc/source/api/services/<safe_service_name>.rst
        -> doc/source/_services_index.rst
        -> doc/source/overview/_services_list.rst

Important pieces:

* ``botocraft.sync.models.BotocraftInterface.load()`` loads all services and
  builds the global model import map.
* ``botocraft.sync.service.ServiceGenerator`` orchestrates model generation,
  manager generation, formatting, and doc generation.
* ``botocraft.sync.service.ModelGenerator`` merges botocore shapes with YAML
  overrides.
* ``botocraft.sync.service.ManagerGenerator`` builds manager methods from
  ``managers.yml``.
* ``botocraft.sync.shapes.PythonTypeShapeConverter`` decides nested Python
  types, quoted forward references, and cross-service imports.
* ``botocraft.sync.sphinx.ServiceSphinxDocBuilder`` writes the generated
  service API page.

.. important::

   Generated files in ``botocraft/services`` and
   ``doc/source/api/services`` are outputs.  Change the YAML, the sync code, or
   handwritten helpers, then regenerate.


Canonical file layout
---------------------

Use this layout for every authored service:

.. code-block:: text

    botocraft/data/<service_name>/
        models.yml
        managers.yml

``botocraft.sync`` loads ``.yml`` files, not ``.yaml`` files.

.. warning::

   ``botocraft botocore bootstrap <service_name>`` currently creates
   ``models.yaml`` and ``managers.yaml``.  Rename those files to ``.yml`` before
   syncing.


``models.yml`` reference
------------------------

The top-level structure is:

.. code-block:: yaml

    primary:
      PrimaryModelName:
        ...
    secondary:
      SecondaryModelName:
        ...

Primary models
~~~~~~~~~~~~~~

Primary models are the resource-level objects that have managers.  They are the
main models users work with.

Common fields you will use:

* ``primary_key``: object identity
* ``arn_key``: ARN field when present
* ``name_key``: user-facing name field when present
* ``input_shapes``: request shapes that determine which model fields are
  writable
* ``output_shape``: response shape that contributes extra returned fields
* ``fields``: targeted field overrides
* ``properties``: computed values derived from model fields
* ``relations``: object-level links to other primary models
* ``manager_methods``: convenience instance methods that call manager methods
* ``mixins``: handwritten model behavior

Secondary models
~~~~~~~~~~~~~~~~

Secondary models are helper structures used inside primary models, request
models, response models, or nested structures.

You do not need to define every secondary model explicitly.  Define one when
you need to:

* rename it with ``alternate_name``
* force generation with ``force_create: true``
* override field types or docstrings
* add properties or mixins
* prevent name collisions

Important model options
~~~~~~~~~~~~~~~~~~~~~~~

``alternate_name``
   Rename the generated Python class while keeping the original botocore shape
   name in YAML.  Use this when different services would otherwise generate the
   same class name, or when a class name collides with a field/type name in a
   problematic way.

   Existing examples:

   * ``s3.Object -> S3Object``
   * ``ecs.Tag -> ECSTag``
   * ``s3.Owner -> S3Owner``

``input_shapes``
   The most important first-pass authoring knob for writable models.  The sync
   code uses these shapes to infer which fields should stay writable and which
   should become readonly in generated models.

``output_shape``
   Use this when the response returned by a ``get`` or ``list`` style method
   contains useful fields that do not live on the core model shape itself.

``fields``
   Targeted overrides for fields already present on the model shape.  Useful
   keys include ``rename``, ``python_type``, ``required``, ``default``,
   ``docstring``, and ``readonly``.

``extra_fields``
   Extra fields not present on the base botocore shape.  These are common in
   bespoke models and occasionally needed when a more natural object model needs
   data assembled from multiple AWS calls.

``readonly``
   Usually an exception, not the starting point.  Prefer to define
   ``input_shapes`` and let the generator infer writability.  Use explicit
   ``readonly`` only when you need to override that inference or describe
   intentionally immutable behavior.

``bespoke``
   Mark models that do not map cleanly to a single botocore structure.  Their
   fields come from ``extra_fields`` and handwritten manager logic instead of a
   straightforward shape conversion.

``force_create``
   Force generation of a secondary model even when it would not otherwise be
   emitted during dependency-driven generation.


Field authoring
~~~~~~~~~~~~~~~

Use field overrides when a generated field is almost correct but needs a small
fix.

Typical cases:

* rename botocore ``tags`` to ``Tags`` for ``TagsDictMixin`` compatibility
* supply a narrower ``python_type``
* mark a value as explicitly required
* add a better docstring than botocore provides
* work around a shape whose default conversion is not expressive enough

Example patterns from existing services:

.. code-block:: yaml

    fields:
      tags:
        rename: Tags

    fields:
      RuntimePlatform:
        python_type: "Literal['x86_64', 'ARM64']"

Use ``imports`` when the custom type annotation needs extra imports in the
generated module.


When to use bespoke models
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``bespoke: true`` when the resource is real from a user perspective but AWS
does not expose one clean botocore structure that corresponds to that resource.

Good examples:

* ``s3.Bucket``
* ``sqs.Queue``

Bespoke models usually need:

* ``extra_fields`` for the assembled object state
* a manager mixin to gather that state from several AWS API calls
* sometimes model mixins for convenience behavior

If the AWS API already has a clean primary shape and the mismatch is only small,
prefer a normal shape-backed model plus overrides instead of going bespoke.


``managers.yml`` reference
--------------------------

Top-level structure:

.. code-block:: yaml

    PrimaryModelName:
      readonly: false
      mixins:
        - name: SomeManagerMixin
          import_path: botocraft.mixins.some_service
      methods:
        get:
          boto3_name: describe_thing
          ...

Manager-level options
~~~~~~~~~~~~~~~~~~~~~

``readonly``
   Use ``ReadonlyBoto3ModelManager`` as the base class.

``mixins``
   Add handwritten manager behavior when generated methods are not enough.

Method-level options
~~~~~~~~~~~~~~~~~~~~

``boto3_name``
   The boto3 client method to call.

``response_attr``
   Which member of the AWS response should become the method return value.

   .. important::

      Use the botocore response member name here, not the Python field alias
      from ``rename``.

``args``
   Argument overrides for existing boto3 arguments.

``extra_args``
   Extra method arguments exposed by ``botocraft`` even when they do not map
   directly to the boto3 signature.

``return_type``
   Override the generated return type when inference is not correct or not
   expressive enough.

``decorators``
   Wrap generated methods with handwritten post-processing or safety logic.


When plain generated managers are enough
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stay with generated methods when:

* boto3 method names map clearly to the resource
* the input shape is regular
* the response needs little or no reshaping
* the resource can be modeled with straightforward CRUDL-style methods

Reach for handwritten helpers only when generation would otherwise produce an
awkward or incomplete API.


Mixins and decorators
---------------------

Put handwritten helpers in ``botocraft/mixins/<service>.py``.

Model mixins
~~~~~~~~~~~~

Use a model mixin when the behavior belongs on the object and needs real Python
code.

Examples:

* ``ECSServiceModelMixin`` adds convenience properties like required CPU and
  memory, plus richer object navigation.
* ``TaskDefinitionModelMixin`` adds derived information such as family/revision.
* ``QueueModelMixin`` and ``MessageModelMixin`` support bespoke SQS behavior.

Manager mixins
~~~~~~~~~~~~~~

Use a manager mixin when a manager method needs several AWS API calls, more
stateful control, or logic that is too irregular for YAML-generated wrappers.

Examples:

* ``BucketManagerMixin`` assembles an S3 bucket from several AWS calls.
* ``ECSServiceManagerMixin`` adds account-wide service traversal helpers.
* ``TaskDefinitionManagerMixin`` adds higher-level queries that are not plain
  boto3 wrappers.

Decorators
~~~~~~~~~~

Use a method decorator when the generated method body should stay mostly
generated, but the result needs a small transformation.

Common uses:

* convert lists of identifiers into real model objects
* patch missing response data into a friendlier object
* handle an AWS exception as an expected empty result
* batch operations around an AWS per-call limit

Examples:

* ``ecs_services_only``
* ``ecs_task_definition_include_tags``
* ``bucket_update_safe_get_lifecycle``
* ``object_list_add_bucket_name_and_tags``

Where to wire them
~~~~~~~~~~~~~~~~~~

* Model mixins go in ``models.yml`` under ``mixins`` for a model.
* Manager mixins go in ``managers.yml`` under ``mixins`` for a manager.
* Method decorators go in ``managers.yml`` under a method's ``decorators``.


Properties, relations, and manager shortcut methods
---------------------------------------------------

Use these three tools differently:

Properties
~~~~~~~~~~

Use a property when the value is derived from data already on the model.

Transformers available through YAML:

* ``mapping``
* ``regex``
* ``alias``
* ``code``

Properties are good for:

* derived names
* parsed ARN components
* simple object-level conveniences

Relations
~~~~~~~~~

Use a relation when a model field or derived value should resolve to another
primary model object.

Use relations when:

* you have raw identifier data such as an ARN, name, or compound key
* the related thing is naturally another resource object
* the target is a primary model with a manager

Prefer a raw field or simple property instead when:

* users still need the exact identifier directly
* there is no stable manager lookup path
* resolving the relation would be surprising or excessively expensive

Relationship authoring rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``primary_model_name``
   Must name a primary model, not a secondary model.

``transformer``
   Prefer ``mapping`` when you can construct lookup kwargs directly from fields
   or expressions.

   ``regex`` transformers are validated at the model-definition layer, but the
   current relation code generation path is not reliable enough to recommend as
   normal maintainer workflow.  Treat regex-backed relations as experimental
   until the relation generator is fixed; in current practice, prefer
   ``mapping``-based relations and plain properties for parsed string data.

``many``
   Set ``many: true`` when the relation returns a collection.

``method``
   Override the manager method if ``get`` or ``list`` is not the right lookup.

``cached``
   Disable caching when the relation is dynamic, expensive, or likely to change
   frequently during a process lifetime.

Limitations:

* alias transformers are not supported for relations
* regex transformers must use named groups only
* regex-backed relations are currently not a dependable authoring path; prefer
  ``mapping`` for working maintainership today
* the target must be lookuppable through a primary model manager

Relationship examples to study
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``ecs.Service.cluster``
* ``ecs.Service.task_definition``
* ``ecs.Service.tasks``
* ``ecs.ContainerDefinition.image_object``

These examples cover:

* simple single-object lookups
* many-valued relations
* cross-service relations
* mapping-based construction of lookup kwargs
* expression-based kwargs in mapping transformers

Manager shortcut methods
~~~~~~~~~~~~~~~~~~~~~~~~

Use ``manager_methods`` when the behavior is conceptually "call the manager for
this instance", but the instance should expose a more ergonomic object method.

Examples:

* ``s3.Bucket.get_policy``
* ``s3.Bucket.put_policy``
* ``sqs.Queue.receive``

Use manager shortcut methods when:

* the operation is naturally scoped to the current instance
* the instance already has the key data needed to call the manager
* you want users to think in object terms instead of manager terms


Naming, imports, and collision handling
---------------------------------------

Cross-service name collisions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``BotocraftInterface`` registers model names globally while loading services and
again while generating classes.  If two services produce the same public class
name, generation fails.

Use ``alternate_name`` to avoid collisions.

Why full sync matters
~~~~~~~~~~~~~~~~~~~~~

Always validate with:

.. code-block:: bash

    botocraft sync

That catches:

* duplicate public model names across services
* cross-service import collisions
* bad ``alternate_name`` choices
* forward-reference/import problems that a single-service sync can miss
* rewritten generated indexes and package exports that need to stay in sync with
  the new service

Hyphenated service names
~~~~~~~~~~~~~~~~~~~~~~~~

Service directory names use the botocore service codename.  Generated Python
module names use the safe service name, where ``-`` becomes ``_``.

Example:

* data directory: ``botocraft/data/application-autoscaling/``
* generated module: ``botocraft/services/application_autoscaling.py``

Field names whose type matches their own name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a subtle but important edge case.

If a field's Python type annotation ends up equal to the field name itself,
forward references can become invalid or unusable, especially when the field is
optional or readonly.

When this happens, fix it by:

* giving the model an ``alternate_name``, or
* renaming the field with ``rename``

Existing examples like ``S3Object`` and ``ECSTag`` show the general pattern:
rename the generated class to keep the type graph unambiguous.

Circular import avoidance in handwritten code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For handwritten helpers in ``botocraft/mixins``, follow the existing pattern
used across the repository:

* put type-only imports inside ``if TYPE_CHECKING:``
* import generated runtime classes inside the method, property, or helper that
  needs them

This keeps generated modules importable while still allowing precise type hints
in mixins.


Common pitfalls
---------------

``response_attr`` uses the wrong name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a model field is renamed in ``models.yml``, keep using the original botocore
response member name in ``response_attr``.

Overusing explicit ``readonly``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prefer ``input_shapes`` first.  Treat explicit ``readonly`` as a real override,
not routine setup.

Adding too many explicit secondary models too early
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Only define the secondary models you need.  Let dependency-driven generation do
the rest until you have a reason to override behavior.

Using a relation when a property is enough
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you only need a parsed name or ARN component, use a property.  If you need a
resolved resource object, use a relation.

Caching a dynamic relation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Remember that relations default to cached behavior.  Turn caching off when the
underlying AWS state changes often enough that stale object references would be
surprising.

Depending only on service-specific sync
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Service-only sync is useful for local experimentation, but full sync is the
real validation path for maintainers.


Examples worth studying
-----------------------

``ecs``
   Best overall example for relations, properties, decorators, and mixed
   generated/handwritten behavior.

``s3``
   Best example of a bespoke resource plus manager mixin and response-fixing
   decorators.

``sqs``
   Best example of bespoke queue/message modeling and field renaming to
   ``Tags``.


Recommended maintainer loop
---------------------------

#. Discover the service and inspect raw botocore shapes.
#. Create ``models.yml`` and ``managers.yml``.
#. Start with one or two primary models.
#. Prefer ``input_shapes`` over explicit ``readonly`` flags.
#. Add handwritten helpers only when generation is not enough.
#. Run full ``botocraft sync``.
#. Inspect generated code and generated service docs.
#. Run ``botocraft shell`` to catch import and forward-reference problems.
#. Iterate.


Related docs
------------

* :doc:`authoring`
* :doc:`../api/models`
