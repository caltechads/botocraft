Tunnel-Aware Connectivity
=========================

``botocraft`` can now resolve connection targets for selected private AWS
resources without forcing callers to care whether they are running inside or
outside AWS.

Supported resources
-------------------

Auto-resolved managed resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following models expose ``open_connection_target()`` and automatically
find a tagged tunnel host instance in the target VPC when tunneling is
required:

* ``botocraft.services.rds.DBInstance``
* ``botocraft.services.elasticache.CacheCluster``
* ``botocraft.services.elasticache.ReplicationGroup``
* ``botocraft.services.docdb.DocDBCluster``

Each method returns a context-managed object with these attributes:

* ``host``: hostname to connect to
* ``port``: port to connect to
* ``tunneled``: whether a local SSM tunnel is active
* ``tunnel_host_instance``: EC2 jump host used for the tunnel, when applicable

EC2 Instance tunneling
~~~~~~~~~~~~~~~~~~~~~~

``botocraft.services.ec2.Instance`` exposes two related APIs for reaching
arbitrary remote endpoints through a jump host that you choose explicitly:

``open_connection_target(host=..., port=...)``
    Returns a :py:class:`~botocraft.connectivity.ResolvedConnectionTarget`
    with the same ``host``, ``port``, ``tunneled``, and
    ``tunnel_host_instance`` attributes as the managed-resource helpers.
    On context entry, the target is rewritten to
    ``127.0.0.1:<local-port>``.

``tunnel(host=..., remote_port=...)``
    Lower-level context manager that yields the chosen local forwarded port
    directly. ``TunnelAwareConnectionResolver`` uses this internally. Pair it
    with ``open_tunnel()`` and ``close_tunnel()`` when you need manual tunnel
    lifecycle control instead of a context manager.

Both APIs use AWS Systems Manager port forwarding through the instance. Literal
IP addresses are forwarded unchanged. Hostnames, including private VPC DNS
names such as LDAP servers, are passed through to SSM so resolution happens on
the jump host inside the VPC.

Why context manager?
--------------------

When ``botocraft`` is running outside AWS, private endpoints may only be
reachable through a tunnel host instance inside the target VPC. In that case
``open_connection_target()`` establishes a local SSM port-forward and rewrites
the connection target to ``127.0.0.1:<local-port>``. The context manager keeps
that tunnel alive for the duration of the block and cleans it up afterward.

When ``botocraft`` is already running inside AWS, the same API returns the real
resource endpoint unchanged.

The first pass intentionally matches the existing ``awsutils`` behavior:

* inside/outside is determined by reachability of the EC2 metadata endpoint
  (IMDS)
* no same-VPC detection is attempted yet
* missing tunnel host instances only fail when a tunnel is actually required

Configuration
-------------

Tunnel behavior is configured through ``botocraft.config.BotocraftSettings``.
Configuration sources are loaded in this order:

1. initialization arguments
2. environment variables
3. ``~/.botocraft.toml`` or ``BOTOCRAFT_CONFIG_FILE``
4. defaults

Example TOML:

.. code-block:: toml

    [tunnel]
    enabled = true
    tunnel_host_tag_key = "Purpose"
    tunnel_host_tag_value = "tunnel-host"
    ready_timeout_seconds = 10

Equivalent environment variables:

.. code-block:: bash

    export BOTOCRAFT_TUNNEL__ENABLED=true
    export BOTOCRAFT_TUNNEL__TUNNEL_HOST_TAG_KEY=Purpose
    export BOTOCRAFT_TUNNEL__TUNNEL_HOST_TAG_VALUE=tunnel-host
    export BOTOCRAFT_TUNNEL__READY_TIMEOUT_SECONDS=10

Examples
--------

RDS:

.. code-block:: python

    from botocraft.services.rds import DBInstance

    db = DBInstance.objects.get(DBInstanceIdentifier="db-main")
    with db.open_connection_target() as target:
        print(target.host, target.port, target.tunneled)

ElastiCache replication group:

.. code-block:: python

    from botocraft.services.elasticache import ReplicationGroup

    redis = ReplicationGroup.objects.get(ReplicationGroupId="cache-main")
    with redis.open_connection_target() as target:
        print(target.host, target.port)

DocumentDB cluster:

.. code-block:: python

    from botocraft.services.docdb import DocDBCluster

    cluster = DocDBCluster.objects.get(DBClusterIdentifier="docdb-main")
    with cluster.open_connection_target() as target:
        print(target.host, target.port)

EC2 jump host with ``open_connection_target()``:

.. code-block:: python

    from botocraft.services.ec2 import Instance

    jump = Instance.objects.get(InstanceId="i-0123456789abcdef0")
    with jump.open_connection_target(host="ldap.corp.internal", port=389) as target:
        ldap.connect(host=target.host, port=target.port)

EC2 jump host with ``tunnel()``:

.. code-block:: python

    from botocraft.services.ec2 import Instance

    jump = Instance.objects.get(InstanceId="i-0123456789abcdef0")
    with jump.tunnel(host="ldap.corp.internal", remote_port=389) as local_port:
        ldap.connect(host="127.0.0.1", port=local_port)

Failure modes
-------------

Common connection errors now surface as clear runtime exceptions:

* resource has no usable endpoint
* resource VPC cannot be resolved
* no running provisioner instance matches the configured tag key/value
* AWS CLI is missing
* local AWS CLI lacks ``aws ssm start-session``
* the SSM tunnel subprocess exits early and returns stderr

See :doc:`/runbook/tunneling` for setup and troubleshooting details.
