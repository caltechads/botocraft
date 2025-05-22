.. _overview_adding_events_from_example:

Adding a new EventBridge event to botocraft from an example message
===================================================================

Background
----------

The ``botocraft.eventbridge`` module contains a factory class
(:py:class:`~botocraft.eventbridge.factory.EventFactory`) that decodes the json
from an EventBridge event and loads it into a corresponding Pydantic model.  This
factory class is currently used by :py:meth:`~botocraft.services.sqs.Queue.poll`
to decode the raw json of an event into a usable Pydantic model.

We then have wrappers for the raw Pydantic models from the EventBridge schema that
add appropriate relations to other ``botocraft`` models from attributes of the raw
event model, as well has convenience properties.

Normally we would use the procedure in
:ref:`overview_adding_events_from_schema_library` to implement a new event, but
the AWS EventBridge schema library is not complete, even for the AWS services
that seem to be represented.

This recipe shows how to implement a new event from an example message, rather
than from the schema library.  This is useful when the event is not in the
EventBridge schema library at all.

Procedure overview
^^^^^^^^^^^^^^^^^^

First, complete adding all the events from the EventBridge schema library, using :ref:`overview_adding_events_from_schema_library` as a guide.

Then, look to ensure that the service documentation does not have any other events
listed that are not in the EventBridge schema library.  Normally these events are
listed as example messages, not OpenAPI 3.0 schema as in the EventBridge schema
library, so we have to do some extra work to implement them.

1. Google for ``{service_name} eventbridge events`` to find the service documentation.
2. Find the event you want to implement and copy the example message into a buffer in
   VSCode.
3. Ask Copilot Chat to generate an OpenAPI 3.0 schema for the example message.  One things
   to note is that this may not be exactly accurate, because the example message may not
   be complete or acknowledge that some fields are optional.
4. Save the schema to your filesystem
5. Go back to :ref:`overview_adding_events_from_schema_library` and follow the steps from (3)
   to the end to generate the Pydantic models and implement the event.

Find an event in the AWS service documentation
----------------------------------------------

Google for ``{service_name} eventbridge events`` to find the service documentation.

In another tab in your browser, open for the AWS EventBridge schema library and
search for` ``aws.{service_name}`` to see what events are already implemented in
the EventBridge schema library.  Note that there may be no hits at all for your service
in the EventBridge schema library, so all the events are new.

Look through the service documentation to see if there are any events that are not
in the EventBridge schema library.  These events are always listed as example
messages, not OpenAPI 3.0 schema as in the EventBridge schema library.   Look at each event and note the description (e.g. ``ECR Scan State Change``).  If no such event exists in the
EventBridge schema library, then copy the example event into a new buffer in VSCode.

Convert the example message to OpenAPI 3.0 schema
-------------------------------------------------

Ask Copilot Chat to generate an OpenAPI 3.0 schema for the example message.  Claude 3.7 Sonnet Thinking does a good job of this.  Ensure the file with your example message is focused, open the Copilot Chat interface (typically in the left sidebar), and use this prompt:

.. code-block:: text

    Generate an OpenAPI 3.0 schema JSON message in the currently selected
    buffer.  The schema should be valid OpenAPI 3.0 and should include all the
    fields in the message, including any nested fields.  The schema should also
    include any required fields and their types.

Let it work, apply the changes to your file, and save the file to your
filesystem.

Proceed with the normal procedure
---------------------------------

Now that you have the OpenAPI 3.0 schema, you can proceed with the normal
procedure for adding an event to ``botocraft``.  See :ref:`overview_adding_events_from_schema_library`
for the steps to follow, starting at step (3) (Run ``datamodel-codegen`` on that schema to generate the Pydantic models).


Caveats
-------

Since we're generating the OpenAPI 3.0 schema from an example message, there may
be inconsistencies between the example message and all possibilities for the
actual event.  For example, the example message may not include all the fields that are
actually present in the event, or some of the included fields may be optional.  You
may have to adjust the generate Pydantic models to account for this in future releases.