CHANGELOG
=========

0.36.6 (2026-11-19)
-------------------

Bugfixes
^^^^^^^^

- AgentCore create and update calls omit empty nested lists and maps whose minimum length is 1. ``AgentCoreAgentRuntimeManager.create()`` and ``update()`` send a JWT authorizer that holds only ``discoveryUrl`` and ``allowedClients`` without ``allowedAudience``, ``allowedScopes``, ``customClaims``, ``certificateConfigurations``, ``advertisedScopeMapping``, or empty ``privateEndpointOverrides``. A populated list or map is still sent. A get that omits these fields still validates, and ``update()`` of that model sends only the values it holds.

0.36.4 (2026-11-19)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against boto3 1.44.7 and botocore 1.44.7.
- ``ACMCertificateManager.request()`` and ``list()`` accept Amazon N2 ``RootHierarchyType`` and ``CertificateUsage``.
- An AgentCore runtime can mount an S3 bucket (``S3BucketMountConfiguration``) and set a Linux privilege mode on a capacity provider.
- ``CognitoUserPoolClientManager.create()`` and ``update()`` take ``PublishSecretsInAWSSecretsManager``. The client exposes ``ClientSecretArn``.
- CodeConnections provider types include ``GitHubEnterpriseCloudDataResidency``. A connection exposes ``ProviderEndpoint``.
- ELBv2 mutual authentication accepts ``ClientCertificateIdentityFilter``.
- IAM roles and login profiles expose ``MaxSigninSessionDuration``. ``update()`` clears it with ``ResetMaxSigninSessionDuration``.
- An RDS DB instance exposes ``RDSPrimaryEndpoint`` and ``VPCNetworkingEnabled``.
- SES delivery options include ``SharedPoolDeliveryMode``.
- STS assume-role responses include ``STSTrustedIdentityPropagationContext``.

Bugfixes
^^^^^^^^

- ``AgentCoreAgentRuntimeManager.create()`` and ``update()`` omit empty ``allowedPorts``, ``filesystemConfigurations``, ``resourceConfigurations``, and ``environmentVariables``.

0.36.3 (2026-11-19)
-------------------

Bugfixes
^^^^^^^^

- ``AgentCoreAgentRuntime.get()`` reads a runtime that omits ``description``. ``description`` is ``str | None``.

0.36.2 (2026-11-18)
-------------------

Enhancements
^^^^^^^^^^^^

- ``S3Object.get()``, ``list()``, and ``create()`` set ``BucketName`` and ``Key``. ``contents()`` returns the unread body, and ``create()`` returns the object.
- Added DocumentDB cluster parameter groups. ``update()`` returns the refreshed group.
- Added ``AgentCoreAgentRuntimeManager.list_versions()``.
- ``PrimaryBoto3ModelQuerySet`` is parameterized by its model class.
- Renamed colliding shapes to ``BedrockS3Location``, ``AgentCoreS3Location``, ``AgentCoreVpcConfig``, and ``AgentCoreDocument``.

Bugfixes
^^^^^^^^

- ``Bucket.objects.get()`` reads a bucket logging configuration that omits unused fields.
- ``S3ObjectManager.create()`` omits an empty ``ChecksumAlgorithm`` list.
- ``ACMManagerMixin.update()`` sends tag dictionaries to ACM.
- Paged ``list()`` methods continue when a page is empty and still carries a token.
- Event summaries render when a detail field is also named ``event``.
- ``LogGroupManager.create()`` accepts ``tags``.
- Optional read-only enum fields are typed ``| None``.

0.36.1 (2026-11-03)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against current boto3 and botocore.

Bugfixes
^^^^^^^^

- ``PayloadType.json`` is ``json_data``. ``PortRange`` is ``AgentCorePortRange``, with ``from`` and ``to`` as ``from_port`` and ``to_port``.
- Cleared remaining Pydantic warnings in the generated models.

0.36.0 (2026-10-23)
-------------------

Enhancements
^^^^^^^^^^^^

- Added Amplify Hosting for apps, branches, domains, and manual zip deploys.
- ``deploy_zip()`` uploads a local zip and starts the deployment. ``job.wait()``, ``job.log_text()``, and ``step.log_text()`` follow that job.

0.35.2 (2026-10-21)
-------------------

