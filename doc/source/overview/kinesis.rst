Kinesis streams
===============

``botocraft`` now gives you three useful layers for Kinesis streams:

* :py:class:`~botocraft.services.kinesis.KinesisStream` for stream discovery,
  stream-scoped update helpers, and Botocraft-native polling
* :py:class:`~botocraft.services.kinesis.KinesisShard` for shard discovery and
  shard iterator setup
* session-aware access to the underlying boto3 Kinesis client for lower-level
  reads and writes

This page shows common consumer and producer flows for
:py:class:`~botocraft.services.kinesis.KinesisStream`. For generated API
reference, see :doc:`/api/services/kinesis`.

Imports
-------

Overview examples use:

.. code-block:: python

    from datetime import UTC, datetime
    import json

    from botocraft.services.kinesis import (
        KinesisShard,
        KinesisStream,
        KinesisStreamModeDetails,
    )

If you use a non-default AWS session, call
``KinesisStream.objects.using(session)`` before ``get`` or ``list``. General
session usage is covered in :doc:`/overview/services`.

Retrieve one stream
-------------------

Fetch a stream by name with the generated manager:

.. code-block:: python

    stream = KinesisStream.objects.get("my-stream")
    if stream is None:
        raise RuntimeError("stream not found")

    print(stream.StreamName)
    print(stream.StreamARN)
    print(stream.StreamStatus)
    print(stream.tags)

Botocraft hydrates ``tags`` automatically on ``get()`` and ``list()``.

Use ``poll()``
--------------

:py:meth:`~botocraft.services.kinesis.KinesisStream.poll` is Botocraft's
high-level eternal generator for record ingestion:

.. code-block:: python

    for record in stream.poll(
        shard_iterator_type="LATEST",
        limit=100,
        poll_interval_seconds=1.0,
    ):
        print(record.ShardId, record.PartitionKey, record.Data.decode("utf-8"))

``poll()``:

* lists currently open shards through :py:class:`~botocraft.services.kinesis.KinesisShard`
* acquires initial shard iterators for those shards
* keeps calling ``get_records``
* yields generated :py:class:`~botocraft.services.kinesis.KinesisRecord` models
* sleeps briefly when no shard has data in one pass

Use ``poll()`` when you want a long-running consumer and do not need to manage
shard iterators yourself.

Start from timestamp or sequence number
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can start ``poll()`` from a specific timestamp or sequence number:

.. code-block:: python

    for record in stream.poll(
        shard_iterator_type="AT_TIMESTAMP",
        timestamp=datetime(2026, 5, 27, 12, 0, tzinfo=UTC),
        poll_interval_seconds=1.0,
    ):
        print(record.Data.decode("utf-8"))

For sequence-based recovery:

.. code-block:: python

    for record in stream.poll(
        shard_iterator_type="AFTER_SEQUENCE_NUMBER",
        starting_sequence_number="49658015299545671348840649359186658727177341713543663618",
    ):
        print(record.Data.decode("utf-8"))

Inspect shards with Botocraft
-----------------------------

Each stream exposes an uncached ``shards`` relation:

.. code-block:: python

    for shard in stream.shards or []:
        print(shard.ShardId, shard.StreamARN)

This relation uses :py:meth:`~botocraft.services.kinesis.KinesisShardManager.list`
under the hood and returns all shards that ``ListShards`` currently exposes for
the stream.

If you want only shards that are still open for new records, call the shard
manager directly:

.. code-block:: python

    open_shards = KinesisShard.objects.list(
        StreamARN=stream.StreamARN,
        open_only=True,
    )

    for shard in open_shards:
        print(shard.ShardId)

``open_only`` is a Botocraft convenience keyword argument. It is not a raw AWS
``ListShards`` parameter.

Get one shard and create an iterator
------------------------------------

Use the shard manager when you know the shard ID:

.. code-block:: python

    shard = KinesisShard.objects.get(
        "shardId-000000000000",
        StreamARN=stream.StreamARN,
    )
    if shard is None:
        raise RuntimeError("shard not found")

    shard_iterator = shard.iterator("LATEST")
    print(shard_iterator)

