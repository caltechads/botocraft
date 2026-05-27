"""Handwritten helpers for generated Kinesis service managers."""

from __future__ import annotations

import time
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Generator, Literal, cast

from botocraft.mixins.common import arg_value, ensure_queryset

if TYPE_CHECKING:
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
    from botocraft.services.common import Tag
    from botocraft.services.kinesis import (
        KinesisConsumer,
        KinesisRecord,
        KinesisShard,
        KinesisStream,
    )


class KinesisResponseHelper:
    """
    Hydrate Kinesis manager responses into stable public models.

    Args:
        manager: Generated manager instance that owns boto3 client and session.

    """

    #: Generated manager instance used for follow-up AWS calls and sessionization.
    manager: Any

    def __init__(self, manager: Any) -> None:
        """
        Initialize helper for one generated manager call.

        Args:
            manager: Generated manager instance that owns boto3 client and session.

        """
        #: Generated manager instance used for follow-up AWS calls and sessionization.
        self.manager = manager

    def _tag_models(self, tags: list[dict[str, Any]] | None) -> list[Tag]:
        """
        Convert raw tag dictionaries into generated tag models.

        Args:
            tags: Raw tag dictionaries returned by boto3.

        Returns:
            Generated tag models.

        """
        from botocraft.services.common import Tag

        if not tags:
            return []
        return [Tag(**tag) for tag in tags]

    def _load_tags(self, resource_arn: str | None) -> list[Tag]:
        """
        Load tag models for one Kinesis resource.

        Args:
            resource_arn: Resource ARN to query.

        Returns:
            Tag models for resource, or empty list when ARN absent.

        """
        if not resource_arn:
            return []
        response = self.manager.client.list_tags_for_resource(ResourceARN=resource_arn)
        return self._tag_models(response.get("Tags"))

    def _sessionize(self, model: Any) -> Any:
        """
        Attach active boto3 session to one model or queryset.

        Args:
            model: Model or queryset to sessionize.

        Returns:
            Same object after sessionization.

        Side Effects:
            Binds manager session to returned object graph.

        """
        self.manager.sessionize(model)
        return model

    def stream_with_tags(self, stream: KinesisStream | None) -> KinesisStream | None:
        """
        Attach tags to one Kinesis stream model.

        Args:
            stream: Stream model returned by generated manager method.

        Returns:
            Hydrated stream model, or ``None`` when result absent.

        """
        if stream is None:
            return None
        stream.Tags = self._load_tags(stream.StreamARN)
        return cast("KinesisStream", self._sessionize(stream))

    def streams_with_tags(self, results: Any) -> PrimaryBoto3ModelQuerySet:
        """
        Attach tags to listed Kinesis streams.

        Args:
            results: List or queryset of Kinesis stream models.

        Returns:
            Queryset of enriched stream models.

        """
        query_set = ensure_queryset(results)
        for stream in query_set.results:
            stream.Tags = self._load_tags(cast("KinesisStream", stream).StreamARN)
        return cast("PrimaryBoto3ModelQuerySet", self._sessionize(query_set))

    def consumer_with_tags(
        self,
        consumer: KinesisConsumer | None,
        *,
        stream_arn: str | None = None,
    ) -> KinesisConsumer | None:
        """
        Attach tags and optional parent stream ARN to one consumer model.

        Args:
            consumer: Consumer model returned by generated manager method.

        Keyword Args:
            stream_arn: Optional stream ARN to backfill when AWS omitted it.

        Returns:
            Hydrated consumer model, or ``None`` when result absent.

        """
        from botocraft.services.kinesis import KinesisConsumer

        if consumer is None:
            return None
        if stream_arn and getattr(consumer, "StreamARN", None) is None:
            payload = consumer.model_dump(exclude_none=True)
            payload["StreamARN"] = stream_arn
            consumer = KinesisConsumer(**payload)
        consumer.Tags = self._load_tags(consumer.ConsumerARN)
        return cast("KinesisConsumer", self._sessionize(consumer))

    def consumer_from_create(
        self,
        consumer: KinesisConsumer | None,
        *args: Any,
        **kwargs: Any,
    ) -> KinesisConsumer | None:
        """
        Hydrate create-consumer response into public consumer model.

        Args:
            consumer: Consumer model returned by generated create method.
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Hydrated consumer model, or ``None`` when result absent.

        """
        model = arg_value(args, kwargs, "model", 0)
        stream_arn = getattr(model, "StreamARN", None)
        return self.consumer_with_tags(consumer, stream_arn=stream_arn)

    def consumers_with_tags(
        self,
        results: Any,
        *args: Any,
        **kwargs: Any,
    ) -> PrimaryBoto3ModelQuerySet:
        """
        Attach tags and list-scope context to listed Kinesis consumers.

        Args:
            results: List or queryset of Kinesis consumer models.
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Queryset of enriched consumer models.

        """
        stream_arn = cast("str | None", arg_value(args, kwargs, "StreamARN", 0))
        query_set = ensure_queryset(results)
        for index, consumer in enumerate(query_set.results):
            hydrated = self.consumer_with_tags(
                cast("KinesisConsumer", consumer),
                stream_arn=stream_arn,
            )
            if hydrated is not None:
                query_set.results[index] = hydrated
        return cast("PrimaryBoto3ModelQuerySet", self._sessionize(query_set))


