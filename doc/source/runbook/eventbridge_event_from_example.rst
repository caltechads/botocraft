.. _overview_adding_events_from_example:

Adding a new EventBridge event to botocraft from an example message
===================================================================

Background
----------

The preferred authoring path for adding  new EventBridge events to botocraft is
:ref:`overview_adding_events_from_schema_library`, which uses the
``botocraft eventbridge export-service`` CLI command plus the new ``schemas``
service to export raw models directly from EventBridge Schema Registry.

This page is the fallback workflow for the cases where that registry path comes
up empty.  Use it when the event exists in AWS service documentation as an
example payload but does not exist in the registry you need to export from.

If you are doing EventBridge maintainership work in this repository, also read
``.skills/botocraft-eventbridge-authoring/SKILL.md`` before you start.  That
skill captures the current preferred workflow for raw exports, wrapper
registration, factory composition, docs, and tests.

Procedure overview
^^^^^^^^^^^^^^^^^^

Before you generate anything by hand, verify that the registry path really does
not already cover the event:

.. code-block:: bash

    botocraft eventbridge export-service <service> --dry-run

If that dry run finds the event you need, stop here and follow
:ref:`overview_adding_events_from_schema_library`.

If the dry run finds nothing useful, use this fallback workflow:

1. Find the event in AWS service documentation and copy the example payload.
2. Turn that payload into an OpenAPI 3.0 schema.
3. Generate a raw Pydantic module locally from that schema.
4. Move the raw module into ``botocraft/eventbridge/raw/<service>/``.
5. Resume the shared wrapper, ``EVENT_CLASS_MAP``, docs, and test workflow from
   :ref:`overview_adding_events_from_schema_library`.

Find an event in the AWS service documentation
----------------------------------------------

Google for ``{service_name} eventbridge events`` to find the service documentation.

Look through the service documentation for events that are only documented as
example messages.  If a service event has no useful registry match from
``botocraft eventbridge export-service --dry-run``, copy the example payload
into a new buffer.

Capture the event's human-facing name as well, for example
``ECR Scan Resource Change``.  You will need that later when you register the
wrapper in ``EVENT_CLASS_MAP``.

AWS API Call via CloudTrail — special case
------------------------------------------

If the event's ``detail-type`` is ``AWS API Call via CloudTrail`` and the
EventBridge ``source`` is ``aws.<service>``, **do not** build an OpenAPI schema
that types ``detail.requestParameters`` from one example operation.  A single
example only reflects one ``detail.eventName``; other operations will not match.

Instead:

1. Copy the **envelope** fields from a trustworthy example (or from
   ``botocraft/eventbridge/raw/acm/aws_api_call_via_cloudtrail.py``).
2. Keep ``requestParameters`` and ``responseElements`` as ``dict[str, Any] | None``.
3. Hand-write ``botocraft/eventbridge/raw/<service>/aws_api_call_via_cloudtrail.py``
   and the top-level ``*AWSAPICallViaCloudTrailEvent`` envelope class.
4. On the wrapper, inherit
   :class:`~botocraft.eventbridge.cloudtrail.CloudTrailApiCallMixin` plus
   :class:`~botocraft.eventbridge.base.EventBridgeEvent` plus the raw class.
5. Register ``("aws.<service>", "AWS API Call via CloudTrail")`` in
   ``EVENT_CLASS_MAP``.
6. Test :meth:`~botocraft.eventbridge.cloudtrail.CloudTrailApiCallMixin.parsed_request`
   for at least one real ``eventName`` (see ``tests/eventbridge/test_cloudtrail.py``).

Operation-specific typing is **lazy**: callers use ``event.parsed_request()``,
which builds a cached Pydantic model from the botocore operation input shape for
``detail.eventSource`` and ``detail.eventName``.  See
:doc:`/runbook/eventbridge_event_from_schema` for the full contract.

Skip the OpenAPI / ``datamodel-codegen`` steps below for this event family and
resume at :ref:`overview_adding_events_from_example_resume_wrapper`.

Convert the example message to OpenAPI 3.0 schema
-------------------------------------------------

Use your editor or coding assistant to generate an OpenAPI 3.0 schema from the
example message.  Ensure the example payload is focused and ask for a schema
that includes all nested fields, required properties, and types.

.. code-block:: text

    Generate an OpenAPI 3.0 schema for the currently selected example
    EventBridge event payload. Include all nested fields, reasonable required
    fields, and valid property types.

Save that schema to your filesystem, for example as ``schema.yaml``.

Generate the raw Pydantic models locally
----------------------------------------

The local fallback should mirror the same toolchain the CLI exporter uses:

.. code-block:: bash

    datamodel-codegen \
      --input schema.yaml \
      --input-file-type openapi \
      --output-model-type pydantic_v2.BaseModel \
      --output generated_event.py

    bump-pydantic generated_event.py

Then inspect the generated file and rename the primary event class to Botocraft's
service-prefixed convention, for example ``ECRScanResourceChangeEvent``.

Move the raw module into the correct raw package
------------------------------------------------

Move the generated file into ``botocraft/eventbridge/raw/<service>/``.  If this
is the first raw module for the service, create the package and make sure the
``__init__.py`` files re-export the new class.

At the end of this step you should have:

* ``botocraft/eventbridge/raw/<service>/<module>.py``
* ``botocraft/eventbridge/raw/<service>/__init__.py``
* ``botocraft/eventbridge/raw/__init__.py``

.. _overview_adding_events_from_example_resume_wrapper:

Resume the shared wrapper workflow
----------------------------------

Once you have a raw module, rejoin the normal EventBridge authoring path from
:ref:`overview_adding_events_from_schema_library`.

That means:

1. Add or update the wrapper module in ``botocraft/eventbridge/<service>.py``.
2. For ``AWS API Call via CloudTrail``, include
   :class:`~botocraft.eventbridge.cloudtrail.CloudTrailApiCallMixin`.
3. Register the wrapper through ``EVENT_CLASS_MAP``.
4. Update docs and targeted tests (include ``parsed_request`` for CloudTrail events).
5. Verify that :py:class:`~botocraft.eventbridge.factory.EventFactory` can now
   decode the new event type.


Caveats
-------

Since you are generating the OpenAPI schema from an example payload, the result
may still be incomplete:

* optional fields may look required
* fields present in other real events may be missing
* nested shapes may need cleanup after you see real traffic

Treat the example payload as a strong starting point, not a contract.  As real
events arrive, adjust the raw model and wrapper as needed.

**Exception:** ``AWS API Call via CloudTrail`` events intentionally keep
``requestParameters`` flexible in the raw model.  Use ``parsed_request()`` for
operation-aware validation instead of expanding the raw schema per ``eventName``.