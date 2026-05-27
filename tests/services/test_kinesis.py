from __future__ import annotations

from collections import OrderedDict
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.kinesis import (
    KinesisShard,
    KinesisShardManager,
    KinesisStream,
    KinesisStreamModeDetails,
)


class FakePaginator:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def paginate(self, **kwargs: object) -> list[dict[str, object]]:
        self.calls.append(dict(kwargs))
        return self.responses


class FakeShardClient:
    def __init__(
        self,
        *,
        pages: list[dict[str, object]] | None = None,
        iterator: str = "iterator-123",
    ) -> None:
        self.paginator = FakePaginator(pages or [])
        self.get_shard_iterator = MagicMock(return_value={"ShardIterator": iterator})

    def get_paginator(self, name: str) -> FakePaginator:
        assert name == "list_shards"
        return self.paginator


def make_manager(client: FakeShardClient) -> KinesisShardManager:
    manager = KinesisShardManager.__new__(KinesisShardManager)
    manager.client = client
    manager.session = None
    return manager


def shard_payload(
    shard_id: str,
    *,
    ending_sequence_number: str | None = None,
) -> dict[str, Any]:
    return {
        "ShardId": shard_id,
        "HashKeyRange": {
            "StartingHashKey": "0",
            "EndingHashKey": "100",
        },
        "SequenceNumberRange": {
            "StartingSequenceNumber": "1",
            "EndingSequenceNumber": ending_sequence_number,
        },
    }