class KinesisTagsManagerMixin:
    """
    Shared Kinesis tag serialization helpers for handwritten manager methods.
    """

    def _tag_map(self, tags: list[Any] | None) -> dict[str, str] | None:
        """
        Convert Botocraft tag models into AWS Kinesis tag maps.

        Args:
            tags: Botocraft tag models or raw tag dictionaries.

        Returns:
            AWS tag map, or ``None`` when no tags were supplied.

        """
        if not tags:
            return None
        payload: dict[str, str] = {}
        for tag in tags:
            if isinstance(tag, dict):
                key = cast("str | None", tag.get("Key"))
                value = cast("str | None", tag.get("Value"))
            else:
                key = cast("str | None", getattr(tag, "Key", None))
                value = cast("str | None", getattr(tag, "Value", None))
            if key is not None:
                payload[key] = "" if value is None else value
        return payload or None


class KinesisShardManagerMixin:
    """
    Handwritten shard helpers for :py:class:`KinesisShardManager`.

    This mixin owns Botocraft-specific shard ergonomics such as the
    ``open_only`` filter and stream-context backfilling.
    """

    #: Boto3 client used by generated Kinesis shard manager.
    client: Any

    def _stream_identity_kwargs(
        self,
        *,
        StreamARN: str | None = None,  # noqa: N803
        StreamName: str | None = None,  # noqa: N803
    ) -> dict[str, str]:
        """
        Validate and normalize stream identity kwargs.

        Keyword Args:
            StreamARN: Optional stream ARN.
            StreamName: Optional stream name.

        Returns:
            Stream identity kwargs for downstream AWS calls.

        Raises:
            ValueError: Neither stream ARN nor stream name was provided.

        """
        if StreamARN:
            return {"StreamARN": StreamARN}
        if StreamName:
            return {"StreamName": StreamName}
        msg = "StreamARN or StreamName is required for Kinesis shards."
        raise ValueError(msg)

    def _validate_iterator_args(
        self,
        ShardIteratorType: Literal[  # noqa: N803
            "AT_SEQUENCE_NUMBER",
            "AFTER_SEQUENCE_NUMBER",
            "TRIM_HORIZON",
            "LATEST",
            "AT_TIMESTAMP",
        ],
        *,
        StartingSequenceNumber: str | None = None,  # noqa: N803
        Timestamp: Any | None = None,  # noqa: N803
    ) -> None:
        """
        Validate ``get_shard_iterator`` prerequisites.

        Args:
            ShardIteratorType: Iterator type requested for shard reads.

        Keyword Args:
            StartingSequenceNumber: Optional starting sequence number.
            Timestamp: Optional iterator timestamp.

        Raises:
            ValueError: Required iterator inputs are missing.

        """
        if ShardIteratorType in {
            "AT_SEQUENCE_NUMBER",
            "AFTER_SEQUENCE_NUMBER",
        } and not StartingSequenceNumber:
            msg = (
                "starting_sequence_number is required for "
                f"{ShardIteratorType.lower()}."
            )
            raise ValueError(msg)
        if ShardIteratorType == "AT_TIMESTAMP" and Timestamp is None:
            msg = "timestamp is required for at_timestamp."
            raise ValueError(msg)

    def list(  # noqa: PLR0913
        self,
        *,
        StreamARN: str | None = None,  # noqa: N803
        StreamName: str | None = None,  # noqa: N803
        ExclusiveStartShardId: str | None = None,  # noqa: N803
        MaxResults: int | None = None,  # noqa: N803
        NextToken: str | None = None,  # noqa: N803
        ShardFilter: Any | None = None,  # noqa: N803
        StreamCreationTimestamp: Any | None = None,  # noqa: N803
        StreamId: str | None = None,  # noqa: N803
        open_only: bool = False,
    ) -> PrimaryBoto3ModelQuerySet:
        """
        List shards for one Kinesis stream.

        Keyword Args:
            StreamARN: Optional stream ARN.
            StreamName: Optional stream name.
            ExclusiveStartShardId: Optional shard ID after which listing starts.
            MaxResults: Optional maximum number of shards to request per page.
            NextToken: Optional pagination token from a previous list call.
            ShardFilter: Optional AWS shard filter object.
            StreamCreationTimestamp: Optional stream creation timestamp.
            StreamId: Optional reserved stream identifier.
            open_only: When true, keep only shards with no ending sequence number.

        Returns:
            Queryset of listed shard models.

        Side Effects:
            Sessionizes returned shard models onto active manager session.

        Raises:
            ValueError: Stream identity is missing.

        """
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
        from botocraft.services.kinesis import KinesisShard

        args: dict[str, Any] = {
            **self._stream_identity_kwargs(StreamARN=StreamARN, StreamName=StreamName),
            "ExclusiveStartShardId": ExclusiveStartShardId,
            "MaxResults": MaxResults,
            "NextToken": NextToken,
            "ShardFilter": self.serialize(ShardFilter),  # type: ignore[attr-defined]
            "StreamCreationTimestamp": StreamCreationTimestamp,
            "StreamId": StreamId,
        }
        paginator = self.client.get_paginator("list_shards")
        shards: list[KinesisShard] = []
        for page in paginator.paginate(
            **{key: value for key, value in args.items() if value is not None}
        ):
            for payload in page.get("Shards", []):
                shard = KinesisShard(
                    **payload,
                    StreamARN=StreamARN,
                    StreamName=StreamName,
                )
                if (
                    open_only
                    and shard.SequenceNumberRange.EndingSequenceNumber is not None
                ):
                    continue
                shards.append(shard)
        query_set = PrimaryBoto3ModelQuerySet(shards)
        self.sessionize(query_set)  # type: ignore[attr-defined]
        return query_set

    def get(
        self,
        ShardId: str,  # noqa: N803
        *,
        StreamARN: str | None = None,  # noqa: N803
        StreamName: str | None = None,  # noqa: N803
    ) -> KinesisShard | None:
        """
        Get one shard from a Kinesis stream by exact shard ID.

        Args:
            ShardId: Shard identifier to locate.

        Keyword Args:
            StreamARN: Optional stream ARN.
            StreamName: Optional stream name.

        Returns:
            Matching shard model, or ``None`` when not found.

        Raises:
            ValueError: Stream identity is missing.

        """
        for shard in self.list(
            StreamARN=StreamARN,
            StreamName=StreamName,
            open_only=False,
        ):
            if cast("KinesisShard", shard).ShardId == ShardId:
                return cast("KinesisShard", shard)
        return None

    def iterator(  # noqa: PLR0913
        self,
        ShardId: str,  # noqa: N803
        ShardIteratorType: Literal[  # noqa: N803
            "AT_SEQUENCE_NUMBER",
            "AFTER_SEQUENCE_NUMBER",
            "TRIM_HORIZON",
            "LATEST",
            "AT_TIMESTAMP",
        ],
        *,
        StartingSequenceNumber: str | None = None,  # noqa: N803
        StreamARN: str | None = None,  # noqa: N803
        StreamId: str | None = None,  # noqa: N803
        StreamName: str | None = None,  # noqa: N803
        Timestamp: Any | None = None,  # noqa: N803
    ) -> str | None:
        """
        Get a shard iterator for one shard.

        Args:
            ShardId: Shard identifier to initialize.
            ShardIteratorType: Iterator type to request.

        Keyword Args:
            StartingSequenceNumber: Optional starting sequence number.
            StreamARN: Optional stream ARN.
            StreamId: Optional reserved stream identifier.
            StreamName: Optional stream name.
            Timestamp: Optional timestamp for ``AT_TIMESTAMP``.

        Returns:
            Shard iterator string when AWS returns one.

        Raises:
            ValueError: Iterator prerequisites or stream identity are invalid.

        """
        self._validate_iterator_args(
            ShardIteratorType,
            StartingSequenceNumber=StartingSequenceNumber,
            Timestamp=Timestamp,
        )
        args: dict[str, Any] = {
            **self._stream_identity_kwargs(StreamARN=StreamARN, StreamName=StreamName),
            "ShardId": ShardId,
            "ShardIteratorType": ShardIteratorType,
            "StartingSequenceNumber": StartingSequenceNumber,
            "StreamId": StreamId,
            "Timestamp": Timestamp,
        }
        response = self.client.get_shard_iterator(
            **{key: value for key, value in args.items() if value is not None}
        )
        return cast("str | None", response.get("ShardIterator"))


