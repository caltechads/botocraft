SES outbound email
==================

``botocraft`` now exposes outbound send workflows for both classic Amazon SES
(``botocraft.services.ses``) and Amazon SESv2
(``botocraft.services.sesv2``).

Use classic SES when you want the original SES template, verification, and
raw-message APIs. Use SESv2 when you want the newer consolidated
``send_email`` / ``send_bulk_email`` surface.

Classic SES outbound email
--------------------------

Classic SES outbound sending is exposed through three resource-oriented entry
points:

* :py:class:`~botocraft.services.ses.SESIdentity` for sender-bound
  ``send_email`` and ``send_raw_email``
* :py:class:`~botocraft.services.ses.SESTemplate` for
  ``send_templated_email`` and ``send_bulk_templated_email``
* :py:class:`~botocraft.services.ses.SESCustomVerificationEmailTemplate` for
  ``send_custom_verification_email``

For the full generated classic SES service surface, including receiving and
configuration resources, see :doc:`/api/services/ses`.

Imports
~~~~~~~

.. code-block:: python

    from botocraft.services.ses import (
        SESBody,
        SESBulkEmailDestination,
        SESContent,
        SESCustomVerificationEmailTemplate,
        SESDestination,
        SESIdentity,
        SESMessage,
        SESMessageTag,
        SESRawMessage,
        SESTemplate,
    )

Resolve or verify a sender identity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :py:class:`~botocraft.services.ses.SESIdentity` as the model-bound entry
point for sender-specific classic SES operations.

Look up an existing identity:

.. code-block:: python

    identity = SESIdentity.objects.get("sender@example.com")
    if identity is None:
        raise RuntimeError("SES identity not found")

    print(identity.Identity, identity.VerificationStatus)

Start verification through ``create()``. Email identities call
``verify_email_identity``; domain identities call ``verify_domain_identity`` and
preserve the returned verification token:

.. code-block:: python

    identity = SESIdentity(Identity="example.com", IdentityType="Domain")
    identity = SESIdentity.objects.create(identity)
    if identity is None:
        raise RuntimeError("SES identity verification did not return a model")

    print(identity.VerificationToken)

Send one classic SES email
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :py:meth:`~botocraft.services.ses.SESIdentity.send_mail` for the classic
``send_email`` operation:

.. code-block:: python

    identity = SESIdentity.objects.get("sender@example.com")
    if identity is None:
        raise RuntimeError("SES identity not found")

    message_id = identity.send_mail(
        SESDestination(ToAddresses=["user@example.com"]),
        SESMessage(
            Subject=SESContent(Data="Welcome"),
            Body=SESBody(
                Text=SESContent(Data="Thanks for signing up."),
                Html=SESContent(Data="<p>Thanks for signing up.</p>"),
            ),
        ),
        ConfigurationSetName="transactional",
        Tags=[
            SESMessageTag(Name="app", Value="botocraft"),
            SESMessageTag(Name="kind", Value="welcome"),
        ],
    )

    print(message_id)

Send a raw classic SES email
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :py:meth:`~botocraft.services.ses.SESIdentity.send_raw_mail` for MIME-based
messages:

.. code-block:: python

    raw_message_id = identity.send_raw_mail(
        SESRawMessage(Data=b"From: sender@example.com\nTo: user@example.com\n\nhello"),
        Destinations=["user@example.com"],
    )

    print(raw_message_id)

Send templated email with classic SES templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :py:class:`~botocraft.services.ses.SESTemplate` when your workflow is
template-centric. The model-bound methods automatically bind
``Template=self.TemplateName``:

.. code-block:: python

    template = SESTemplate.objects.get("welcome-email")
    if template is None:
        raise RuntimeError("SES template not found")

    message_id = template.send_mail(
        "sender@example.com",
        SESDestination(ToAddresses=["ada@example.com"]),
        '{"first_name": "Ada"}',
        ConfigurationSetName="transactional",
    )

    print(message_id)

For bulk templated sends:

.. code-block:: python

    results = template.send_bulk_templated_mail(
        "sender@example.com",
        [
            SESBulkEmailDestination(
                Destination=SESDestination(ToAddresses=["one@example.com"]),
                ReplacementTemplateData='{"first_name": "Ada"}',
            ),
            SESBulkEmailDestination(
                Destination=SESDestination(ToAddresses=["two@example.com"]),
                ReplacementTemplateData='{"first_name": "Linus"}',
            ),
        ],
        DefaultTemplateData='{"first_name": "Friend"}',
    )

    for result in results:
        print(result.Status, result.MessageId, result.Error)

Send custom verification email
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :py:class:`~botocraft.services.ses.SESCustomVerificationEmailTemplate` to
send one verification email with a stored custom verification template:

.. code-block:: python

    verification_template = SESCustomVerificationEmailTemplate.objects.get(
        "verify-template"
    )
    if verification_template is None:
        raise RuntimeError("SES verification template not found")

    message_id = verification_template.send_verification_mail(
        "person@example.com",
        ConfigurationSetName="transactional",
    )

    print(message_id)

