.. _overview_adding_resources:
.. _runbook__service_authoring:

How to add a new service to botocraft
=====================================

This page is maintainer-oriented documentation for adding a brand new AWS
service to ``botocraft`` or adding another model to an existing service.

If you want a field-by-field explanation of the YAML configuration files and the
sync pipeline internals, see :doc:`service_authoring_reference`.


What you are editing
--------------------

The source of truth for service authoring lives in ``botocraft/data``:

* ``botocraft/data/<service_name>/models.yml`` defines primary models,
  secondary models, field overrides, bespoke models, properties, relations,
  manager shortcut methods, and model mixins.
* ``botocraft/data/<service_name>/managers.yml`` defines manager classes,
  generated methods, argument overrides, decorators, manager mixins, and return
  handling.

The generated output lands in two places:

* ``botocraft/services/<service_name>.py``
* ``doc/source/api/services/<service_name>.rst``

Full sync also refreshes:

* ``botocraft/services/__init__.py``
* ``doc/source/_services_index.rst``
* ``doc/source/overview/_services_list.rst``

Do not hand-edit those generated files.  Durable changes belong in
``botocraft/data``, ``botocraft/sync``, or handwritten helpers in
``botocraft/mixins``.


Workflow at a glance
--------------------

.. code-block:: text

    botocore service discovery
        -> create botocraft/data/<service_name>/
        -> choose first primary model(s)
        -> define models.yml
        -> define managers.yml
        -> add mixins/decorators only when generation is not enough
        -> run full "botocraft sync"
        -> inspect generated service code and docs
        -> run "botocraft shell" to catch import/circular-reference issues
        -> iterate until full sync and docs build are clean


1. Find the botocore service alias
----------------------------------

Start by finding the botocore service codename:

.. code-block:: bash

    botocraft botocore services

Find the service you want and use that codename as ``<service_name>``.

Examples:

* ``ecs``
* ``s3``
* ``route53``
* ``application-autoscaling``

The service codename is also the name of the directory under
``botocraft/data``.


2. Create the configuration directory
-------------------------------------

Create the service directory and the two canonical files:

.. code-block:: bash

    mkdir -p botocraft/data/<service_name>
    touch botocraft/data/<service_name>/models.yml
    touch botocraft/data/<service_name>/managers.yml

You can also use:

.. code-block:: bash

    botocraft botocore bootstrap <service_name>

.. important::

   ``botocraft.sync`` loads ``models.yml`` and ``managers.yml``.

   At the time of writing, ``botocraft botocore bootstrap`` creates
   ``models.yaml`` and ``managers.yaml``.  If you use the bootstrap command,
   rename those files to ``.yml`` before running ``botocraft sync``.


3. Inspect the raw botocore models
----------------------------------

Before you write YAML, inspect what botocore actually exposes:

.. code-block:: bash

    botocraft botocore models <service_name>

This shows the available shapes for the service.  Most of them are not primary
resources.  Many are substructures, request/response wrappers, or exception
shapes.

When you want to inspect one shape in detail, including nested dependencies and
related operations, use:

.. code-block:: bash

    botocraft botocore model <service_name> <shape> --dependencies --operations

Use this when you need to answer questions like:

* What fields does this structure really have?
* Which nested structures will need secondary models?
* Which boto3 operations consume or return this shape?
* Does this resource have different input and output shapes?


4. Find likely primary models
-----------------------------

The fastest way to identify likely resource models is:

.. code-block:: bash

    botocraft botocore primary-models <service_name>

This command uses a heuristic: it snake-cases model names and looks for boto3
operations that appear to act on those models.  That makes it a strong starting
point, but not an oracle.

Use the output to identify:

* models that clearly have CRUDL-like operations
* models that look read-only
* models that are likely just nested structures
* places where the resource name and operation name do not line up cleanly

Start with one or two obvious primary models.  It is usually easier to add the
rest after the first full sync succeeds.


5. Pick the first primary models
--------------------------------

A good first primary model usually has most of these properties:

* It represents a real AWS resource instead of a nested structure.
* It has at least ``get`` or ``list`` style operations.
* Its identity is clear enough to define a ``primary_key``.
* Its request and response shapes are understandable from botocore output.

For each primary model, figure out:

* which field is the primary key
* whether there is also an ARN field
* whether there is also a human-readable name field
* which request shapes make fields writable
* whether the service returns extra data that is not present on the main shape

If the service has no clean botocore resource shape, you may need a bespoke
model instead.  ``s3.Bucket`` and ``sqs.Queue`` are the clearest examples.
See :doc:`service_authoring_reference` for when to use bespoke models.


6. Write ``models.yml``
-----------------------

Start small.  Define only the primary models and the secondary models you need
to make those primary models usable.

In practice that means:

* set ``primary_key`` and, when appropriate, ``arn_key`` and ``name_key``
* add ``input_shapes`` first so the generator can infer most writable vs
  readonly behavior automatically
* add ``output_shape`` if the get/list response includes fields that are not on
  the base model shape
* use ``fields`` for targeted overrides such as ``rename``, ``python_type``,
  ``required``, or truly intentional ``readonly`` overrides
* add explicit secondary model config only when you need overrides,
  ``alternate_name``, ``force_create``, or better generated behavior

.. note::

   Many older ``botocraft/data`` entries set ``readonly`` explicitly.  Prefer
   to let the generator infer writability from ``input_shapes`` unless you have
   a real reason to override it.

