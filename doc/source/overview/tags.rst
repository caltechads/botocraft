AWS Resource Tags in botocraft
==============================

Many AWS resources support tagging, which allows you to assign metadata to your
resources in the form of key-value pairs. Tags are useful for organizing
resources, tracking costs, implementing access control, and more.

In ``botocraft``, we've simplified working with tags by providing a consistent
interface across all services, despite the fact that the underlying AWS APIs
represent tags differently depending on the service and resource type.

Tag Dictionary Interface
-----------------------

All taggable ``botocraft`` models implement a ``tags`` property that provides a
dictionary-like interface to the resource's tags. This property allows you to:

* Access tags using dictionary syntax
* Set tags using dictionary syntax
* Delete tags using dictionary syntax
* Iterate over tags as key-value pairs

Example Usage
------------

Here's an example of working with tags on an EC2 instance:

.. code-block:: python

    from botocraft.services import Instance

    # Get an instance
    instance = Instance.objects.get('i-1234567890abcdef0')

    # Access tags
    print(instance.tags)  # {'Name': 'web-server', 'Environment': 'production'}
    print(instance.tags['Name'])  # 'web-server'

    # Check if a tag exists
    if 'Environment' in instance.tags:
        print(f"Environment: {instance.tags['Environment']}")

    # Set a new tag
    instance.tags['Department'] = 'Engineering'

    # Update an existing tag
    instance.tags['Environment'] = 'staging'

    # Delete a tag
    del instance.tags['Department']

    # Iterate over tags
    for key, value in instance.tags.items():
        print(f"{key}: {value}")

    # Save the changes
    instance.save()

Underlying Implementation
-------------------------

Behind the scenes, ``botocraft`` handles the conversion between the dictionary
interface and the various tag representations used by different AWS services:

* Some services (like EC2) represent tags as a list of objects with ``Key`` and ``Value`` properties
* Other services use a list of objects with ``key`` and ``value`` (lowercase)
* Some services represent tags directly as a dictionary
* A few services have other unique representations

When you access ``model.tags``, ``botocraft`` automatically converts from the
service-specific representation to a Python dictionary. When you save the model,
``botocraft`` converts the dictionary back to the appropriate representation for
the service.

Service-Specific Tag Behavior
-----------------------------

While the tags dictionary provides a consistent interface, there are some
service-specific behaviors to be aware of:

* Some services have tag naming restrictions (e.g., certain characters may not be allowed)
* Some services have limits on the number of tags per resource
* Some services have tag propagation features that can apply tags from one resource to related resources

For details on these restrictions, consult the AWS documentation for the
specific service you're working with.

Creating Resources with Tags
---------------------------

You can also set tags when creating a new resource:

.. code-block:: python

    from botocraft.services import Instance

    # Create a new instance with tags
    instance = Instance(
        # ... other instance properties ...
        tags={'Name': 'web-server', 'Environment': 'production'}
    )
    instance.save()

The ``TagsDictMixin``
--------------------

For advanced users and contributors, the tags functionality is implemented
through the ``TagsDictMixin`` class. This mixin adds the tags dictionary
interface to a model by mapping between the service-specific tag representation
and a Python dictionary.

Different services use different model classes for tags (e.g., ``EC2Tag``,
``ECSTag``), so the mixin needs to know which tag class to use for a particular
model. This is configured through the ``tag_class`` class variable and the
``Tags`` field.

In most cases, you won't need to interact with these implementation details
directly, as the tags dictionary interface provides a clean abstraction.

Conclusion
---------

The consistent tags dictionary interface in ``botocraft`` makes it easy to work
with tags across different AWS services, without having to worry about the
varying underlying representations. This approach simplifies your code and makes
it more maintainable by providing a uniform way to handle tags for all
resources.