class TestKinesisShardManager:
    def test_list_filters_open_only_and_backfills_stream_identity(self) -> None:
        client = FakeShardClient(
            pages=[
                {
                    "Shards": [
                        shard_payload("shard-0001"),
                        shard_payload("shard-0002", ending_sequence_number="99"),
                    ]
                }
            ]
        )
        manager = make_manager(client)

        all_shards = manager.list(StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo")
        open_shards = manager.list(
            StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
            open_only=True,
        )

        assert isinstance(all_shards, PrimaryBoto3ModelQuerySet)
        assert [shard.ShardId for shard in all_shards] == ["shard-0001", "shard-0002"]
        assert [shard.StreamARN for shard in all_shards] == [
            "arn:aws:kinesis:us-west-2:123:stream/demo",
            "arn:aws:kinesis:us-west-2:123:stream/demo",
        ]
        assert isinstance(open_shards, PrimaryBoto3ModelQuerySet)
        assert [shard.ShardId for shard in open_shards] == ["shard-0001"]
        assert client.paginator.calls == [
            {"StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo"},
            {"StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo"},
        ]

    def test_get_returns_matching_shard_or_none(self) -> None:
        client = FakeShardClient(
            pages=[
                {
                    "Shards": [
                        shard_payload("shard-0001"),
                        shard_payload("shard-0002", ending_sequence_number="99"),
                    ]
                }
            ]
        )
        manager = make_manager(client)

        loaded = manager.get("shard-0002", StreamName="demo")
        missing = manager.get("shard-missing", StreamName="demo")

        assert loaded is not None
        assert loaded.ShardId == "shard-0002"
        assert loaded.StreamName == "demo"
        assert missing is None

    def test_iterator_validates_and_calls_client(self) -> None:
        client = FakeShardClient()
        manager = make_manager(client)

        with pytest.raises(ValueError, match="starting_sequence_number"):
            manager.iterator(
                "shard-0001",
                "AFTER_SEQUENCE_NUMBER",
                StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
            )

        with pytest.raises(ValueError, match="timestamp"):
            manager.iterator(
                "shard-0001",
                "AT_TIMESTAMP",
                StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
            )

        iterator = manager.iterator(
            "shard-0001",
            "LATEST",
            StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
        )

        assert iterator == "iterator-123"
        client.get_shard_iterator.assert_called_once_with(
            ShardId="shard-0001",
            ShardIteratorType="LATEST",
            StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
        )


class ShardRelationManager:
    last_instance: ShardRelationManager | None = None

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        ShardRelationManager.last_instance = self

    def using(self, _session: object) -> ShardRelationManager:
        return self

    def list(self, **kwargs: object) -> PrimaryBoto3ModelQuerySet:
        self.calls.append(kwargs)
        return PrimaryBoto3ModelQuerySet([])


class StreamShortcutManager:
    last_instance: StreamShortcutManager | None = None
    calls: ClassVar[list[tuple[str, tuple[object, ...], dict[str, object]]]] = []

    def __init__(self) -> None:
        StreamShortcutManager.last_instance = self

    def using(self, _session: object) -> StreamShortcutManager:
        return self

    def update_shard_count(
        self,
        target_shard_count: int,
        scaling_type: str,
        **kwargs: object,
    ) -> str:
        self.__class__.calls.append(
            (
                "update_shard_count",
                (target_shard_count, scaling_type),
                dict(kwargs),
            )
        )
        return "updated-shards"

    def update_stream_mode(
        self,
        stream_mode_details: object,
        **kwargs: object,
    ) -> None:
        self.__class__.calls.append(
            (
                "update_stream_mode",
                (stream_mode_details,),
                dict(kwargs),
            )
        )

    def update_stream_warm_throughput(
        self,
        warm_throughput_mi_bps: int,
        **kwargs: object,
    ) -> str:
        self.__class__.calls.append(
            (
                "update_stream_warm_throughput",
                (warm_throughput_mi_bps,),
                dict(kwargs),
            )
        )
        return "warm"

    def update_max_record_size(
        self,
        max_record_size_in_ki_b: int,
        **kwargs: object,
    ) -> None:
        self.__class__.calls.append(
            (
                "update_max_record_size",
                (max_record_size_in_ki_b,),
                dict(kwargs),
            )
        )


class PollerStreamManager:
    last_instance: PollerStreamManager | None = None

    def __init__(self) -> None:
        self.client = MagicMock()
        self.client.get_records.return_value = {
            "NextShardIterator": "next-iterator",
            "Records": [
                {
                    "SequenceNumber": "1",
                    "Data": b"payload",
                    "PartitionKey": "pk",
                }
            ],
        }
        PollerStreamManager.last_instance = self

    def using(self, _session: object) -> PollerStreamManager:
        return self


class PollerShardManager:
    last_instance: PollerShardManager | None = None

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        PollerShardManager.last_instance = self

    def using(self, _session: object) -> PollerShardManager:
        return self

    def list(self, **kwargs: object) -> PrimaryBoto3ModelQuerySet:
        self.calls.append(kwargs)
        shard = KinesisShard(
            ShardId="shard-0001",
            HashKeyRange={"StartingHashKey": "0", "EndingHashKey": "100"},
            SequenceNumberRange={"StartingSequenceNumber": "1"},
            StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
        )
        return PrimaryBoto3ModelQuerySet([shard])


class TestKinesisStreamErgonomics:
    def test_stream_relations_and_shortcuts_use_stream_arn(self) -> None:
        stream = KinesisStream(
            StreamName="demo",
            StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
            StreamStatus="ACTIVE",
        )
        StreamShortcutManager.calls = []

        with (
            patch.object(KinesisShard, "manager_class", ShardRelationManager),
            patch.object(KinesisStream, "manager_class", StreamShortcutManager),
        ):
            shards = stream.shards
            assert isinstance(shards, PrimaryBoto3ModelQuerySet)
            assert list(shards) == []

            details = KinesisStreamModeDetails(StreamMode="ON_DEMAND")
            stream.update_shard_count(4, "UNIFORM_SCALING")
            stream.update_stream_mode(details, WarmThroughputMiBps=256)
            stream.update_stream_warm_throughput(512)
            stream.update_max_record_size(2048)

        assert ShardRelationManager.last_instance is not None
        assert ShardRelationManager.last_instance.calls == [
            {"StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo"}
        ]
        assert StreamShortcutManager.calls == [
            (
                "update_shard_count",
                (4, "UNIFORM_SCALING"),
                {"StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo"},
            ),
            (
                "update_stream_mode",
                (details,),
                {
                    "StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo",
                    "WarmThroughputMiBps": 256,
                },
            ),
            (
                "update_stream_warm_throughput",
                (512,),
                {"StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo"},
            ),
            (
                "update_max_record_size",
                (2048,),
                {"StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo"},
            ),
        ]


class TestKinesisStreamPoller:
    def test_poller_uses_shard_manager_open_only_and_shard_iterator(self) -> None:
        from botocraft.mixins.kinesis import KinesisStreamPoller

        stream = KinesisStream(
            StreamName="demo",
            StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
            StreamStatus="ACTIVE",
        )

        with (
            patch.object(KinesisStream, "manager_class", PollerStreamManager),
            patch.object(KinesisShard, "manager_class", PollerShardManager),
            patch.object(
                KinesisShard,
                "iterator",
                return_value="iterator-123",
                create=True,
            ) as iterator_mock,
        ):
            poller = KinesisStreamPoller(stream, limit=25)
            record = next(poller.poll())

        assert PollerShardManager.last_instance is not None
        assert PollerShardManager.last_instance.calls == [
            {
                "StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo",
                "open_only": True,
            }
        ]
        iterator_mock.assert_called_once_with(
            "LATEST",
            StartingSequenceNumber=None,
            Timestamp=None,
        )
        assert record.ShardId == "shard-0001"
        assert PollerStreamManager.last_instance is not None
        PollerStreamManager.last_instance.client.get_records.assert_called_once_with(
            ShardIterator="iterator-123",
            Limit=25,
            StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
        )


def test_kinesis_shard_pk_is_stream_scoped_ordered_dict() -> None:
    shard = KinesisShard(
        ShardId="shard-0001",
        HashKeyRange={"StartingHashKey": "0", "EndingHashKey": "100"},
        SequenceNumberRange={"StartingSequenceNumber": "1"},
        StreamARN="arn:aws:kinesis:us-west-2:123:stream/demo",
        StreamName="demo",
    )

    assert shard.pk == OrderedDict(
        {
            "StreamARN": "arn:aws:kinesis:us-west-2:123:stream/demo",
            "ShardId": "shard-0001",
        }
    )