Choose the smallest useful shape of the model first.  Do not try to encode all
relations, properties, and helper methods in the first edit.


7. Write ``managers.yml``
-------------------------

Once the first primary model exists, define the manager methods that map it to
AWS operations.

Typical first pass:

* ``get``
* ``list``
* ``create`` if the service supports creation cleanly
* ``update`` or ``partial_update`` if the service has a sane update path
* ``delete`` if the service supports deletion

For each method, verify:

* ``boto3_name`` is the actual boto3 client method name
* the response attribute matches the botocore response member name
* argument overrides line up with the botocore input shape
* any nonstandard behavior is clearly documented in YAML or moved to a helper

Use plain generated methods when possible.  Reach for mixins or decorators only
when the generated method body is not enough.


8. Decide whether you need mixins, decorators, properties, or relations
-----------------------------------------------------------------------

Most services start with plain generated models and managers.  Add handwritten
behavior only when the generated code would otherwise be awkward, incomplete, or
wrong.

Use a model mixin when:

* a model needs convenience properties or methods that are not simple YAML
  transformations
* the logic depends on several fields or several related resources
* the behavior should live on the model as real Python code

Use a manager mixin when:

* an operation requires multiple AWS API calls
* the AWS API is too irregular for generated CRUDL methods to feel natural
* the manager needs a helper method that is not a direct boto3 wrapper

Use a method decorator when:

* the generated boto3 call is correct, but the return value needs reshaping
* a list method returns identifiers that should become real model objects
* the API needs a small post-processing step, safety wrapper, or batching shim

Use a property when:

* you are deriving data from fields already present on the model
* a regex, mapping, alias, or small expression is enough

Use a relation when:

* you have raw identifier data and want an object-level link to another primary
  model
* the related target already has a manager
* users will naturally think of the field as another resource, not as raw ID
  data

See :doc:`service_authoring_reference` for detailed relationship guidance and
examples.


9. Put handwritten helpers in ``botocraft/mixins/<service>.py``
---------------------------------------------------------------

Handwritten authoring helpers belong in ``botocraft/mixins/<service>.py``.

That file may contain:

* model mixin classes
* manager mixin classes
* method decorators
* helper functions used by those mixins and decorators

Existing examples worth studying:

* ``botocraft/mixins/ecs.py`` for relation-heavy services, decorators, model
  mixins, and manager mixins
* ``botocraft/mixins/s3.py`` for bespoke resources and response-fixing
  decorators
* ``botocraft/mixins/sqs.py`` for bespoke queue/message behavior

When handwritten helpers need to refer to generated models from other services,
follow the repository's circular-import avoidance pattern:

* put type-only imports under ``if TYPE_CHECKING:``
* keep runtime imports inside the property, method, or helper that actually
  needs them

That is the normal pattern in existing mixin modules.


10. Run the full generator
--------------------------

Always regenerate all services:

.. code-block:: bash

    botocraft sync

Do not rely on ``botocraft sync --service <service_name>`` as your main
validation loop.

.. important::

   Full regeneration catches cross-service problems that service-only sync can
   miss, especially:

   * class name collisions across services
   * import path conflicts
   * alternate-name mistakes
   * circular-reference pressure that only appears when other services import
     the same type names

After sync succeeds, inspect:

* ``botocraft/services/<safe_service_name>.py``
* ``doc/source/api/services/<safe_service_name>.rst``
* ``botocraft/services/__init__.py``
* ``doc/source/_services_index.rst``
* ``doc/source/overview/_services_list.rst``

If the service name contains a hyphen, the generated Python module uses the safe
service name with underscores.


11. Smoke-test the generated import graph
-----------------------------------------

Run:

.. code-block:: bash

    botocraft shell

This is an important maintainer smoke test.  The shell needs to load without
namespace issues, circular import failures, or forward-reference explosions.

If the shell does not load cleanly, investigate naming conflicts before adding
more features to the service.


12. Iterate
-----------

After the first sync succeeds:

* add more primary models
* add secondary model overrides only where they improve generated output
* add properties and relations that feel natural at the object layer
* add mixins or decorators only where generation is not expressive enough
* keep running full ``botocraft sync`` after each meaningful change


Checklist
---------

New service
~~~~~~~~~~~

#. Find the botocore service alias.
#. Create ``botocraft/data/<service_name>/models.yml`` and
   ``botocraft/data/<service_name>/managers.yml``.
#. Inspect raw botocore shapes and operations.
#. Choose one or two likely primary models.
#. Define ``models.yml`` with keys, input shapes, and minimal overrides.
#. Define ``managers.yml`` with the first useful methods.
#. Add mixins or decorators only if generation is not enough.
#. Run full ``botocraft sync``.
#. Inspect generated code and generated service docs.
#. Run ``botocraft shell``.
#. Repeat until the service feels natural to use.

New model in an existing service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Inspect the botocore shape and related operations.
#. Decide whether the model is primary, secondary, or bespoke.
#. Add only the necessary YAML entries.
#. Add properties, relations, or manager shortcut methods if they improve the
   object API.
#. Add mixins or decorators only when YAML alone is not enough.
#. Run full ``botocraft sync``.
#. Check for naming collisions with other services.
#. Run ``botocraft shell``.


Next stop
---------

Continue with :doc:`service_authoring_reference` for the full configuration
reference, relationship authoring guidance, generator internals, and the common
edge cases that show up during sync.
