"""Tests for Amplify manual deploy, job hydration, and tag updates."""

import inspect
from datetime import datetime, timezone
from email.message import Message
from typing import cast
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

# ruff: isort: off
import botocraft.services.amplify as amplify_service
from botocraft.services.amplify import AmplifyBranch, Job
from botocraft.mixins.amplify import (
    AmplifyAppManagerMixin,
    AmplifyBranchManagerMixin,
    AmplifyJobManagerMixin,
    _page,
    amplify_stamp_app_id,
    amplify_sync_tags,
)
# ruff: isort: on


def _when() -> datetime:
    """Return a fixed timestamp for job payloads."""
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def _job_payload(job_id: str = "1") -> dict[str, object]:
    """Return a GetJob ``job`` payload with one step."""
    moment = _when()
    return {
        "summary": {
            "jobArn": f"arn:aws:amplify:us-west-2:123:apps/d1/branches/main/jobs/{job_id}",
            "jobId": job_id,
            "commitId": "abc",
            "commitMessage": "manual",
            "commitTime": moment,
            "startTime": moment,
            "status": "SUCCEED",
            "jobType": "MANUAL",
        },
        "steps": [
            {
                "stepName": "DEPLOY",
                "startTime": moment,
                "status": "SUCCEED",
                "endTime": moment,
                "logUrl": "https://logs.example/1",
            }
        ],
    }


def _branch_manager() -> AmplifyBranchManagerMixin:
    """Return a mixin with a mock client and sessionize."""
    manager = AmplifyBranchManagerMixin()
    manager.client = MagicMock()
    manager.sessionize = MagicMock()  # type: ignore[attr-defined]
    return manager


def test_deploy_zip_uploads_then_starts(tmp_path) -> None:
    """A local zip is PUT, then StartDeployment, then the full job comes back."""
    zip_path = tmp_path / "site.zip"
    zip_path.write_bytes(b"PK\x03\x04")
    manager = _branch_manager()
    manager.client.create_deployment.return_value = {
        "jobId": "1",
        "zipUploadUrl": "https://upload.example/zip",
    }
    manager.client.get_job.return_value = {"job": _job_payload()}

    with patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = b""
        job = manager.deploy_zip("d1", "main", zip_path)

    request = urlopen.call_args.args[0]
    assert request.method == "PUT"
    assert request.data == b"PK\x03\x04"
    manager.client.start_deployment.assert_called_once_with(
        appId="d1",
        branchName="main",
        jobId="1",
    )
    assert job.appId == "d1"
    assert job.branchName == "main"
    assert job.steps[0].stepName == "DEPLOY"
    assert job.steps[0].logUrl == "https://logs.example/1"


def test_deploy_zip_does_not_start_when_upload_fails(tmp_path) -> None:
    """A failed PUT must not call StartDeployment."""
    zip_path = tmp_path / "site.zip"
    zip_path.write_bytes(b"PK")
    manager = _branch_manager()
    manager.client.create_deployment.return_value = {
        "jobId": "1",
        "zipUploadUrl": "https://upload.example/zip",
    }

    with patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen:
        urlopen.side_effect = HTTPError(
            "https://upload.example/zip",
            403,
            "Forbidden",
            Message(),
            None,
        )
        with pytest.raises(HTTPError):
            manager.deploy_zip("d1", "main", zip_path)

    manager.client.start_deployment.assert_not_called()
    manager.client.get_job.assert_not_called()


def test_deploy_zip_rejects_missing_upload_url(tmp_path) -> None:
    """No upload URL means no PUT and no StartDeployment."""
    manager = _branch_manager()
    manager.client.create_deployment.return_value = {"jobId": "1"}

    with (
        patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen,
        pytest.raises(ValueError, match="zip upload URL"),
    ):
        manager.deploy_zip("d1", "main", tmp_path / "missing.zip")

    urlopen.assert_not_called()
    manager.client.start_deployment.assert_not_called()


def test_job_list_hydrates_steps() -> None:
    """ListJobs summaries are replaced by GetJob payloads."""
    manager = AmplifyJobManagerMixin()
    manager.client = MagicMock()
    manager.sessionize = MagicMock()  # type: ignore[attr-defined]
    paginator = MagicMock()
    paginator.paginate.return_value = [{"jobSummaries": [{"jobId": "9"}]}]
    manager.client.get_paginator.return_value = paginator
    manager.client.get_job.return_value = {"job": _job_payload("9")}

    jobs = [cast("Job", job) for job in manager.list("d1", "main")]

    manager.client.get_job.assert_called_once_with(
        appId="d1",
        branchName="main",
        jobId="9",
    )
    assert jobs[0].summary.status == "SUCCEED"
    assert jobs[0].steps[0].stepName == "DEPLOY"
    assert jobs[0].appId == "d1"
    assert jobs[0].branchName == "main"


