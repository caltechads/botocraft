DataSync day-to-day workflows
=============================

``botocraft`` now provides a handwritten workflow layer for AWS DataSync in
``botocraft.datasync``. This layer wraps generated
``botocraft.services.datasync`` models and managers into cohesive classes for
daily work:

* define sync jobs
* start job runs
* stop active runs
* monitor progress and wait for completion

Use this workflow layer when you want a stable, task-oriented API. Drop down to
the generated service layer when you need the full raw AWS surface.

Workflow layer versus generated service layer
---------------------------------------------

Two DataSync layers now exist:

* ``botocraft.datasync``: handwritten workflow helpers such as
  :py:class:`~botocraft.datasync.DataSyncWorkspace`,
  :py:class:`~botocraft.datasync.DataSyncJobDefinition`, and
  :py:class:`~botocraft.datasync.DataSyncJobRun`
* ``botocraft.services.datasync``: generated AWS models and managers such as
  :py:class:`~botocraft.services.datasync.DataSyncTask`,
  :py:class:`~botocraft.services.datasync.DataSyncTaskExecution`, and
  :py:class:`~botocraft.services.datasync.DataSyncTaskManager`

The generated models remain canonical payload types. You still instantiate
``DataSyncTask``, ``DataSyncLocationS3``, and similar models from the generated
service module. The workflow layer gives you a cleaner orchestration surface on
top of those models.

Imports
-------

Import workflow helpers from ``botocraft.datasync``:

.. code-block:: python

    from botocraft.datasync import DataSyncWorkspace

Import generated DataSync models from ``botocraft.services.datasync``:

.. code-block:: python

    from botocraft.services.common import Tag
    from botocraft.services.datasync import (
        DataSyncAgent,
        DataSyncLocationNfs,
        DataSyncLocationS3,
        DataSyncOnPremConfig,
        DataSyncOptions,
        DataSyncS3Config,
        DataSyncTask,
    )

Create a workspace
------------------

Use :py:class:`~botocraft.datasync.DataSyncWorkspace` as the session-bound
entrypoint for all workflow operations:

.. code-block:: python

    import boto3

    from botocraft.datasync import DataSyncWorkspace

    session = boto3.session.Session(region_name="us-west-2")
    workspace = DataSyncWorkspace(session=session)

The workspace exposes four main areas:

* ``workspace.agents``
* ``workspace.locations``
* ``workspace.tasks``
* ``workspace.executions``

Create an agent
---------------

Use ``workspace.agents`` for CRUD-style agent operations:

.. code-block:: python

    agent = workspace.agents.create(
        DataSyncAgent(
            ActivationKey="ABCDE-ABCDE-ABCDE-ABCDE-ABCDE",
            Name="migration-agent",
            Tags=[Tag(Key="Environment", Value="prod")],
        )
    )

    print(agent.AgentArn)

You can also retrieve or update an existing agent:

.. code-block:: python

    agent = workspace.agents.get("arn:aws:datasync:us-west-2:123456789012:agent/agent-id")
    if agent is None:
        raise RuntimeError("DataSync agent not found")

    agent.Name = "migration-agent-renamed"
    agent = workspace.agents.update(agent)

Create source and destination locations
---------------------------------------

Locations are intentionally explicit and typed. Each subtype has its own
session-bound facade under ``workspace.locations``:

.. code-block:: python

    source = workspace.locations.nfs.create(
        DataSyncLocationNfs(
            ServerHostname="10.0.0.10",
            Subdirectory="/exports/data",
            OnPremConfig=DataSyncOnPremConfig(AgentArns=[agent.AgentArn]),
        )
    )

    destination = workspace.locations.s3.create(
        DataSyncLocationS3(
            S3BucketArn="arn:aws:s3:::example-bucket",
            Subdirectory="/ingest",
            S3Config=DataSyncS3Config(
                BucketAccessRoleArn="arn:aws:iam::123456789012:role/datasync-access"
            ),
        )
    )

Available typed location facades:

* ``workspace.locations.azure_blob``
* ``workspace.locations.efs``
* ``workspace.locations.fsx_lustre``
* ``workspace.locations.fsx_ontap``
* ``workspace.locations.fsx_openzfs``
* ``workspace.locations.fsx_windows``
* ``workspace.locations.hdfs``
* ``workspace.locations.nfs``
* ``workspace.locations.object_storage``
* ``workspace.locations.s3``
* ``workspace.locations.smb``

Define a sync job
-----------------

In this workflow layer, a DataSync task is your job definition. Build a
generated ``DataSyncTask`` model, then hand it to
:py:meth:`~botocraft.datasync.DataSyncWorkspace.define_job`:

.. code-block:: python

    job = workspace.define_job(
        DataSyncTask(
            Name="daily-ingest",
            SourceLocationArn=source.LocationArn,
            DestinationLocationArn=destination.LocationArn,
            Options=DataSyncOptions(
                BytesPerSecond=10485760,
                VerifyMode="ONLY_FILES_TRANSFERRED",
            ),
            Tags=[Tag(Key="Application", Value="warehouse")],
        )
    )

    print(job.arn, job.name)