``using(session)`` returns a new manager bound to that session. The manager you called it on keeps its previous session. Keep the returned manager for calls that must use those credentials. ``using(None)`` returns the same manager.

Bugfixes
^^^^^^^^

- A shared manager keeps its own session when another caller binds a different one.
- ``save()`` and ``delete()`` use the session stamped on the model.
- Security group creation uses the session on the model.
- DataSync helpers keep the manager returned by ``using()``.
- A session-bound manager recomputes cached values from the previous session.

0.35.1 (2026-10-19)
-------------------

Bugfixes
^^^^^^^^

- Renamed the ECS attachment model to ``ECSAttachment``.

0.35.0 (2026-09-29)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer boto3 and botocore.
- ``create()`` forwards tags from the model. The separate ``Tags`` keyword on create is removed.

0.34.0 (2026-09-24)
-------------------

This version was bumped and not tagged. 0.35.0 is the next tagged release.

Enhancements
^^^^^^^^^^^^

- An SSM parameter can read and update its tags.

0.33.3 (2026-09-03)
-------------------

Bugfixes
^^^^^^^^

- AgentCore and ECS each keep their own ``NetworkConfiguration`` model.

0.33.2 (2026-08-31)
-------------------

Enhancements
^^^^^^^^^^^^

- Added ``CognitoUserManager.set_password()`` and ``CognitoUserManager.reset_password()``.

0.33.1 (2026-08-31)
-------------------

Bugfixes
^^^^^^^^

- Generated method docstrings are indented as normal docstrings.

0.33.0 (2026-08-31)
-------------------

Enhancements
^^^^^^^^^^^^

- Added Cognito user pools (``cognito-idp``) and Cognito identity pools (``cognito-identity``).

0.32.0 (2026-08-28)
-------------------

Enhancements
^^^^^^^^^^^^

- Added Amazon Bedrock AgentCore and AgentCore control.

0.31.0 (2026-08-07)
-------------------

Enhancements
^^^^^^^^^^^^

- Added AWS Managed Grafana.

Bugfixes
^^^^^^^^

- Grafana name fields leave ``PrimaryBoto3Model.name`` in place.
- A service-account or token list round-trip keeps the name.

0.30.4 (2026-07-28)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer botocore.

Bugfixes
^^^^^^^^

- DataSync task-execution helpers keep the session on the manager in use.

0.30.3 (2026-07-24)
-------------------

Bugfixes
^^^^^^^^

- CodePipeline EventBridge events include the detail fields from the AWS docs.

0.30.2 (2026-06-11)
-------------------

Enhancements
^^^^^^^^^^^^

- Added ``Instance.open_connection_target()`` as a context manager for a tunnel-aware connection.

0.30.1 (2026-06-09)
-------------------

Enhancements
^^^^^^^^^^^^

- Added CloudWatch Logs Insights search and ``QueryDefinition`` support.

0.30.0 (2026-05-29)
-------------------

Enhancements
^^^^^^^^^^^^

- Added DataSync, SES, SESv2, Kinesis, EFS, and CodeConnections.
- Added ElastiCache EventBridge events, and aligned the ELBv2, ECR, and ECS CloudTrail event models.

0.29.0 (2026-05-26)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services.
- Folded the ACM CloudTrail API-call events into one event model.

0.28.1 (2026-05-26)
-------------------

Bugfixes
^^^^^^^^

- ``TaskDefinitionManager.get()`` works again.
- The test suite runs again.

0.28.0 (2026-05-26)
-------------------

Enhancements
^^^^^^^^^^^^

- Added CloudWatch and OpenSearch.
- Added ECS Exec on a task and on a service.
- Added tunnel-aware connection targets for private services.
- Added more EC2 primary models, with VPC, subnet, and security-group relations where the identifiers are on the object.
- Added EventBridge events for OpenSearch, Elasticsearch, and CodePipeline.

0.27.0 (2026-05-18)
-------------------

Enhancements
^^^^^^^^^^^^

- Added CodePipeline and CodeBuild.
- Added ECS daemons, Express gateway services, capacity providers, service revisions, and task sets.

Bugfixes
^^^^^^^^

- A model whose ARN field is ``arn``, or whose name field is ``name``, keeps that single property.
- Rebuilt Bedrock against the boto3 and botocore shapes in this release.