def test_page_stops_on_repeated_token() -> None:
    """A repeated nextToken does not spin."""
    client = MagicMock()
    client.list_webhooks.side_effect = [
        {"webhooks": [{"webhookId": "a"}], "nextToken": "again"},
        {"webhooks": [{"webhookId": "b"}], "nextToken": "again"},
    ]

    pages = _page(client, "list_webhooks", "webhooks", appId="d1")

    assert [item["webhookId"] for item in pages] == ["a", "b"]
    assert client.list_webhooks.call_count == 2


def test_sync_tags_skips_unset_tags() -> None:
    """Update does not call tag_resource unless the caller set Tags."""
    manager = MagicMock()
    model = MagicMock()
    model.Tags = {"env": "prod"}
    model.model_fields_set = set()
    result = MagicMock(appArn="arn:aws:amplify:app", branchArn=None)

    def update(_self, _model, *_args, **_kwargs):
        return result

    assert amplify_sync_tags(update)(manager, model) is result
    manager.client.tag_resource.assert_not_called()

    model.model_fields_set = {"Tags"}
    amplify_sync_tags(update)(manager, model)
    manager.client.tag_resource.assert_called_once_with(
        resourceArn="arn:aws:amplify:app",
        tags={"env": "prod"},
    )
    assert result.Tags == {"env": "prod"}


def test_stamp_app_id_from_positional_arg() -> None:
    """Branch results gain the app id the caller passed in."""

    class Item:
        appId = None

    def get(_self, _app_id: str, _branch_name: str) -> Item:
        return Item()

    item = amplify_stamp_app_id(get)(object(), "d1", "main")
    assert item.appId == "d1"


def test_service_imports() -> None:
    """Generated Amplify classes import, and build APIs stay absent."""
    assert amplify_service.App.__name__ == "App"
    assert amplify_service.AmplifyBranch.__name__ == "AmplifyBranch"
    assert "start_job" not in amplify_service.JobManager.__dict__
    assert "stop_job" not in amplify_service.JobManager.__dict__
    assert "steps" in Job.model_fields
    create_parameters = inspect.signature(amplify_service.AppManager.create).parameters
    assert "model" not in create_parameters
    assert "kwargs" in create_parameters
    assert isinstance(amplify_service.AmplifyBranch.active_job, property)


def _input_shape(members: list[str], required: list[str]) -> MagicMock:
    """Return a botocore-like input shape."""
    shape = MagicMock()
    shape.members = dict.fromkeys(members)
    shape.required_members = required
    return shape


def _app_manager() -> AmplifyAppManagerMixin:
    """Return an app mixin with a mock client and sessionize."""
    manager = AmplifyAppManagerMixin()
    manager.client = MagicMock()
    manager.sessionize = MagicMock()  # type: ignore[attr-defined]
    shape = _input_shape(
        ["name", "platform", "enableBasicAuth", "tags"],
        ["name"],
    )
    manager.client.meta.service_model.operation_model.return_value.input_shape = shape
    return manager


def _app_payload() -> dict[str, object]:
    """Return a CreateApp response ``app`` payload."""
    moment = _when()
    return {
        "appId": "d1",
        "appArn": "arn:aws:amplify:us-west-2:123:apps/d1",
        "name": "site",
        "description": "site",
        "repository": "https://example.com/site.git",
        "platform": "WEB",
        "createTime": moment,
        "updateTime": moment,
        "environmentVariables": {},
        "defaultDomain": "d1.amplifyapp.com",
        "enableBranchAutoBuild": True,
        "enableBasicAuth": False,
    }


def _branch_payload() -> dict[str, object]:
    """Return a CreateBranch response ``branch`` payload."""
    moment = _when()
    return {
        "branchArn": "arn:aws:amplify:us-west-2:123:apps/d1/branches/main",
        "branchName": "main",
        "description": "main",
        "stage": "PRODUCTION",
        "displayName": "main",
        "enableNotification": False,
        "createTime": moment,
        "updateTime": moment,
        "environmentVariables": {},
        "enableAutoBuild": False,
        "customDomains": [],
        "framework": "React",
        "activeJobId": "1",
        "totalNumberOfJobs": "1",
        "enableBasicAuth": False,
        "ttl": "5",
        "enablePullRequestPreview": False,
    }