You can also resolve an existing job definition later:

.. code-block:: python

    job = workspace.job("arn:aws:datasync:us-west-2:123456789012:task/task-id")
    if job is None:
        raise RuntimeError("DataSync task not found")

Refresh, update, or delete a job definition with the wrapper:

.. code-block:: python

    job = job.refresh()
    job.task.Name = "daily-ingest-v2"
    job = job.update()
    # job.delete()

Start a job run
---------------

Call :py:meth:`~botocraft.datasync.DataSyncJobDefinition.start` on a job
definition when you want a new execution:

.. code-block:: python

    run = job.start(
        OverrideOptions=DataSyncOptions(BytesPerSecond=20971520),
        Tags=[Tag(Key="TriggeredBy", Value="botocraft")],
    )

    print(run.arn, run.status)

If you prefer, you can also start from the task facade directly:

.. code-block:: python

    run = workspace.tasks.start(job.task)

Monitor progress
----------------

Use :py:meth:`~botocraft.datasync.DataSyncJobRun.summary`,
:py:meth:`~botocraft.datasync.DataSyncJobRun.progress`, and
:py:meth:`~botocraft.datasync.DataSyncJobRun.wait` for common monitoring
workflows.

One-line summary:

.. code-block:: python

    print(run.summary())

Structured progress snapshot:

.. code-block:: python

    progress = run.progress()
    print(progress.status)
    print(progress.bytes_transferred, progress.estimated_bytes_to_transfer)
    print(progress.files_transferred, progress.files_verified)
    print(progress.error_code, progress.error_detail)

Wait for completion with polling:

.. code-block:: python

    final_run = run.wait(poll_interval_seconds=15, timeout_seconds=3600)
    print(final_run.status)

``wait()`` polls ``describe_task_execution`` until the run reaches a terminal
state. In this first slice, terminal means:

* ``SUCCESS``
* ``ERROR``

``CANCELLING`` is intentionally treated as non-terminal, so ``wait()`` keeps
polling until DataSync fully settles.

Find current or recent runs
---------------------------

When you already have a job definition, use the wrapper helpers:

.. code-block:: python

    latest_run = job.latest_run()
    if latest_run is not None:
        print(latest_run.summary())

Cross-account support (S3 first slice)
--------------------------------------

``botocraft.datasync`` also supports an explicit first slice of cross-account
workflow support for S3-backed transfers. This slice is intentionally narrow:

* one task account owns the DataSync task and its executions
* one source account owns the source location
* one destination account owns the destination location
* source and destination locations must both be S3 when the accounts differ
* each S3 location must include ``BucketAccessRoleArn``
* manifest-backed transfers must also include
  ``ManifestConfig.Source.S3.BucketAccessRoleArn``

Monitoring and lifecycle operations always route through the task account.

Account contexts
----------------

Create named account contexts and pass them into
:py:class:`~botocraft.datasync.DataSyncWorkspace`:

.. code-block:: python

    import boto3

    from botocraft.datasync import (
        DataSyncAccountContext,
        DataSyncWorkspace,
    )

    workspace = DataSyncWorkspace(
        accounts={
            "task": DataSyncAccountContext(
                name="task",
                session=boto3.session.Session(profile_name="datasync-task"),
            ),
            "source": DataSyncAccountContext(
                name="source",
                session=boto3.session.Session(profile_name="source-data"),
            ),
            "destination": DataSyncAccountContext(
                name="destination",
                session=boto3.session.Session(profile_name="destination-data"),
            ),
        }
    )

Use the account-scoped accessors when you need CRUD operations against a
specific account:

* ``workspace.agents_in("task")``
* ``workspace.locations_in("source")``
* ``workspace.locations_in("destination")``
* ``workspace.tasks_in("task")``
* ``workspace.executions_in("task")``

Assume-role setup
-----------------

If you prefer to construct sessions by assuming roles, use
:py:func:`~botocraft.datasync.assume_role_account_context`:

.. code-block:: python

    import boto3

    from botocraft.datasync import assume_role_account_context

    task_account = assume_role_account_context(
        "task",
        "arn:aws:iam::111111111111:role/datasync-task",
        session_name="botocraft-datasync",
        base_session=boto3.session.Session(profile_name="bootstrap"),
    )

Cross-account S3-to-S3 example
------------------------------

The workflow stays explicit about which account owns each resource:

.. code-block:: python

    import boto3

    from botocraft.datasync import (
        DataSyncAccountContext,
        DataSyncCrossAccountSpec,
        DataSyncWorkspace,
    )
    from botocraft.services.datasync import (
        DataSyncLocationS3,
        DataSyncS3Config,
        DataSyncTask,
    )

    workspace = DataSyncWorkspace(
        accounts={
            "task": DataSyncAccountContext(
                name="task",
                session=boto3.session.Session(profile_name="task"),
            ),
            "source": DataSyncAccountContext(
                name="source",
                session=boto3.session.Session(profile_name="source"),
            ),
            "destination": DataSyncAccountContext(
                name="destination",
                session=boto3.session.Session(profile_name="destination"),
            ),
        }
    )

    source = workspace.locations_in("source").s3.create(
        DataSyncLocationS3(
            S3BucketArn="arn:aws:s3:::source-bucket",
            Subdirectory="/exports",
            S3Config=DataSyncS3Config(
                BucketAccessRoleArn="arn:aws:iam::222222222222:role/datasync-source"
            ),
        )
    )

    destination = workspace.locations_in("destination").s3.create(
        DataSyncLocationS3(
            S3BucketArn="arn:aws:s3:::destination-bucket",
            Subdirectory="/imports",
            S3Config=DataSyncS3Config(
                BucketAccessRoleArn="arn:aws:iam::333333333333:role/datasync-destination"
            ),
        )
    )

    spec = DataSyncCrossAccountSpec(
        task_account="task",
        source_account="source",
        destination_account="destination",
    )

    job = workspace.define_cross_account_job(
        DataSyncTask(
            Name="cross-account-s3-copy",
            SourceLocationArn=source.LocationArn,
            DestinationLocationArn=destination.LocationArn,
        ),
        spec=spec,
    )

    run = job.start()
    final_run = run.wait(poll_interval_seconds=15, timeout_seconds=3600)
    print(final_run.summary())

Limitations
-----------

This first slice intentionally does not attempt to infer account ownership from
ARNs or support every DataSync location type across accounts. Non-S3
cross-account location pairs remain unsupported here. The caller is still
responsible for IAM trust policies, bucket policies, and the actual AWS-side
permissions that allow DataSync to assume the configured roles.

    for execution in job.runs():
        print(execution.TaskExecutionArn, execution.Status)

You can also resolve an execution wrapper directly from the workspace:

.. code-block:: python

    run = workspace.run(
        "arn:aws:datasync:us-west-2:123456789012:task/task-id/execution/exec-id"
    )
    if run is not None:
        print(run.summary())

Stop an active run
------------------

Use :py:meth:`~botocraft.datasync.DataSyncJobRun.cancel` to stop an active
execution and refresh it once:

.. code-block:: python

    run = run.cancel()
    print(run.status)

You can also cancel by ARN through the execution facade:

.. code-block:: python

    workspace.executions.cancel(
        "arn:aws:datasync:us-west-2:123456789012:task/task-id/execution/exec-id"
    )

End-to-end example
------------------

This example creates an agent and locations, defines a task, starts it, waits,
and prints the final summary:

.. code-block:: python

    import boto3

    from botocraft.datasync import DataSyncWorkspace
    from botocraft.services.common import Tag
    from botocraft.services.datasync import (
        DataSyncAgent,
        DataSyncLocationNfs,
        DataSyncLocationS3,
        DataSyncOptions,
        DataSyncOnPremConfig,
        DataSyncS3Config,
        DataSyncTask,
    )

    workspace = DataSyncWorkspace(
        session=boto3.session.Session(region_name="us-west-2")
    )

    agent = workspace.agents.create(
        DataSyncAgent(
            ActivationKey="ABCDE-ABCDE-ABCDE-ABCDE-ABCDE",
            Name="migration-agent",
        )
    )

    source = workspace.locations.nfs.create(
        DataSyncLocationNfs(
            ServerHostname="10.0.0.10",
            Subdirectory="/exports/data",
            OnPremConfig=DataSyncOnPremConfig(AgentArns=[agent.AgentArn]),
        )
    )

    destination = workspace.locations.s3.create(
        DataSyncLocationS3(
            S3BucketArn="arn:aws:s3:::example-bucket",
            Subdirectory="/ingest",
            S3Config=DataSyncS3Config(
                BucketAccessRoleArn="arn:aws:iam::123456789012:role/datasync-access"
            ),
        )
    )

    job = workspace.define_job(
        DataSyncTask(
            Name="daily-ingest",
            SourceLocationArn=source.LocationArn,
            DestinationLocationArn=destination.LocationArn,
            Options=DataSyncOptions(VerifyMode="ONLY_FILES_TRANSFERRED"),
            Tags=[Tag(Key="Application", Value="warehouse")],
        )
    )

    run = job.start()
    run = run.wait(poll_interval_seconds=15, timeout_seconds=3600)
    print(run.summary())

Manager versus workflow layer
-----------------------------

Use the workflow layer when:

* you want cohesive define/start/stop/monitor flows
* you already think in terms of jobs and runs
* you want session handling attached to one workspace

Use the generated managers when:

* you need an AWS method not covered by the workflow layer
* you want exact parity with the generated DataSync service surface
* you need lower-level CRUD behavior without workflow wrappers

Examples:

* workflow layer:
  ``DataSyncWorkspace.define_job(...)`` and ``DataSyncJobRun.wait()``
* generated layer:
  :py:meth:`botocraft.services.datasync.DataSyncTaskManager.start_task_execution`
  and
  :py:meth:`botocraft.services.datasync.DataSyncTaskExecutionManager.cancel`

For the full generated DataSync API surface, see :doc:`/api/services/datasync`.