0.26.0 (2026-05-14)
-------------------

Enhancements
^^^^^^^^^^^^

- Added Amazon Bedrock and Bedrock Runtime. Streaming calls such as ``converse_stream()`` return iterators.
- Added the Schemas service and ``botocraft eventbridge`` commands.
- Added Bedrock model relations and the SSM EventBridge events published in the AWS schema library.

Bugfixes
^^^^^^^^

- Schema list results come back as a queryset.
- ``botocraft botocore bootstrap`` writes the filenames the rest of the tool expects.

Documentation
^^^^^^^^^^^^^

- Added an overview of Bedrock inference and clearer instructions for adding a service.

0.25.1 (2026-04-22)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against current dependencies.

Bugfixes
^^^^^^^^

- ``TargetGroup.objects.get(TargetGroupArn=...)`` works again.

0.25.0 (2026-04-10)
-------------------

Enhancements
^^^^^^^^^^^^

- Added ElastiCache users and user groups as primary models.

0.24.2 (2026-04-07)
-------------------

Bugfixes
^^^^^^^^

- ``LoadBalancer.objects.get()`` works again.

0.24.1 (2026-04-06)
-------------------

Bugfixes
^^^^^^^^

- ``AMIManager.in_use(tags=...)`` uses ``tags`` to choose which AMIs to inspect.

0.24.0 (2026-04-03)
-------------------

Enhancements
^^^^^^^^^^^^

- Added Secrets Manager. ``Secret.objects.get()`` returns a ``Secret``.
- Added DocumentDB.
- An RDS instance that stores its master password in Secrets Manager can read that username and password through ``credentials``.

Bugfixes
^^^^^^^^

- Botocraft imports and runs on Python 3.14.

0.23.2 (2026-04-01)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against current dependencies.

0.23.1 (2026-03-23)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer boto3 and botocore.

0.23.0 (2026-02-06)
-------------------

Enhancements
^^^^^^^^^^^^

- Added ACM.

0.22.0 (2026-02-06)
-------------------

Enhancements
^^^^^^^^^^^^

- Added the first CloudWatch Logs models and managers.
- A container definition can identify the ECR image it uses.
- A relation can declare the imports it needs when the related model lives in another service.

0.21.7 (2026-01-20)
-------------------

Bugfixes
^^^^^^^^

- Removed a debugging print from the AMI in-use check.

0.21.6 (2026-01-20)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer boto3 and botocore.

Bugfixes
^^^^^^^^

- ``AMIManager.in_use()`` honors the ``tags`` argument.

0.21.5 (2026-01-14)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against current dependencies.
- Updated the packaged license file for 2026.

0.21.4 (2025-12-11)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer boto3 and botocore.

0.21.3 (2025-11-11)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer boto3 and botocore.

Bugfixes
^^^^^^^^

- Listing unused AMIs and deleting them completes.

0.21.2 (2025-10-21)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer boto3 and botocore.

0.21.1 (2025-10-09)
-------------------

Enhancements
^^^^^^^^^^^^

- An S3 object can be downloaded, including its bytes.

0.21.0 (2025-10-08)
-------------------

Enhancements
^^^^^^^^^^^^

- Added S3.
- A model definition can force a response shape to be generated when the usual rules would skip it.

0.20.3 (2025-10-03)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services.

Bugfixes
^^^^^^^^

- ``TaskDefinition.delete()`` works again, including a delete of more than ten task definitions.
- ``RunTimePlatform.cpuArchitecture`` accepts ``x86_64`` and ``ARM``.

0.20.2 (2025-10-02)
-------------------

Bugfixes
^^^^^^^^

- Broke the circular import introduced with task-definition delete.

0.20.1 (2025-10-02)
-------------------

Enhancements
^^^^^^^^^^^^

- ``TaskDefinitionManager`` has ``deregister()`` and ``delete()``.
- Rebuilt the generated services against current dependencies.

0.20.0 (2025-09-18)
-------------------

Enhancements
^^^^^^^^^^^^

- Added IAM.

Bugfixes
^^^^^^^^

- Tag handling works when a tag class has no defaults.

0.19.1 (2025-09-05)
-------------------

Bugfixes
^^^^^^^^

- ``AMI.objects.in_use()`` asks EC2 about AMIs in smaller groups.