def test_create_app_sends_request_fields_only() -> None:
    """CreateApp receives boto inputs, including false, and no response fields."""
    manager = _app_manager()
    manager.client.create_app.return_value = {"app": _app_payload()}

    app = manager.create(name="site", platform="WEB", enableBasicAuth=False)

    manager.client.create_app.assert_called_once_with(
        name="site",
        platform="WEB",
        enableBasicAuth=False,
    )
    assert app.appId == "d1"
    manager.sessionize.assert_called_once()  # type: ignore[attr-defined]


def test_create_app_rejects_unknown_or_missing_fields() -> None:
    """Response fields and omitted required fields never reach AWS."""
    manager = _app_manager()

    with pytest.raises(TypeError, match="appId"):
        manager.create(name="site", appId="d1")
    with pytest.raises(TypeError, match="name"):
        manager.create(platform="WEB")

    manager.client.create_app.assert_not_called()


def test_create_branch_stamps_app_id() -> None:
    """A created branch keeps the app id used to create it."""
    manager = _branch_manager()
    shape = _input_shape(["appId", "branchName"], ["appId", "branchName"])
    manager.client.meta.service_model.operation_model.return_value.input_shape = shape
    manager.client.create_branch.return_value = {"branch": _branch_payload()}

    branch = manager.create(appId="d1", branchName="main")

    manager.client.create_branch.assert_called_once_with(appId="d1", branchName="main")
    assert branch.appId == "d1"
    assert branch.branchName == "main"


def test_wait_polls_until_terminal() -> None:
    """A running job is read again until the status is terminal."""
    pending = _job_payload()
    pending["summary"]["status"] = "RUNNING"  # type: ignore[index]
    job = Job(**pending)
    job.appId = "d1"
    job.branchName = "main"
    done = Job(**_job_payload())

    with (
        patch.object(Job, "objects") as objects,
        patch("botocraft.mixins.amplify.time.sleep") as sleep,
    ):
        objects.using.return_value.get.return_value = done
        result = job.wait(timeout=30, interval=2)

    assert result.summary.status == "SUCCEED"
    sleep.assert_called_once_with(2)
    objects.using.return_value.get.assert_called_once_with("d1", "main", "1")


def test_wait_requires_scope() -> None:
    """A job without an app id is not polled."""
    job = Job(**_job_payload())

    with pytest.raises(ValueError, match="appId"):
        job.wait()


def test_wait_raises_when_job_disappears() -> None:
    """A missing follow-up read fails instead of waiting out the timeout."""
    pending = _job_payload()
    pending["summary"]["status"] = "RUNNING"  # type: ignore[index]
    job = Job(**pending)
    job.appId = "d1"
    job.branchName = "main"

    with (
        patch.object(Job, "objects") as objects,
        patch("botocraft.mixins.amplify.time.sleep"),
    ):
        objects.using.return_value.get.return_value = None
        with pytest.raises(ValueError, match="disappeared"):
            job.wait(timeout=30, interval=1)


def test_wait_times_out_while_running() -> None:
    """A job that stays RUNNING raises TimeoutError."""
    pending = _job_payload()
    pending["summary"]["status"] = "RUNNING"  # type: ignore[index]
    job = Job(**pending)
    job.appId = "d1"
    job.branchName = "main"
    clock = {"now": 0.0}

    def monotonic() -> float:
        return clock["now"]

    def sleep(_interval: float) -> None:
        clock["now"] = 50.0

    with (
        patch.object(Job, "objects") as objects,
        patch("botocraft.mixins.amplify.time.monotonic", monotonic),
        patch("botocraft.mixins.amplify.time.sleep", sleep),
    ):
        objects.using.return_value.get.return_value = Job(**pending)
        with pytest.raises(TimeoutError, match="RUNNING"):
            job.wait(timeout=10, interval=1)

    objects.using.return_value.get.assert_called_once()


