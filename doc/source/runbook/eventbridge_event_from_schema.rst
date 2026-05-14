.. _overview_adding_events_from_schema_library:

Adding a new EventBridge event to botocraft from AWS Schema Registry
====================================================================

Background
----------

``botocraft`` has a first-class EventBridge authoring path for schemas in the
AWS Schema Registry.

* the ``schemas`` service in ``botocraft.services`` lets you list and export
  EventBridge schemas from registries such as ``aws.events``
* the ``botocraft eventbridge export-service`` CLI command exports matching
  OpenAPI schemas, generates raw Pydantic models, and refreshes
  ``botocraft/eventbridge/raw/<service>/``
* wrapper modules in ``botocraft.eventbridge`` expose declarative
  ``EVENT_CLASS_MAP`` constants that :py:class:`~botocraft.eventbridge.factory.EventFactory`
  composes automatically

If you are doing EventBridge maintainership work in this repository with a coding agent
you can use ``.skills/botocraft-eventbridge-authoring/SKILL.md``.  That skill reflects the
current authoring path and keeps the raw export, wrapper work, factory wiring,
and docs follow-through aligned.

How schema discovery works
--------------------------

The CLI is built on top of the ``schemas`` botocraft service.  Under the hood it is
doing work equivalent to:

.. code-block:: python

    from botocraft.services import Schema

    schemas = Schema.objects.list(
        RegistryName="aws.events",
        SchemaNamePrefix="aws.cloudtrail",
    )

    for schema in schemas:
        latest_version = max(
            schema.versions(),
            key=lambda version: int(version.SchemaVersion),
        )
        exported = schema.export(SchemaVersion=latest_version.SchemaVersion)

The CLI then runs ``datamodel-codegen`` and ``bump-pydantic`` for you, renames
the primary generated class to Botocraft's service-prefixed convention, and
refreshes the ``__init__.py`` re-exports in the raw package.

Using a coding agent to add event support for a service
-------------------------------------------------------

To use the skill, you can use the following prompt:

.. code-block:: text

    Add Botocraft EventBridge support for the `rds` service.  Use the skill `botocraft-eventbridge-authoring` in .skills to do this.

Manual workflow
---------------

Procedure overview
^^^^^^^^^^^^^^^^^^

To add a new EventBridge event from Schema Registry, follow this path:

1. Use ``botocraft eventbridge export-service <service>`` to discover and export
   raw schema models for the service.
2. Inspect the generated modules in ``botocraft/eventbridge/raw/<service>/``.
3. Add or update the handwritten wrapper module in
   ``botocraft/eventbridge/<service>.py``.
4. Register wrapper classes through that module's ``EVENT_CLASS_MAP`` constant.
5. Update docs and tests for the new event types.

Export raw schemas with the CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The normal entry point is:

.. code-block:: bash

    botocraft eventbridge export-service cloudtrail

Default behavior:

* searches the ``aws.events`` registry
* filters schema names with the prefix ``aws.<service>``
* writes raw modules under ``botocraft/eventbridge/raw/<service>/``

The most useful options are:

.. code-block:: bash

    botocraft eventbridge export-service cloudtrail \
      --registry-name aws.events \
      --schema-name-prefix aws.cloudtrail \
      --raw-root botocraft/eventbridge/raw \
      --dry-run

Use ``--dry-run`` first when you want to inspect what will be exported without
writing files or running code generators.

If the default registry has no matches, the command fails with a message telling
you to retry with one or more explicit ``--registry-name`` values.


Inspect and normalize the raw models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After export, inspect the generated modules under
``botocraft/eventbridge/raw/<service>/``.

Things to verify:

* generated class names are readable and unique
* raw field names match the upstream schema
* any generated imports or typing oddities are cleaned up

The CLI already applies the repository's standard class renaming convention, so
for many events this step is mostly inspection plus any small cleanup you need.

Add the handwritten wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add or update the service wrapper module in ``botocraft/eventbridge``.  Wrapper
classes should inherit from both :py:class:`~botocraft.eventbridge.base.EventBridgeEvent`
and the raw generated class:

.. code-block:: python

    from .base import EventBridgeEvent
    from .raw import CloudtrailAWSAPICallViaCloudTrailEvent as RawCloudtrailAWSAPICallViaCloudTrailEvent


    class CloudtrailAWSAPICallViaCloudTrailEvent(
        EventBridgeEvent,
        RawCloudtrailAWSAPICallViaCloudTrailEvent,
    ):
        """
        Friendly Botocraft wrapper for the CloudTrail API call event.
        """

Use the wrapper for:

* convenience properties
* related-resource lookups
* readable ``__str__`` helpers
* any event-specific ergonomics that belong on the event object itself

Keep raw schema classes thin.  Put human-oriented behavior in the wrapper.

Register the event declaratively
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Do not add new nested conditionals to ``EventFactory.new()``.

Instead, export a flat mapping from the wrapper module:

.. code-block:: python

    EVENT_CLASS_MAP = {
        (
            "aws.cloudtrail",
            "AWS API Call via CloudTrail",
        ): CloudtrailAWSAPICallViaCloudTrailEvent,
    }

``EventFactory`` composes those per-module maps into one lookup table.  Unknown
events still fall back to raw ``dict`` payloads.

Add docs and tests
^^^^^^^^^^^^^^^^^^

When you add new event support, also update:

* the relevant API docs under ``doc/source/api/eventbridge/<service>/``
* any maintainer docs that mention the supported workflow
* targeted tests for factory mapping, wrappers, and authoring helpers

The most relevant tests for this workflow today are:

* ``tests/cli/test_eventbridge.py``
* ``tests/eventbridge/test_factory.py``
* ``tests/mixins/test_schemas.py``

Caveats
-------

Schema Registry coverage is still incomplete.  When the registry does not
contain the event you need, switch to
:doc:`/runbook/eventbridge_event_from_example` and build the initial OpenAPI
schema from an example payload instead.