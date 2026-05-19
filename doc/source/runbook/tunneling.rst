Tunnel Setup and Troubleshooting
================================

``botocraft`` uses AWS Systems Manager Session Manager port forwarding when it
needs to reach private resource endpoints from outside AWS.

This runbook covers:

* prerequisites
* runtime configuration
* tunnel host instance discovery
* common errors

Prerequisites
-------------

``botocraft`` relies on the local AWS CLI for tunnel creation. The local
machine must have:

* AWS CLI installed and available on ``PATH``
* support for ``aws ssm start-session``
* credentials/profile access that can start SSM sessions against the tunnel host
  instance

If either prerequisite is missing, ``open_connection_target()`` raises a clear
runtime error before trying to open the tunnel.

How tunneling is triggered
--------------------------

The first pass follows the same trigger used by ``awsutils``:

* when the EC2 metadata endpoint ``169.254.169.254:80`` is reachable,
  ``botocraft`` assumes it is already running inside AWS and uses the real
  resource endpoint directly
* otherwise it resolves a tunnel host instance in the target VPC and opens a
  local SSM tunnel through that instance

This is intentionally conservative. Same-VPC detection is not implemented yet.

Tunnel host discovery
---------------------

Tunnel host lookup searches for a running EC2 instance in the target VPC with
one configurable tag key/value pair.

Defaults:

* tag key: ``Purpose``
* tag value: ``provisioner``

Lookup filters are:

* ``tag:<configured-key> = <configured-value>``
* ``vpc-id = <target-vpc-id>``
* ``instance-state-name = running``

Configuration
-------------

Runtime tunnel settings can come from either environment variables or a TOML
file.

Default file path:

.. code-block:: text

    ~/.botocraft.toml

Override file path:

.. code-block:: bash

    export BOTOCRAFT_CONFIG_FILE=/path/to/botocraft.toml

Example configuration:

.. code-block:: toml

    [tunnel]
    enabled = true
    tunnel_host_tag_key = "Purpose"
    tunnel_host_tag_value = "tunnel-host"
    ready_timeout_seconds = 10

Environment-variable equivalents:

.. code-block:: bash

    export BOTOCRAFT_TUNNEL__ENABLED=true
    export BOTOCRAFT_TUNNEL__TUNNEL_HOST_TAG_KEY=Purpose
    export BOTOCRAFT_TUNNEL__TUNNEL_HOST_TAG_VALUE=tunnel-host
    export BOTOCRAFT_TUNNEL__READY_TIMEOUT_SECONDS=10

Using the API
-------------

All supported resources expose the same interface:

.. code-block:: python

    with resource.open_connection_target() as target:
        connect(host=target.host, port=target.port)

``target.tunneled`` tells you whether the block is using the original endpoint
or a local forwarded port.

Troubleshooting
---------------

``AWS CLI is not installed or not in PATH.``
    Install AWS CLI and ensure ``aws`` is available in the current shell.

``AWS CLI does not support `aws ssm start-session`. ...``
    Upgrade to AWS CLI v2 with Session Manager support.

``Unable to connect to ... no running tunnel host instance matched tag ...``
    Confirm the target VPC contains a running EC2 tunnel host instance with the
    configured tag key/value pair.

``... does not have a usable endpoint.``
    The resource is missing endpoint metadata. Check that it is in an available
    state and fully provisioned.

``... does not have a resolvable VPC.``
    The resource or its supporting subnet metadata does not expose a VPC ID.

``Failed to open tunnel ... AWS CLI stderr: ...``
    The AWS CLI/SSM subprocess exited before the local port opened. The stderr
    suffix should contain the actionable failure, such as expired credentials or
    denied SSM access.
