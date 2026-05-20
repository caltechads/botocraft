ECS Exec
========

:py:class:`~botocraft.services.ecs.Service` and :py:class:`~botocraft.services.ecs.Task`
expose :py:meth:`~botocraft.mixins.ecs.ECSExecMixin.exec` to open an interactive shell
in a running container through `ECS Exec <https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-exec.html>`_.

Botocraft runs the local `AWS CLI v2 <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>`_
``execute-command`` subcommand and forwards Control-C to the remote session so the
caller does not exit while the ECS Exec session keeps running.

Prerequisites
-------------

ECS Exec must already be enabled for the cluster, task definition, service, and caller
IAM principal as described in the AWS documentation. The machine running botocraft also
needs:

* a current AWS CLI v2 with ``aws ecs execute-command`` available
* the `Session Manager plugin <https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html>`_
* credentials for the same profile botocraft uses on the model's session

Service example
---------------

Exec into the first running task and first container:

.. code-block:: python

    from botocraft.services.ecs import Service

    service = Service.objects.get(
        cluster="my-cluster",
        service="my-service",
    )
    service.exec()

Pick a specific task and container when several are running:

.. code-block:: python

    tasks = service.running_tasks
    service.exec(
        task_arn=tasks[1].taskArn,
        container_name=tasks[1].containers[1].name,
    )

Task example
------------

Exec into a single task you already fetched:

.. code-block:: python

    from botocraft.services.ecs import Task

    task = Task.objects.get(
        cluster="my-cluster",
        task="arn:aws:ecs:us-west-2:123456789012:task/my-cluster/abc123",
    )
    task.exec()

Failure modes
-------------

* :py:exc:`~botocraft.mixins.ecs.ECSExecMixin.NoRunningTasks` when no ``RUNNING`` tasks
  are available on the service or the task is not running
* :py:exc:`ValueError` when the requested task or container name cannot be resolved
* :py:exc:`RuntimeError` when the AWS CLI is missing or does not expose ECS Exec

See also :doc:`/overview/connectivity` for tunnel-aware connections to private RDS,
ElastiCache, and DocumentDB endpoints.