0.19.0 (2025-09-04)
-------------------

Enhancements
^^^^^^^^^^^^

- Added an EC2 snapshot as a primary model.

0.18.1 (2025-09-03)
-------------------

Bugfixes
^^^^^^^^

- An attached EBS volume may report status ``in-use``.

0.18.0 (2025-09-03)
-------------------

Enhancements
^^^^^^^^^^^^

- Models that have a primary key can be used in sets and as dictionary keys.

0.17.11 (2025-09-03)
--------------------

Bugfixes
^^^^^^^^

- The AMI mixin starts its filter list empty.

0.17.10 (2025-08-06)
--------------------

Bugfixes
^^^^^^^^

- ``AMI.Platform`` accepts ``windows`` or empty.

0.17.9 (2025-08-06)
-------------------

Enhancements
^^^^^^^^^^^^

- Two primary-model querysets can be added together.

Bugfixes
^^^^^^^^

- ``AMI.Platform`` may be empty.

0.17.8 (2025-08-06)
-------------------

Enhancements
^^^^^^^^^^^^

- Mixin and decorator methods that returned a list of models now return a queryset.

0.17.7 (2025-08-06)
-------------------

Enhancements
^^^^^^^^^^^^

- ``AMI.in_use()`` also searches Auto Scaling groups.

Bugfixes
^^^^^^^^

- An EC2-instances filter survives a page that comes back empty.

0.17.6 (2025-08-06)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer botocore.

Bugfixes
^^^^^^^^

- A paged list continues until ``NextToken`` is absent.

0.17.5 (2025-06-10)
-------------------

Refreshed locked requirements for the semgrep tooling. No service behavior changes.

0.17.4 (2025-06-10)
-------------------

Enhancements
^^^^^^^^^^^^

- A task definition load includes its tags.
- Rebuilt the generated services against current dependencies.

Bugfixes
^^^^^^^^

- The generated ECS CloudTrail API-call event includes the payload fields it was dropping.

0.17.3 (2025-06-03)
-------------------

Enhancements
^^^^^^^^^^^^

- Added ``botocraft botocore bootstrap`` to scaffold a new service definition.

Bugfixes
^^^^^^^^

- Reading tags on an ECR repository completes.
- ``ECSServiceActionEvent`` prints the event it received.

0.17.2 (2025-06-02)
-------------------

Enhancements
^^^^^^^^^^^^

- EventBridge events have a readable string form.
- An SQS message can carry the queue URL it came from. ``receive()``, ``poll()``, and ``receive_messages()`` can parse the body as an EventBridge event.

Bugfixes
^^^^^^^^

- ``PrimaryBoto3Model.delete()`` calls the manager ``delete()``.
- The raw EventBridge event modules import again.

0.17.1 (2025-05-28)
-------------------

Refreshed locked requirements. No service behavior changes.

0.17.0 (2025-05-28)
-------------------

Enhancements
^^^^^^^^^^^^

- ``list()`` and ``get_many()`` return a queryset that can be filtered further.

0.16.0 (2025-05-23)
-------------------

Enhancements
^^^^^^^^^^^^

- Added AWS Inspector.
- An EventBridge event can be parsed into a Pydantic model.
- Added an ECS service deployment as a primary model.
- ``botocraft botocore operations --names-only`` prints operation names.
- Now requires Python 3.10 or newer.

Bugfixes
^^^^^^^^

- Generated ``list()`` methods page correctly.
- ``get_many()`` keeps an optional return type when the call may find nothing.

0.15.0 (2025-05-16)
-------------------

Enhancements
^^^^^^^^^^^^

- Added Application Auto Scaling, including relations between its models.
- An SQS queue can poll with a generator of messages.
- A primary model may use a composite primary key.

Bugfixes
^^^^^^^^

- ``Instance.open_tunnel()`` returns after the local port is accepting connections.
- Saving a model that AWS does not allow you to update raises an exception.
- Service names that contain a dash generate a valid Python module.
- Hand-written models get the same manager arguments as shape-backed models.
- SQS queue tags arrive in the shape the shared tag mixin expects.

0.14.0 (2025-05-14)
-------------------

Enhancements
^^^^^^^^^^^^