class KinesisStreamManagerMixin(KinesisTagsManagerMixin):
    """
    Handwritten create helper for :py:class:`KinesisStreamManager`.
    """

    #: Boto3 client used by generated Kinesis stream manager.
    client: Any

    def create(self, model: KinesisStream) -> None:
        """
        Create a Kinesis stream from a public Botocraft stream model.

        Args:
            model: Stream model containing create-time configuration.

        Side Effects:
            Creates a stream in AWS Kinesis.

        """
        args: dict[str, Any] = {
            "StreamName": model.StreamName,
            "ShardCount": model.ShardCount,
            "StreamModeDetails": self.serialize(model.StreamModeDetails),  # type: ignore[attr-defined]
            "Tags": self._tag_map(cast("list[Any] | None", model.Tags)),
            "WarmThroughputMiBps": model.WarmThroughputMiBps,
            "MaxRecordSizeInKiB": model.MaxRecordSizeInKiB,
        }
        self.client.create_stream(  # type: ignore[attr-defined]
            **{key: value for key, value in args.items() if value is not None}
        )


class KinesisConsumerManagerMixin(KinesisTagsManagerMixin):
    """
    Handwritten create helper for :py:class:`KinesisConsumerManager`.
    """

    #: Boto3 client used by generated Kinesis consumer manager.
    client: Any

    def create(
        self,
        model: KinesisConsumer,
        StreamId: str | None = None,  # noqa: N803
    ) -> KinesisConsumer | None:
        """
        Register an enhanced fan-out consumer from a public Botocraft model.

        Args:
            model: Consumer model containing registration configuration.

        Keyword Args:
            StreamId: Optional reserved stream identifier accepted by AWS.

        Side Effects:
            Registers a Kinesis consumer in AWS.

        Returns:
            Hydrated public consumer model.

        """
        args: dict[str, Any] = {
            "StreamARN": model.StreamARN,
            "ConsumerName": model.ConsumerName,
            "StreamId": StreamId,
            "Tags": self._tag_map(cast("list[Any] | None", model.Tags)),
        }
        response = self.client.register_stream_consumer(  # type: ignore[attr-defined]
            **{key: value for key, value in args.items() if value is not None}
        )
        from botocraft.services.kinesis import KinesisConsumer

        consumer_payload = cast("dict[str, Any] | None", response.get("Consumer"))
        if consumer_payload is None:
            return None
        wrapper = KinesisConsumer(**consumer_payload)
        self.sessionize(wrapper)  # type: ignore[attr-defined]
        return KinesisResponseHelper(self).consumer_with_tags(
            wrapper,
            stream_arn=model.StreamARN,
        )


