Bedrock Runtime on FoundationModel
==================================

``botocraft`` exposes Amazon Bedrock Runtime in two complementary ways.  You can
call :py:class:`botocraft.services.bedrock_runtime.ConversationManager`
directly when you want to provide a ``modelId`` on every call, or you can fetch
a :py:class:`botocraft.services.bedrock.FoundationModel` and use its
model-bound helpers from
:py:class:`botocraft.mixins.bedrock_runtime.FoundationModelRuntimeMixin`.

For most application code, the model-bound API is easier to read.  Once you
have a ``FoundationModel`` instance, the runtime helpers automatically bind the
model identity for you and return typed ``botocraft`` models instead of raw
dicts.  In particular, ``messages`` should be built from
:py:class:`botocraft.services.bedrock_runtime.BedrockMessage` objects and
``system`` should be built from
:py:class:`botocraft.services.bedrock_runtime.SystemContentBlock` objects.

Loading a FoundationModel
-------------------------

All examples below use a ``FoundationModel`` instance named ``model``:

.. code-block:: python

    from botocraft.services import BedrockMessage, ContentBlock, FoundationModel, SystemContentBlock

    model = FoundationModel.objects.get(
        "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    if model is None:
        raise LookupError("Foundation model not found.")

If your application uses a non-default AWS session, call
``FoundationModel.objects.using(session).get(...)`` instead.  The rest of the
runtime helper calls stay the same.

Method Mapping
--------------

The following table shows how the generated
:py:class:`botocraft.services.bedrock_runtime.ConversationManager` methods map
to the model-bound helpers on
:py:class:`botocraft.services.bedrock.FoundationModel`.

.. list-table::
   :header-rows: 1

   * - ConversationManager method
     - FoundationModel method
     - Difference
   * - ``converse(modelId, ...)``
     - ``model.converse(...)``
     - ``modelId`` comes from the model instance.
   * - ``converse_stream(modelId, ...)``
     - ``model.converse_stream(...)``
     - ``modelId`` comes from the model instance.
   * - ``count_tokens(modelId, input=...)``
     - ``model.count_tokens(input)``
     - Only ``input`` remains in the call.
   * - ``invoke_model(modelId, ...)``
     - ``model.invoke_model(...)``
     - Raw invoke, but model-bound.
   * - ``invoke_model_with_response_stream(modelId, ...)``
     - ``model.invoke_model_with_response_stream(...)``
     - Raw streaming invoke, but model-bound.
   * - ``start_async_invoke(modelId, ...)``
     - ``model.start_async_invoke(...)``
     - Async invoke starts against the fetched model.
   * - ``get_async_invoke(invocationArn)``
     - ``model.get_async_invoke(invocationArn)``
     - Wrapper verifies the returned ``modelArn`` matches the model instance.
   * - ``list_async_invokes(...)``
     - ``model.list_async_invokes(...)``
     - Wrapper filters each AWS page to summaries for the model's ``modelArn``.

There are two extra conveniences on the model-bound API:

* :py:meth:`botocraft.services.bedrock.FoundationModel.converse` and
  :py:meth:`botocraft.services.bedrock.FoundationModel.converse_stream` accept a
  fetched :py:class:`botocraft.services.bedrock.Guardrail` object through the
  ``guardrail`` keyword argument.
* :py:meth:`botocraft.services.bedrock.FoundationModel.close` closes the
  temporary Bedrock Runtime client used by these helpers.

Conversation Helpers
--------------------

Running ``converse``
^^^^^^^^^^^^^^^^^^^^

Use :py:meth:`botocraft.services.bedrock.FoundationModel.converse` when you
want a normal request/response conversation against one fetched model.

.. code-block:: python

    from botocraft.services import (
        BedrockMessage,
        ContentBlock,
        FoundationModel,
        SystemContentBlock,
    )

    model = FoundationModel.objects.get(
        "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    if model is None:
        raise LookupError("Foundation model not found.")

    conversation = model.converse(
        messages=[
            BedrockMessage(
                role="user",
                content=[
                    ContentBlock(
                        text="Give me three short deployment safety checks."
                    )
                ],
            )
        ],
        system=[SystemContentBlock(text="Answer with concise bullet points.")],
    )

    print(conversation.output.message.role)
    print(conversation.output.message.content[0].text)

Using a Guardrail object
^^^^^^^^^^^^^^^^^^^^^^^^

The model-bound ``converse`` helper accepts a fetched
:py:class:`botocraft.services.bedrock.Guardrail` object directly.  This is the
main convenience difference from the generated manager method.

.. code-block:: python

    from botocraft.services import BedrockMessage, ContentBlock, FoundationModel, Guardrail

    model = FoundationModel.objects.get(
        "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    if model is None:
        raise LookupError("Foundation model not found.")

    guardrail = Guardrail.objects.get("gr-123", guardrailVersion="1")
    if guardrail is None:
        raise LookupError("Guardrail not found.")

    conversation = model.converse(
        messages=[
            BedrockMessage(
                role="user",
                content=[ContentBlock(text="Summarize this incident without secrets.")],
            )
        ],
        guardrail=guardrail,
    )

    print(conversation.stopReason)

Running ``converse_stream``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use :py:meth:`botocraft.services.bedrock.FoundationModel.converse_stream` when
you want the structured streaming response model for one fetched foundation
model.

.. code-block:: python

    from botocraft.services import BedrockMessage, ContentBlock, FoundationModel

    model = FoundationModel.objects.get(
        "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    if model is None:
        raise LookupError("Foundation model not found.")

    response = model.converse_stream(
        messages=[
            BedrockMessage(
                role="user",
                content=[ContentBlock(text="Stream a one sentence release note.")],
            )
        ]
    )

    if response.stream is None:
        raise LookupError("No stream payload returned.")

    if response.stream.messageStart is not None:
        print(response.stream.messageStart.role)

    if (
        response.stream.contentBlockDelta is not None
        and response.stream.contentBlockDelta.delta.text is not None
    ):
        print(response.stream.contentBlockDelta.delta.text)

    if response.stream.messageStop is not None:
        print(response.stream.messageStop.stopReason)

Token Counting
--------------

Running ``count_tokens``
^^^^^^^^^^^^^^^^^^^^^^^^

Use :py:meth:`botocraft.services.bedrock.FoundationModel.count_tokens` to
estimate token usage before calling ``converse`` or ``invoke_model``.

.. code-block:: python

    from botocraft.services import (
        BedrockMessage,
        ContentBlock,
        ConverseTokensRequest,
        CountTokensInput,
        FoundationModel,
        SystemContentBlock,
    )

    model = FoundationModel.objects.get(
        "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    if model is None:
        raise LookupError("Foundation model not found.")

    token_count = model.count_tokens(
        CountTokensInput(
            converse=ConverseTokensRequest(
                messages=[
                    BedrockMessage(
                        role="user",
                        content=[ContentBlock(text="Draft a rollback checklist.")],
                    )
                ],
                system=[SystemContentBlock(text="Keep the answer under five bullets.")],
            )
        )
    )

    print(token_count.inputTokens)

Raw Inference Helpers
---------------------

Running ``invoke_model``
^^^^^^^^^^^^^^^^^^^^^^^^

Use :py:meth:`botocraft.services.bedrock.FoundationModel.invoke_model` when you
need a provider-specific raw request body instead of the higher-level Converse
API.

.. code-block:: python

    from botocraft.services import FoundationModel

    model = FoundationModel.objects.get(
        "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    if model is None:
        raise LookupError("Foundation model not found.")

    response = model.invoke_model(
        body=b'{"inputText":"Summarize this deployment note in one sentence."}',
        contentType="application/json",
        accept="application/json",
    )

    print(response.contentType)
    print(response.body.decode("utf-8"))

.. note::

   ``invoke_model`` is the low-level escape hatch.  ``botocraft`` binds the
   model for you, but the request body itself remains raw provider-specific JSON
   bytes.

Running ``invoke_model_with_response_stream``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use
:py:meth:`botocraft.services.bedrock.FoundationModel.invoke_model_with_response_stream`
for provider-specific raw requests that return a streaming response body.

.. code-block:: python

    from botocraft.services import FoundationModel

    model = FoundationModel.objects.get(
        "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    if model is None:
        raise LookupError("Foundation model not found.")

    response = model.invoke_model_with_response_stream(
        body=b'{"inputText":"Stream a one sentence status update."}',
        contentType="application/json",
        accept="application/json",
    )

    if response.body.chunk is not None:
        print(response.body.chunk.data.decode("utf-8"))

    if response.body.modelStreamErrorException is not None:
        raise RuntimeError(
            response.body.modelStreamErrorException.message or "Stream error"
        )

Async Invocation Helpers
------------------------

Running ``start_async_invoke``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use :py:meth:`botocraft.services.bedrock.FoundationModel.start_async_invoke`
for Bedrock runtime operations that run asynchronously and write output to S3.

.. code-block:: python

    from botocraft.services import (
        AsyncInvokeOutputDataConfig,
        AsyncInvokeS3OutputDataConfig,
        FoundationModel,
    )

    model = FoundationModel.objects.get("amazon.nova-reel-v1:0")
    if model is None:
        raise LookupError("Foundation model not found.")

    job = model.start_async_invoke(
        modelInput={
            "taskType": "TEXT_VIDEO",
            "textToVideoParams": {
                "text": "Cinematic orbital shot of a satellite above Earth."
            },
        },
        outputDataConfig=AsyncInvokeOutputDataConfig(
            s3OutputDataConfig=AsyncInvokeS3OutputDataConfig(
                s3Uri="s3://my-bedrock-output/video-jobs/"
            )
        ),
    )

    print(job.invocationArn)

.. note::

   ``outputDataConfig`` is fully typed in ``botocraft``.  ``modelInput``
   remains provider-specific payload data, so this is one place where you still
   pass the model-native structure directly.

Running ``get_async_invoke``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use :py:meth:`botocraft.services.bedrock.FoundationModel.get_async_invoke` to
look up a specific async invocation that belongs to the fetched model.

.. code-block:: python

    from botocraft.services import FoundationModel

    model = FoundationModel.objects.get("amazon.nova-reel-v1:0")
    if model is None:
        raise LookupError("Foundation model not found.")
    if model.modelArn is None:
        raise ValueError("This helper requires modelArn on the FoundationModel.")

    invocation = model.get_async_invoke(
        "arn:aws:bedrock:us-west-2:123456789012:async-invoke/example"
    )

    print(invocation.status)
    print(invocation.outputDataConfig.s3OutputDataConfig.s3Uri)

If the invocation belongs to a different ``modelArn``, the wrapper raises
``LookupError`` instead of returning the mismatched job.

Running ``list_async_invokes``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use :py:meth:`botocraft.services.bedrock.FoundationModel.list_async_invokes` to
list async invocations for one model.

.. code-block:: python

    from botocraft.services import FoundationModel

    model = FoundationModel.objects.get("amazon.nova-reel-v1:0")
    if model is None:
        raise LookupError("Foundation model not found.")
    if model.modelArn is None:
        raise ValueError("This helper requires modelArn on the FoundationModel.")

    page = model.list_async_invokes(maxResults=10, statusEquals="Completed")

    for summary in page.asyncInvokeSummaries or []:
        print(summary.invocationArn)
        print(summary.status)

    if page.nextToken:
        next_page = model.list_async_invokes(
            maxResults=10,
            nextToken=page.nextToken,
        )
        print(len(next_page.asyncInvokeSummaries or []))

.. note::

   This wrapper filters ``asyncInvokeSummaries`` after each AWS page is returned.
   That means a page can come back with fewer items than ``maxResults``, or even
   no items at all, and still include a ``nextToken`` for the next AWS page.

Closing Runtime Client Resources
--------------------------------

Use :py:meth:`botocraft.services.bedrock.FoundationModel.close` when you want to
explicitly close the temporary Bedrock Runtime client used by these helpers.

.. code-block:: python

    from botocraft.services import FoundationModel

    model = FoundationModel.objects.get(
        "anthropic.claude-3-5-sonnet-20240620-v1:0"
    )
    if model is None:
        raise LookupError("Foundation model not found.")

    model.close()

See Also
--------

For the generated reference documentation, see
:doc:`/api/services/bedrock` and :doc:`/api/services/bedrock_runtime`.
