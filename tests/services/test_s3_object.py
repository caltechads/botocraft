import io
from unittest.mock import MagicMock

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from botocraft.services.s3 import GetObjectOutput, S3Object, S3ObjectManager

BUCKET = "example-bucket"
KEY = "path/to/key"


def _body(data: bytes) -> tuple[StreamingBody, io.BytesIO]:
    raw = io.BytesIO(data)
    return StreamingBody(raw, len(data)), raw


@pytest.fixture
def s3():
    client = boto3.client(
        "s3",
        region_name="us-west-2",
        aws_access_key_id="FAKEACCESSKEY",
        aws_secret_access_key="fake-secret",  # noqa: S106
    )
    with Stubber(client) as stubber:
        yield client, stubber
    stubber.assert_no_pending_responses()


@pytest.fixture
def session(s3):
    mock = MagicMock()
    mock.client.return_value = s3[0]
    return mock


@pytest.fixture
def manager(s3, session) -> S3ObjectManager:
    manager = S3ObjectManager.__new__(S3ObjectManager)
    manager.client = s3[0]
    manager.session = session
    return manager


def test_get_then_contents(s3, manager) -> None:
    _, stubber = s3
    stubber.add_response("get_object", {"ContentLength": 5})
    body, _raw = _body(b"hello")
    stubber.add_response(
        "get_object",
        {"Body": body, "ContentLength": 5},
        {"Bucket": BUCKET, "Key": KEY},
    )

    obj = manager.get(BUCKET, KEY)

    assert isinstance(obj, S3Object)
    assert (obj.BucketName, obj.Key) == (BUCKET, KEY)
    contents = obj.contents()
    assert isinstance(contents, GetObjectOutput)
    assert contents.Body.read() == b"hello"


def test_get_accepts_keyword_arguments(s3, manager) -> None:
    _, stubber = s3
    stubber.add_response("get_object", {})

    obj = manager.get(Key=KEY, Bucket=BUCKET)

    assert (obj.BucketName, obj.Key) == (BUCKET, KEY)


def test_list_then_contents(s3, manager) -> None:
    _, stubber = s3
    stubber.add_response(
        "list_objects_v2",
        {"Contents": [{"Key": KEY}], "IsTruncated": False, "KeyCount": 1},
        {"Bucket": BUCKET, "Prefix": "path/"},
    )
    body, _raw = _body(b"listed")
    stubber.add_response("get_object", {"Body": body}, {"Bucket": BUCKET, "Key": KEY})

    (obj,) = manager.list(BUCKET, Prefix="path/").results

    assert (obj.BucketName, obj.Key) == (BUCKET, KEY)
    assert obj.contents().Body.read() == b"listed"


def test_list_with_keyword_bucket(s3, manager) -> None:
    _, stubber = s3
    stubber.add_response(
        "list_objects_v2",
        {"Contents": [{"Key": KEY}], "IsTruncated": False, "KeyCount": 1},
        {"Bucket": BUCKET},
    )

    (obj,) = manager.list(Bucket=BUCKET).results

    assert obj.BucketName == BUCKET


def test_create_returns_object_with_bucket_and_key(s3, manager) -> None:
    _, stubber = s3
    stubber.add_response("put_object", {"ETag": '"abc"'})
    model = S3Object(Key=KEY)

    created = manager.create(model, BUCKET)

    assert isinstance(created, S3Object)
    assert (created.BucketName, created.Key) == (BUCKET, KEY)


def test_contents_on_hand_built_object(s3, session) -> None:
    _, stubber = s3
    body, _raw = _body(b"manual")
    stubber.add_response("get_object", {"Body": body}, {"Bucket": BUCKET, "Key": KEY})
    obj = S3Object(BucketName=BUCKET, Key=KEY)
    obj.set_session(session)

    assert obj.contents().Body.read() == b"manual"


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"BucketName": None, "Key": KEY}, "BucketName"),
        ({"BucketName": BUCKET, "Key": None}, "Key"),
    ],
)
def test_contents_without_required_field_raises_named_error(
    session, kwargs, field
) -> None:
    obj = S3Object(**kwargs)
    obj.set_session(session)

    with pytest.raises(ValueError, match=field):
        obj.contents()


def test_body_is_streaming_body_and_unread_until_caller_reads(s3, session) -> None:
    _, stubber = s3
    body, raw = _body(b"lazy")
    stubber.add_response("get_object", {"Body": body})
    obj = S3Object(BucketName=BUCKET, Key=KEY)
    obj.set_session(session)

    contents = obj.contents()

    assert isinstance(contents.Body, StreamingBody)
    assert raw.tell() == 0
    assert contents.Body.read() == b"lazy"
    assert raw.tell() == 4


def test_get_does_not_keep_the_body(s3, manager) -> None:
    _, stubber = s3
    body, raw = _body(b"lazy")
    stubber.add_response("get_object", {"Body": body})

    obj = manager.get(BUCKET, KEY)

    assert not hasattr(obj, "Body")
    assert raw.tell() == 0