- Added SQS.
- Added an EventBridge event bus as a primary model.
- An EC2 instance can open an SSM tunnel with ``tunnel`` / ``open_tunnel()``.
- An RDS instance can reach its subnet group, security groups, and VPC.
- An ElastiCache replication group or cache cluster can report its tags, hostname, and port.
- A model can be defined by hand when AWS has no single shape for it.

Bugfixes
^^^^^^^^

- Class docstrings are generated again.

0.13.0 (2025-05-02)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services.

Bugfixes
^^^^^^^^

- A renamed model field uses a Pydantic alias.
- The class-property helper works on Python 3.13.

0.12.5 (2025-05-01)
-------------------

Enhancements
^^^^^^^^^^^^

- An ElastiCache replication group exposes ``engine_version``.

0.12.4 (2025-05-01)
-------------------

Bugfixes
^^^^^^^^

- Importing the generated services succeeds after the botocore update in 0.12.3.

0.12.3 (2025-05-01)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services.

Bugfixes
^^^^^^^^

- Tag fields are detected more reliably during generation.
- An RDS instance's tag list uses the name the shared tag mixin expects.
- An optional list field defaults to an empty list.

0.12.2 (2025-05-01)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against a newer botocore.

0.12.1 (2025-04-03)
-------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against current dependencies.

0.12.0 (2024-11-12)
-------------------

Enhancements
^^^^^^^^^^^^

- Added STS and EventBridge (``events``).
- An AMI, an ECR image, or a task definition can report whether it is still in use.
- Added ``TaskDefinitionManager.families()`` and ``ServiceManager.all()``.
- An ECR image can list the services and task definitions that reference it.
- A relation can name the manager method that loads the related object.
- Rebuilt the generated services for botocore 1.35.58. A few model names moved with those shapes.

Bugfixes
^^^^^^^^

- ``ECRImage.objects.list()`` completes.
- ``botocraft botocore`` prints list shapes with their members.

0.11.0 (2024-11-04)
-------------------

Enhancements
^^^^^^^^^^^^

- A Classic ELB can list its EC2 instances, and an Application Load Balancer can list its targets.
- An EC2 instance can reach its AMI, network interfaces, and instance type. A launch template can reach its AMI and instance type. A network ACL can reach its VPC and subnets.
- Raised the minimum boto3 and botocore versions and rebuilt the generated services.

Bugfixes
^^^^^^^^

- ``set_session()`` lives on every model.
- An empty list or dict from AWS is left alone during session setup.
- Related objects are loaded with the parent object's session.

0.10.0 (2024-10-31)
-------------------

Enhancements
^^^^^^^^^^^^

- Added Classic ELB, including tags on the load balancer.

Bugfixes
^^^^^^^^

- The Auto Scaling tag-description model is distinct from the Classic ELB one.
- Nested values are serialized on the way to boto3.
- Older mixins load related objects with ``.using(self.session)``.

0.9.0 (2024-10-29)
------------------

Enhancements
^^^^^^^^^^^^

- Added Route 53.
- A field marked required in the service definition stays required.

Bugfixes
^^^^^^^^

- Setting a session on a frozen model thaws it for that assignment.
- Session setup walks lists and dicts of models.
- A create call whose response is the whole payload returns that payload.
- A paged list that ends with a metadata-only page stops there.

0.8.0 (2024-10-28)
------------------

Enhancements
^^^^^^^^^^^^

- Added ElastiCache.
- Require boto3 and botocore 1.35.50 or newer, and rebuilt the generated services.
- ``botocraft botocore model --operations`` prints the input and output shapes.

Bugfixes
^^^^^^^^

- ``KMSKey.objects.list()`` returns keys.
- An ELBv2 name collision with another service is renamed.
- A primary model with an alternate name still generates a working manager.

0.7.0 (2024-10-18)
------------------

Enhancements
^^^^^^^^^^^^

- An ECS service can reach its load balancer and target group.
- A load balancer exposes its attributes, including logging, as a dictionary.

0.6.0 (2024-10-15)
------------------

Enhancements
^^^^^^^^^^^^

- Added KMS.

Bugfixes
^^^^^^^^

- A manager method with an empty response body returns ``None``.

0.5.5 (2024-10-15)
------------------

Bugfixes
^^^^^^^^

- ``get_many()`` is generated as a callable method again.
- A session set on a read-only model stays on that model.