You can also create more specific iterators:

.. code-block:: python

    shard.iterator(
        "AT_TIMESTAMP",
        Timestamp=datetime(2026, 5, 27, 12, 0, tzinfo=UTC),
    )

    shard.iterator(
        "AFTER_SEQUENCE_NUMBER",
        StartingSequenceNumber="49658015299545671348840649359186658727177341713543663618",
    )

Useful iterator types:

* ``LATEST``: start with newly arriving records
* ``TRIM_HORIZON``: start from oldest untrimmed records
* ``AT_TIMESTAMP``: start near a specific timestamp
* ``AT_SEQUENCE_NUMBER`` / ``AFTER_SEQUENCE_NUMBER``: resume from known record

Update stream settings from the model
-------------------------------------

The stream model now carries common update operations as instance helpers:

.. code-block:: python

    stream.update_shard_count(
        4,
        "UNIFORM_SCALING",
    )

    stream.update_stream_mode(
        KinesisStreamModeDetails(StreamMode="ON_DEMAND"),
        WarmThroughputMiBps=256,
    )

    stream.update_stream_warm_throughput(512)
    stream.update_max_record_size(2048)

These methods fill in ``StreamARN`` automatically from the stream instance.

Get session-aware Kinesis client
--------------------------------

For lower-level Kinesis APIs, reuse the client bound to the stream's session:

.. code-block:: python

    client = stream.objects.using(stream.session).client

Use this client when you want direct boto3 access for low-level reads or
producer flows.

Read records with raw boto3 shard APIs
--------------------------------------

If you want explicit control over iterators and ``get_records`` calls, drop to
the session-aware client:

.. code-block:: python

    shards = client.list_shards(StreamARN=stream.StreamARN)["Shards"]
    shard_id = shards[0]["ShardId"]

    shard_iterator = client.get_shard_iterator(
        StreamARN=stream.StreamARN,
        ShardId=shard_id,
        ShardIteratorType="TRIM_HORIZON",
    )["ShardIterator"]

    while shard_iterator:
        response = client.get_records(
            StreamARN=stream.StreamARN,
            ShardIterator=shard_iterator,
            Limit=100,
        )

        for record in response["Records"]:
            payload = record["Data"].decode("utf-8")
            print(payload)

        shard_iterator = response.get("NextShardIterator")

Important AWS behavior:

* shard iterators expire after 5 minutes
* each ``get_records`` call returns ``NextShardIterator`` for the next read
* empty ``Records`` means "no records yet", not "stream is finished"

AWS recommends waiting briefly between polling calls when no records arrive.
Botocraft's ``poll()`` helper above handles that loop for you.

Put one record with raw boto3
-----------------------------

Producer flow currently uses the underlying boto3 client:

.. code-block:: python

    response = client.put_record(
        StreamARN=stream.StreamARN,
        PartitionKey="customer-123",
        Data=b'{"event":"hello"}',
    )

    print(response["ShardId"])
    print(response["SequenceNumber"])

``Data`` must be bytes. If you start with JSON or text, encode it first:

.. code-block:: python

    payload = json.dumps({"event": "hello", "ok": True}).encode("utf-8")
    client.put_record(
        StreamARN=stream.StreamARN,
        PartitionKey="customer-123",
        Data=payload,
    )

Put many records with raw boto3
-------------------------------

Batch production uses ``put_records``:

.. code-block:: python

    entries = [
        {
            "PartitionKey": "customer-123",
            "Data": json.dumps({"event": "created"}).encode("utf-8"),
        },
        {
            "PartitionKey": "customer-456",
            "Data": json.dumps({"event": "updated"}).encode("utf-8"),
        },
    ]

    response = client.put_records(
        StreamARN=stream.StreamARN,
        Records=entries,
    )

    print("failed:", response.get("FailedRecordCount", 0))
    for result in response["Records"]:
        print(result.get("ShardId"), result.get("SequenceNumber"))