Manager versus model methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Classic SES follows same pattern as other Botocraft services:

* manager methods are canonical boto3 wrappers
* model methods are convenience proxies that bind identity or template fields

Examples:

* :py:meth:`~botocraft.services.ses.SESIdentityManager.send_mail` versus
  :py:meth:`~botocraft.services.ses.SESIdentity.send_mail`
* :py:meth:`~botocraft.services.ses.SESTemplateManager.send_mail` versus
  :py:meth:`~botocraft.services.ses.SESTemplate.send_mail`
* :py:meth:`~botocraft.services.ses.SESTemplateManager.send_bulk_templated_mail`
  versus
  :py:meth:`~botocraft.services.ses.SESTemplate.send_bulk_templated_mail`
* :py:meth:`~botocraft.services.ses.SESCustomVerificationEmailTemplateManager.send_verification_mail`
  versus
  :py:meth:`~botocraft.services.ses.SESCustomVerificationEmailTemplate.send_verification_mail`

Prefer model methods when you already have a resolved identity or template in
hand. Prefer manager methods when your code naturally works with raw identifiers
and explicit arguments.

Common classic SES pitfalls
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``SESIdentity.objects.get(...)`` returns ``None`` when the identity is not
  present in SES.
* ``SESIdentity.objects.create(...)`` is verification, not persistent resource
  creation.
* ``SESIdentity.send_mail()`` and ``SESIdentity.send_raw_mail()`` return AWS
  ``MessageId`` strings.
* ``SESTemplate.send_bulk_templated_mail()`` returns per-destination
  :py:class:`~botocraft.services.ses.SESBulkEmailDestinationStatus` objects, so
  inspect each status instead of assuming the whole batch succeeded.
* Classic SES outbound helpers do not replace SES receiving resources such as
  receipt filters or receipt rule sets.

SESv2 outbound email
--------------------

``botocraft`` exposes Amazon SESv2 outbound sending through
:py:class:`~botocraft.services.sesv2.EmailIdentity` and
:py:class:`~botocraft.services.sesv2.EmailIdentityManager`.

This page focuses on the new outbound send workflow:

* look up a verified sending identity
* send one message with :py:meth:`~botocraft.services.sesv2.EmailIdentity.send`
* send many personalized messages with
  :py:meth:`~botocraft.services.sesv2.EmailIdentity.send_bulk`

For the complete generated SESv2 surface, including the full request and
response model catalog, see :doc:`/api/services/sesv2`.

.. note::

   This guide covers SESv2 outbound mail only. Receiving remains out of scope
   for this slice.

Imports
-------

Overview examples use the SESv2 service module directly:

.. code-block:: python

    from botocraft.services.sesv2 import (
        EmailIdentity,
        SESV2Body,
        SESV2BulkEmailContent,
        SESV2BulkEmailEntry,
        SESV2Content,
        SESV2Destination,
        SESV2EmailContent,
        SESV2ListManagementOptions,
        SESV2Message,
        SESV2MessageTag,
        SESV2ReplacementEmailContent,
        SESV2ReplacementTemplate,
        SESV2Template,
    )

If your application uses a non-default AWS session, call
``EmailIdentity.objects.using(session)`` before ``get`` or ``list``. General
session usage is covered in :doc:`/overview/services`.

Resolve a sending identity
--------------------------

The canonical send entrypoint is the SESv2 email identity. Fetch one by the
verified address or domain you plan to send from:

.. code-block:: python

    identity = EmailIdentity.objects.get("sender@example.com")
    if identity is None:
        raise RuntimeError("SES identity not found")

    if not identity.VerifiedForSendingStatus:
        raise RuntimeError("SES identity is not verified for sending")

You can also work manager-first if you prefer explicit parameters over
model-bound helpers:

.. code-block:: python

    identity = EmailIdentity.objects.get("example.com")
    message_id = EmailIdentity.objects.send(
        "sender@example.com",
        Content=SESV2EmailContent(
            Simple=SESV2Message(
                Subject=SESV2Content(Data="hello"),
                Body=SESV2Body(
                    Text=SESV2Content(Data="plain text body"),
                ),
            ),
        ),
    )

In most application code, the model-bound helpers are more ergonomic because
they automatically bind ``FromEmailAddress`` from ``identity.EmailIdentity``.

Send one email
--------------

Use :py:meth:`~botocraft.services.sesv2.EmailIdentity.send` when you want one
SES ``send_email`` call and only need the AWS message ID back.

Simple message
~~~~~~~~~~~~~~

.. code-block:: python

    identity = EmailIdentity.objects.get("sender@example.com")
    if identity is None:
        raise RuntimeError("SES identity not found")

    message_id = identity.send(
        SESV2EmailContent(
            Simple=SESV2Message(
                Subject=SESV2Content(Data="Welcome"),
                Body=SESV2Body(
                    Text=SESV2Content(Data="Thanks for signing up."),
                    Html=SESV2Content(Data="<p>Thanks for signing up.</p>"),
                ),
            ),
        ),
        Destination=SESV2Destination(
            ToAddresses=["user@example.com"],
        ),
        ConfigurationSetName="transactional",
        EmailTags=[
            SESV2MessageTag(Name="app", Value="botocraft"),
            SESV2MessageTag(Name="kind", Value="welcome"),
        ],
    )

    print(message_id)