0.5.4 (2024-10-15)
------------------

Enhancements
^^^^^^^^^^^^

- An ECR image can reach its repository.
- ``botocraft botocore`` prints list and enum shapes in more detail.

Bugfixes
^^^^^^^^

- Manager methods stamp the boto3 session onto the models they return.
- Copying an AMI accepts a tag specification.

0.5.3 (2024-10-04)
------------------

Enhancements
^^^^^^^^^^^^

- Added ``Parameter.objects.get_many()``.

Bugfixes
^^^^^^^^

- A model with an alternate name gets a manager class named after that public name.
- ``Parameter.objects.list()`` returns parameters.
- A session can be set on a read-only model.

0.5.2 (2024-10-04)
------------------

Enhancements
^^^^^^^^^^^^

- Models loaded from AWS keep the boto3 session, and relations use that session.
- ``Model.objects`` is a class property.
- Dependency installs are managed with uv.

0.5.1 (2024-09-13)
------------------

Bugfixes
^^^^^^^^

- Free CPU and free memory on an ECS container instance report the unused capacity.

0.5.0 (2024-09-06)
------------------

Enhancements
^^^^^^^^^^^^

- Added an EC2 AMI as a primary model.
- An ECS service can report required CPU and memory, its container instances, and whether it is stable.
- An Auto Scaling group can report whether it is stable and wait until it is.
- A container instance can list the tasks running on it.
- Added ``PrimaryBoto3Model.get_waiter()``.
- Require boto3 and botocore 1.35.12 or newer.
- Renamed the ECR image model to ``ECRImage``, the ECS container-instance resource model to ``ContainerInstanceResource``, and the Auto Scaling activity model to ``AutoScalingActivity``.

Bugfixes
^^^^^^^^

- ``Service.scale()`` and ``AutoScalingGroup.scale()`` change the desired count.
- An Auto Scaling group's EC2 instances and launch configuration resolve.
- ``Service.roleArn`` and ``TaskDefinition.taskRoleArn`` are optional.
- ``AutoScalingGroupManager.update()`` works.

0.4.0 (2024-08-26)
------------------

Enhancements
^^^^^^^^^^^^

- A model can call manager methods such as ``scale()`` on itself.
- An ECS service or an Auto Scaling group can be scaled, and a group can report instance status.
- An ECR image can report replication status and scan findings.
- An EC2 instance can be rebooted or terminated from its manager.
- Several ECR manager methods return the full result, including failures.
- Renamed the ECR attribute model to ``ECRAttribute``.

Bugfixes
^^^^^^^^

- ``Service.tasks`` is read again on each access.
- Listing ECS services pages in the groups AWS allows.
- A paginated call that returns a non-list payload completes.

0.3.0 (2024-08-22)
------------------

Enhancements
^^^^^^^^^^^^

- Added ``botocraft shell``.
- Expanded ECR beyond the first repository and image models.

0.2.4 (2024-08-07)
------------------

Bugfixes
^^^^^^^^

- A related object is loaded with the same boto3 session as its parent.
- An Auto Scaling group's targets use the type AWS returns.

0.2.3 (2024-08-02)
------------------

Enhancements
^^^^^^^^^^^^

- A manager can be given a boto3 session and uses that session for its calls.

0.2.2 (2024-07-31)
------------------

Enhancements
^^^^^^^^^^^^

- An EC2 instance can be started and stopped from ``InstanceManager``.
- Require a current boto3 and botocore, and rebuilt the generated services.

Bugfixes
^^^^^^^^

- A model field that AWS returns under another name maps onto the Python attribute.
- The helper that fills in an ECS task definition matches the payload boto3 returns.

0.2.1 (2024-06-12)
------------------

Enhancements
^^^^^^^^^^^^

- Rebuilt the generated services against botocore 1.34.13.

0.2.0 (2023-12-15)
------------------

Enhancements
^^^^^^^^^^^^

- First release. Added EC2 VPCs, subnets, security groups, and instances; ECS clusters, services, tasks, and task definitions; ECR repositories; RDS DB instances; Auto Scaling groups; launch templates; and network ACLs.
- ``list()`` for clusters, services, and task definitions returns those objects.
- Models can follow relations to other models, and models with a tag map can read and write those tags.
