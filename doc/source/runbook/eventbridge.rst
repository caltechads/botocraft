.. _overview_adding_events_from_schema_library:

Adding a new EventBridge event to botocraft from the Schema library
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

Procedure overview
^^^^^^^^^^^^^^^^^^

To add a new EventBridge event to botocraft, follow these steps:

1. Go to the AWS EventBridge console, and click on the Schema library.
2. Find the schema you want to add and download its OpenAPI 3.0 schema to your filesystem.
3. Run ``datamodel-codegen`` on that schema to generate the Pydantic models.
4. Run ``bump-pydantic`` on the generated code to convert it from Pydantic v1 to v2 (``datamodel-codegen`` generates v1 code).
5. Edit the file you just created, and rename the ``AWSEvent`` class to ``<SERVICE><event name>Event``, so for the ECS Task State Change event, you would name that class ``ECSTaskStateChangeEvent``.  We need to do this so we have unique names for each event.
6. Open VSCode chat and ask it to document the python file you just edited.
7. Move your python file to the appropriate folder under ``botocraft.eventbridge.raw``.  The folder should be named for the service that generates the event.  So if this is an ``aws.s3`` event, put the file in ``botocraft.eventbridge.raw.s3``, making the directory, adding ``__init__.py`` if necessary, adding ``from .<your_module> import *`` to the ``__init__.py`` in ``botocraft.eventbridge.raw``
8. Edit the appropriate service file in ``botocraft.eventbridge`` for your service and add the wrapper class, adding relations and properties as desired.
9. Update the factory class to recognize the new event type and return an instance of the new model.
10. Add the event file the ``botocraft`` API documentation.

Download the EventBridge Schema
-------------------------------

You can download the EventBridge schema from the AWS EventBridge console.
Navigate to the Schema library, find the schema of the event you want to add to
``botocraft``, and download its OpenAPI 3.0 schema to your filesystem.

You can filter by service by typing ``aws.{service_name}`` in the search bar, where
``service_name`` is lowercase.

If there are multiple versions of the schema, choose the latest one, then click
the "Actions" dropdown and choose "Download schema (version <version_number>)"

.. note::

    The EventBridge schema library is not complete, even for the AWS services that seem
    to be complete.  For example, the ``aws.ecr`` service has a schema for the
    ``ECS Task State Change`` event, but not for the ``ECR ECR Scan Resource Change``
    event.

    Thus to truly implement ALL the events for a service, you may need to google for
    ``{service_name} eventbridge events``.

Run ``datamodel-codegen`` on that schema to generate the Pydantic models.
-------------------------------------------------------------------------

Generate the Pydantic models like so

.. code-block:: bash

    datamodel-codegen --input yourschema.json --input-file-type=openapi --output your_schema.py

Where ``your_schema.py`` should be the name of the event, in snake-case.

Run ``bump-pydantic`` on the generated code
-------------------------------------------

``datamodel-codegen`` generates Pydantic v1 code, but we need v2.  ``bump-pydantic`` will handle this for us.

.. code-block:: bash

    bump-pydantic your_schema.py
    rm log.txt

Change the name of the main class to reflect your event name
------------------------------------------------------------

Edit the file you just created in VSCode, and rename the ``AWSEvent`` class to
``<SERVICE><event name>Event``, so for the ECS Task State Change event, you
would name that class ``ECSTaskStateChangeEvent``.  We need to do this so we
have unique names for each event.

While you're in there, fix any ``ruff`` warnings.  Typically these are bout the
imports.

Document the file
-----------------

Either document the file manually, or use VSCode chat to do it.  Claude 3.7
Sonnet Thinking is a good model to use for documenting the code.   Place focus
on the open file in VSCode and ask Chat (typically in the left sidebar) to document
the file using the following prompt:

.. code-block::

    Please add reasonable class and attribute documentation to the currently
    selected file.  Please document each attribute using `#:` notation.  For the
    class documentation, please put the triple quotes on separate lines and wrap
    lines to 88 characters.

Chat will think for a while, and then produce updated code.  Apply the code.

Possibly make a new folder for your file
----------------------------------------

If this is the first time you're adding an event for this service, do the
following things:

1. Create a new folder for your event file under the appropriate service directory.  The folder should be named for the service that generates the event.  So if this is an ``aws.s3`` event, create a folder named ``botocraft.eventbridge.raw.s3`` and move your event file there.
2. Create an ``__init__.py`` file in the new folder to make it a package.
3. Add an import statement to the ``__init__.py`` file to import your new event class.
4. In ``botocraft.eventbridge.raw`` add ``from .{service_name} import *```

Move your file to the right place
---------------------------------

Finally you can move your new python file to the proper place:

.. code-block:: shell

    mv your_event.py botocraft/eventbridge/raw/<service>

Add the wrapper class for your event
-------------------------------------

Edit the appropriate service file in ``botocraft.eventbridge`` for your service
and add the wrapper class, adding relations and properties as desired.  If that
file doesn't exist, create it.  Example: if you want to add a wrapper for an S3
event, but ``botocraft.eventbridge.s3`` doesn't exist, create
``botocraft/eventbridge/s3.py``.

Import your "raw" class like so:

.. code-block:: python

    from .raw import <eventclass> as Raw<eventclass>

Now add a class named ``<eventclass>`` that starts like this:

.. code-block:: python

    class <eventclass>(EventBridgeEvent, Raw<eventclass>):
        """
        Appropriate docstring
        """

and look through the raw event for attributes you can use to implement relations
(properties that use attributes on you raw event class that return ``botocraft``
objects). on your wrapper class.   Look at some of the existing event wrappers
for inspiration, like
:py:class:`~botocraft.eventbridge.ecs.ECSTaskStateChangeEvent`

You can also add basic properties here for deep attributes on your event class
that you think people may want to use frequently.

Update ``EventFactory`` to be able to deal with the new event
-------------------------------------------------------------

Open  ``botocraft.eventbridge.factory`` and change
:py:meth:`~botocraft.eventbridge.factory.EventFactory.new`  to recognize your
new event.  Follow the paradigm already existing in that method.

Add your new event to the API documentation
-------------------------------------------

Add your new event to the API documentation.  This is done in
``doc/source/api/eventbridge/<service>/<event>.rst``.

Remember to add the new event to the ``doc/source/index.rst`` file.