``send()`` returns the AWS ``MessageId`` string, not a wrapper response model.

Template message
~~~~~~~~~~~~~~~~

If you already manage SES templates, pass a
:py:class:`~botocraft.services.sesv2.SESV2Template` payload:

.. code-block:: python

    message_id = identity.send(
        SESV2EmailContent(
            Template=SESV2Template(
                TemplateName="welcome-email",
                TemplateData='{"first_name": "Ada"}',
            ),
        ),
        Destination=SESV2Destination(
            ToAddresses=["ada@example.com"],
        ),
    )

Optional send controls
~~~~~~~~~~~~~~~~~~~~~~

The model and manager send methods forward the most useful SESv2 outbound
controls directly:

* ``Destination`` for To/CC/BCC recipients
* ``ReplyToAddresses`` for reply handling
* ``ConfigurationSetName`` for event publishing and delivery configuration
* ``EmailTags`` for analytics and routing metadata
* ``ListManagementOptions`` for contact-list and topic-aware unsubscribe flows
* ``TenantName`` and ``EndpointId`` for SESv2 tenant or multi-region endpoint
  use cases

For example, a list-aware send:

.. code-block:: python

    message_id = identity.send(
        SESV2EmailContent(
            Template=SESV2Template(
                TemplateName="newsletter",
                TemplateData='{"month": "May"}',
            ),
        ),
        Destination=SESV2Destination(
            ToAddresses=["subscriber@example.com"],
        ),
        ListManagementOptions=SESV2ListManagementOptions(
            ContactListName="marketing",
            TopicName="monthly-newsletter",
        ),
    )

Send bulk email
---------------

Use :py:meth:`~botocraft.services.sesv2.EmailIdentity.send_bulk` when you want
one SES ``send_bulk_email`` call with many destination-specific entries.

``send_bulk()`` returns the unwrapped list of
:py:class:`~botocraft.services.sesv2.BulkEmailEntryResult` objects from
``BulkEmailEntryResults``.

Template-driven bulk send
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    results = identity.send_bulk(
        SESV2BulkEmailContent(
            Template=SESV2Template(
                TemplateName="product-update",
                TemplateData='{"company_name": "Example Corp"}',
            ),
        ),
        [
            SESV2BulkEmailEntry(
                Destination=SESV2Destination(
                    ToAddresses=["one@example.com"],
                ),
                ReplacementEmailContent=SESV2ReplacementEmailContent(
                    ReplacementTemplate=SESV2ReplacementTemplate(
                        ReplacementTemplateData='{"first_name": "Ada"}',
                    ),
                ),
            ),
            SESV2BulkEmailEntry(
                Destination=SESV2Destination(
                    ToAddresses=["two@example.com"],
                ),
                ReplacementEmailContent=SESV2ReplacementEmailContent(
                    ReplacementTemplate=SESV2ReplacementTemplate(
                        ReplacementTemplateData='{"first_name": "Linus"}',
                    ),
                ),
            ),
        ],
        DefaultEmailTags=[
            SESV2MessageTag(Name="campaign", Value="product-update"),
        ],
        ConfigurationSetName="bulk-marketing",
    )

    for result in results:
        print(result.Status, result.MessageId, result.Error)

Use ``DefaultContent`` for the shared template, then override recipient-specific
template data per entry with ``ReplacementEmailContent``.

When to use manager vs model methods
------------------------------------

Both APIs call the same SESv2 operations:

* :py:meth:`~botocraft.services.sesv2.EmailIdentityManager.send` and
  :py:meth:`~botocraft.services.sesv2.EmailIdentityManager.send_bulk`
  are the canonical manager methods
* :py:meth:`~botocraft.services.sesv2.EmailIdentity.send` and
  :py:meth:`~botocraft.services.sesv2.EmailIdentity.send_bulk`
  are convenience proxies that bind ``FromEmailAddress`` from the model

Prefer model methods when you already have an ``EmailIdentity`` instance in
hand. Prefer manager methods when your sending code naturally works with a raw
identity string.

Common pitfalls
---------------

* The identity must already exist in SESv2 and be verified for sending.
* ``EmailIdentity.objects.get(...)`` returns ``None`` when the identity does not
  exist.
* ``send()`` returns a single ``MessageId`` string, not a response model.
* ``send_bulk()`` returns per-entry results; inspect each
  :py:class:`~botocraft.services.sesv2.BulkEmailEntryResult` for ``Status`` and
  ``Error`` instead of assuming the whole batch succeeded.
* This page demonstrates the typed Pydantic models because they are the most
  explicit Botocraft-native path. The generated models also accept equivalent
  boto-style dictionaries when that is more convenient.

See also
--------

* :doc:`/overview/services` for general model/manager/session usage
* :doc:`/api/services/sesv2` for the complete SESv2 API reference