def test_deploy_zip_wait_returns_terminal_job(tmp_path) -> None:
    """wait=True keeps reading until the deploy job finishes."""
    zip_path = tmp_path / "site.zip"
    zip_path.write_bytes(b"PK\x03\x04")
    manager = _branch_manager()
    manager.client.create_deployment.return_value = {
        "jobId": "1",
        "zipUploadUrl": "https://upload.example/zip",
    }
    pending = _job_payload()
    pending["summary"]["status"] = "PENDING"  # type: ignore[index]
    manager.client.get_job.return_value = {"job": pending}
    done = Job(**_job_payload())

    with (
        patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen,
        patch.object(Job, "objects") as objects,
        patch("botocraft.mixins.amplify.time.sleep"),
    ):
        urlopen.return_value.__enter__.return_value.read.return_value = b""
        objects.using.return_value.get.return_value = done
        job = manager.deploy_zip("d1", "main", zip_path, wait=True, interval=3)

    assert job.summary.status == "SUCCEED"
    objects.using.return_value.get.assert_called_once_with("d1", "main", "1")


def test_job_log_text_reads_failed_step_only() -> None:
    """One failed step is downloaded, and earlier step logs are left alone."""
    payload = _job_payload()
    moment = _when()
    payload["steps"] = [
        {
            "stepName": "BUILD",
            "startTime": moment,
            "status": "SUCCEED",
            "endTime": moment,
            "logUrl": "https://logs.example/build",
        },
        {
            "stepName": "DEPLOY",
            "startTime": moment,
            "status": "FAILED",
            "endTime": moment,
            "logUrl": "https://logs.example/fail",
        },
    ]
    job = Job(**payload)

    with patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = b"boom"
        text = job.log_text()

    assert text == "boom"
    request = urlopen.call_args.args[0]
    assert request.full_url == "https://logs.example/fail"
    assert urlopen.call_count == 1


def test_job_log_text_uses_latest_step_when_none_failed() -> None:
    """A successful job downloads the latest step log, not every step."""
    payload = _job_payload()
    moment = _when()
    payload["steps"] = [
        {
            "stepName": "BUILD",
            "startTime": moment,
            "status": "SUCCEED",
            "endTime": moment,
            "logUrl": "https://logs.example/old",
        },
        {
            "stepName": "DEPLOY",
            "startTime": moment,
            "status": "SUCCEED",
            "endTime": moment,
            "logUrl": "https://logs.example/new",
        },
    ]
    job = Job(**payload)

    with patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = b"ok"
        text = job.log_text()

    assert text == "ok"
    assert urlopen.call_args.args[0].full_url == "https://logs.example/new"
    assert urlopen.call_count == 1


def test_job_log_text_requires_a_url() -> None:
    """A job whose steps have no log URL does not call the network."""
    payload = _job_payload()
    payload["steps"][0]["logUrl"] = None  # type: ignore[index]
    job = Job(**payload)

    with (
        patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen,
        pytest.raises(ValueError, match="job has no step log URL"),
    ):
        job.log_text()

    urlopen.assert_not_called()


def test_step_log_text_requires_url() -> None:
    """A step with no log URL does not call the network."""
    job = Job(**_job_payload())
    job.steps[0].logUrl = None

    with (
        patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen,
        pytest.raises(ValueError, match="step has no log URL"),
    ):
        job.steps[0].log_text()

    urlopen.assert_not_called()


def test_access_log_text_downloads_generated_url() -> None:
    """Access log text is the body behind the generated URL."""
    manager = AmplifyAppManagerMixin()
    manager.generate_access_logs = MagicMock(return_value="https://logs.example/access")  # type: ignore[attr-defined]

    with patch("botocraft.mixins.amplify.urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = b"csv-row"
        text = manager.access_log_text("example.com", "d1", startTime=_when())

    assert text == "csv-row"
    manager.generate_access_logs.assert_called_once_with(  # type: ignore[attr-defined]
        "example.com",
        "d1",
        startTime=_when(),
    )
    assert urlopen.call_args.args[0].full_url == "https://logs.example/access"


def test_active_job_uses_stamped_app_id() -> None:
    """active_job loads Job with the stamped app id and activeJobId."""
    payload = _branch_payload()
    payload["activeJobId"] = "9"
    branch = AmplifyBranch(**payload)
    branch.appId = "d1"
    done = Job(**_job_payload())

    with patch.object(Job, "objects") as objects:
        objects.using.return_value.get.return_value = done
        found = branch.active_job

    assert found is done
    objects.using.return_value.get.assert_called_once_with(
        appId="d1",
        branchName="main",
        jobId="9",
    )