class KinesisStreamPoller:
    """
    Eternally ingest records from a Kinesis stream across open shards.

    Args:
        stream: Stream model that owns identity and optional boto3 session.
        shard_iterator_type: Initial iterator type used for newly discovered shards.
        limit: Maximum number of records to request per shard read.
        starting_sequence_number: Optional sequence number used for sequence-based
            iterator types.
        timestamp: Optional timestamp used for ``AT_TIMESTAMP`` iterators.
        poll_interval_seconds: Delay before retry when no records arrive on any
            open shard in one pass.

    """

    #: Stream model used for identity, session, and yielded-record context.
    stream: KinesisStream
    #: Initial iterator type used for newly discovered shards.
    shard_iterator_type: Literal[
        "AT_SEQUENCE_NUMBER",
        "AFTER_SEQUENCE_NUMBER",
        "TRIM_HORIZON",
        "LATEST",
        "AT_TIMESTAMP",
    ]
    #: Maximum number of records to request per shard read.
    limit: int
    #: Optional sequence number used for sequence-based iterator types.
    starting_sequence_number: str | None
    #: Optional timestamp used for ``AT_TIMESTAMP`` iterators.
    timestamp: Any | None
    #: Delay before retry when no records arrive on any open shard in one pass.
    poll_interval_seconds: float

    def __init__(  # noqa: PLR0913
        self,
        stream: KinesisStream,
        *,
        shard_iterator_type: Literal[
            "AT_SEQUENCE_NUMBER",
            "AFTER_SEQUENCE_NUMBER",
            "TRIM_HORIZON",
            "LATEST",
            "AT_TIMESTAMP",
        ] = "LATEST",
        limit: int = 1000,
        starting_sequence_number: str | None = None,
        timestamp: Any | None = None,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        """
        Initialize long-running Kinesis stream poller.

        Args:
            stream: Stream model that owns identity and optional boto3 session.

        Keyword Args:
            shard_iterator_type: Initial iterator type used for newly discovered
                shards.
            limit: Maximum number of records to request per shard read.
            starting_sequence_number: Optional sequence number used for
                sequence-based iterator types.
            timestamp: Optional timestamp used for ``AT_TIMESTAMP`` iterators.
            poll_interval_seconds: Delay before retry when no records arrive on any
                open shard in one pass.

        Raises:
            ValueError: Iterator prerequisites are invalid.

        """
        #: Stream model used for identity, session, and yielded-record context.
        self.stream = stream
        #: Initial iterator type used for newly discovered shards.
        self.shard_iterator_type = shard_iterator_type
        #: Maximum number of records to request per shard read.
        self.limit = limit
        #: Optional sequence number used for sequence-based iterator types.
        self.starting_sequence_number = starting_sequence_number
        #: Optional timestamp used for ``AT_TIMESTAMP`` iterators.
        self.timestamp = timestamp
        #: Delay before retry when no records arrive on any open shard in one pass.
        self.poll_interval_seconds = poll_interval_seconds
        self._validate()

    @property
    def client(self) -> Any:
        """
        Return Kinesis boto3 client bound to stream session when present.

        Returns:
            Boto3 Kinesis client.

        """
        manager = self.stream.objects.using(self.stream.session)
        return manager.client

    @property
    def stream_kwargs(self) -> dict[str, str]:
        """
        Return stable stream identity arguments for boto3 calls.

        Returns:
            Stream identity kwargs using ARN when available, otherwise name.

        Raises:
            ValueError: Stream has neither ARN nor name.

        """
        if self.stream.StreamARN:
            return {"StreamARN": self.stream.StreamARN}
        if self.stream.StreamName:
            return {"StreamName": self.stream.StreamName}
        msg = "KinesisStream must have StreamARN or StreamName before polling."
        raise ValueError(msg)

    def _validate(self) -> None:
        """
        Validate iterator configuration for long-running polling.

        Raises:
            ValueError: Iterator configuration is invalid.

        """
        if self.limit < 1:
            msg = "limit must be at least 1."
            raise ValueError(msg)
        if self.poll_interval_seconds < 0:
            msg = "poll_interval_seconds must be non-negative."
            raise ValueError(msg)
        if self.shard_iterator_type in {
            "AT_SEQUENCE_NUMBER",
            "AFTER_SEQUENCE_NUMBER",
        } and not self.starting_sequence_number:
            msg = (
                "starting_sequence_number is required for "
                f"{self.shard_iterator_type}."
            )
            raise ValueError(msg)
        if self.shard_iterator_type == "AT_TIMESTAMP" and self.timestamp is None:
            msg = "timestamp is required for AT_TIMESTAMP."
            raise ValueError(msg)

    @property
    def shard_manager(self) -> Any:
        """
        Return shard manager bound to stream session.

        Returns:
            Kinesis shard manager using stream session.

        """
        from botocraft.services.kinesis import KinesisShard

        return KinesisShard.objects.using(self.stream.session)

    def _record_from_payload(
        self,
        payload: dict[str, Any],
        *,
        shard_id: str,
    ) -> KinesisRecord:
        """
        Convert raw get-records payload into generated record model.

        Args:
            payload: Raw record payload from boto3.

        Keyword Args:
            shard_id: Shard identifier that produced record.

        Returns:
            Generated record model with stream context attached.

        """
        from botocraft.services.kinesis import KinesisRecord

        record = KinesisRecord(
            **payload,
            StreamARN=self.stream.StreamARN,
            ShardId=shard_id,
        )
        record.set_session(self.stream.session)
        return record

    def poll(self) -> Generator[KinesisRecord, None, None]:
        """
        Eternally ingest records from all open shards in stream.

        Yields:
            Generated Kinesis record models as records arrive.

        """
        shard_iterators: dict[str, str | None] = {}
        while True:
            yielded = False
            for shard in self.shard_manager.list(open_only=True, **self.stream_kwargs):
                iterator = shard_iterators.get(shard.ShardId)
                if iterator is None:
                    iterator = shard.iterator(
                        self.shard_iterator_type,
                        StartingSequenceNumber=self.starting_sequence_number,
                        Timestamp=self.timestamp,
                    )
                if not iterator:
                    continue
                args: dict[str, Any] = {
                    "ShardIterator": iterator,
                    "Limit": self.limit,
                }
                if self.stream.StreamARN:
                    args["StreamARN"] = self.stream.StreamARN
                response = self.client.get_records(**args)
                shard_iterators[shard.ShardId] = cast(
                    "str | None",
                    response.get("NextShardIterator"),
                )
                records = response.get("Records", [])
                if not records:
                    continue
                yielded = True
                for payload in records:
                    yield self._record_from_payload(payload, shard_id=shard.ShardId)
            if not yielded:
                time.sleep(self.poll_interval_seconds)


class KinesisStreamModelMixin:
    """
    Add eternal record-ingest generator to :py:class:`KinesisStream`.
    """

    #: ARN used for stream-scoped polling operations.
    StreamARN: str | None
    #: Stream name used when ARN is not available.
    StreamName: str | None

    def poll(
        self,
        *,
        shard_iterator_type: Literal[
            "AT_SEQUENCE_NUMBER",
            "AFTER_SEQUENCE_NUMBER",
            "TRIM_HORIZON",
            "LATEST",
            "AT_TIMESTAMP",
        ] = "LATEST",
        limit: int = 1000,
        starting_sequence_number: str | None = None,
        timestamp: Any | None = None,
        poll_interval_seconds: float = 1.0,
    ) -> Generator[KinesisRecord, None, None]:
        """
        Eternally poll stream and yield records as they arrive.

        Keyword Args:
            shard_iterator_type: Initial iterator type used for newly discovered
                shards. Default matches tailing new traffic.
            limit: Maximum number of records to request per shard read.
            starting_sequence_number: Optional sequence number used for
                sequence-based iterator types.
            timestamp: Optional timestamp used for ``AT_TIMESTAMP`` iterators.
            poll_interval_seconds: Delay before retry when no records arrive on any
                open shard in one pass.

        Yields:
            Generated Kinesis record models with stream and shard context.

        """
        yield from KinesisStreamPoller(
            cast("KinesisStream", self),
            shard_iterator_type=shard_iterator_type,
            limit=limit,
            starting_sequence_number=starting_sequence_number,
            timestamp=timestamp,
            poll_interval_seconds=poll_interval_seconds,
        ).poll()


def stream_include_tags(
    func: Callable[..., KinesisStream | None],
) -> Callable[..., KinesisStream | None]:
    """
    Enrich a returned Kinesis stream with tags.

    Args:
        func: Generated manager method returning one stream.

    Returns:
        Wrapped manager method returning hydrated stream model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> KinesisStream | None:
        stream = func(self, *args, **kwargs)
        return KinesisResponseHelper(self).stream_with_tags(stream)

    return wrapper


def streams_include_tags(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Enrich listed Kinesis streams with tags.

    Args:
        func: Generated manager method returning stream list.

    Returns:
        Wrapped manager method returning enriched queryset.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        results = func(self, *args, **kwargs)
        return KinesisResponseHelper(self).streams_with_tags(results)

    return wrapper


def consumer_include_tags(
    func: Callable[..., KinesisConsumer | None],
) -> Callable[..., KinesisConsumer | None]:
    """
    Enrich a returned Kinesis consumer with tags.

    Args:
        func: Generated manager method returning one consumer.

    Returns:
        Wrapped manager method returning hydrated consumer model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> KinesisConsumer | None:
        consumer = func(self, *args, **kwargs)
        return KinesisResponseHelper(self).consumer_with_tags(consumer)

    return wrapper


def consumers_include_tags(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Enrich listed Kinesis consumers with tags.

    Args:
        func: Generated manager method returning consumer list.

    Returns:
        Wrapped manager method returning enriched queryset.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        results = func(self, *args, **kwargs)
        return KinesisResponseHelper(self).consumers_with_tags(
            results,
            *args,
            **kwargs,
        )

    return wrapper
