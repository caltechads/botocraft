# Changelog

## [0.36.0] - 2026-10-23

### Added

- Add Amplify Hosting. You can manage an app, its branches, domains, webhooks, and backend environments, and you can publish a zip you already built. Amplify's own build and job-cancel APIs stay out.
- Add `create()` calls that take the fields Amplify accepts, such as `name` for an app. You no longer have to invent the app id, ARN, or timestamps Amplify assigns.
- Add `deploy_zip()` to upload a local zip and start that deployment. Pass `wait=True` to get the job back after it succeeds, fails, or is cancelled.
- Add `job.wait()` to poll a job until it finishes, and `branch.active_job` to load the job id currently recorded on a branch.
- Add `job.log_text()` and `step.log_text()` to download one step log. A failed step is chosen before any other step. `access_log_text()` downloads the access log for a domain.

## [0.35.2] - 2026-10-20

### Changed

- `using(session)` now returns a new manager bound to that session. The manager you called it on is left as it was. Keep the returned manager and use it for every call that must run with those credentials. `using(None)` still returns the same manager and does not rebind. One `using()` call does not affect any other manager in the process.
- Calling `using(session)` and then using the original manager does not raise an error. Those later calls still run with the original manager's client, usually the process identity. Code that depended on `using()` changing the manager in place must use the manager `using()` returns. There is no deprecation period.

### Fixed

- Fix shared managers picking up whichever session was bound last. A held manager could run a later call with another caller's credentials.
- Fix `save()` and `delete()` so a model loaded under a session writes and deletes with that session. Nested models are still not stamped with the session, and their `save()` and `delete()` use a default manager.
- Fix security group creation so the create call uses the session on the model. Authorizing ingress already did.
- Fix DataSync helpers so they keep the manager `using()` returns, instead of going back to the original manager and its client.
- Fix a manager bound to a new session so it recomputes cached values that came from the previous session, such as an account id.

## [0.35.1] - 2026-10-19

### Fixed

- Rename the ECS attachment model to `ECSAttachment`. The old name collided with the SESv2 attachment model.

## [0.35.0] - 2026-09-29

### Changed

- Rebuild the generated services against a newer boto3 and botocore.
- `create()` forwards tags from the model. The separate `Tags` keyword on create is gone.

## [0.34.0] - 2026-09-29

This version was bumped and not given its own git tag. It sits between 0.33.3 and 0.35.0.

### Added

- Add tag read and update for an SSM parameter.

## [0.33.3] - 2026-09-03

### Fixed

- Keep AgentCore `NetworkConfiguration` from replacing the ECS `NetworkConfiguration` model.

## [0.33.2] - 2026-08-31

### Added

- Add `CognitoUserManager.set_password()` and `CognitoUserManager.reset_password()`.

## [0.33.1] - 2026-08-31

### Fixed

- Generated method docstrings are indented like normal docstrings again.

## [0.33.0] - 2026-08-31

### Added

- Add Cognito user pools (`cognito-idp`) and Cognito identity pools (`cognito-identity`).

## [0.32.0] - 2026-08-28

### Added

- Add Amazon Bedrock AgentCore and AgentCore control.

## [0.31.0] - 2026-08-07

### Added

- Add AWS Managed Grafana.

### Changed

- Rebuild the generated services against current boto3 and botocore.

### Fixed

- Grafana name fields no longer hide `PrimaryBoto3Model.name`.
- A service-account or token list round-trip keeps the name.

## [0.30.4] - 2026-07-28

### Changed

- Rebuild the generated services against a newer botocore.

### Fixed

- DataSync task-execution helpers keep the session on the manager you are using.

## [0.30.3] - 2026-07-24

### Fixed

- CodePipeline EventBridge events include the detail fields described in the AWS docs.

## [0.30.2] - 2026-06-11

### Added

- Add `Instance.open_connection_target()` as a context manager for a tunnel-aware connection target.

### Changed

- Rebuild the generated services against a newer boto3 and botocore.

## [0.30.1] - 2026-06-09

### Added

- Add CloudWatch Logs Insights search and `QueryDefinition` support.

### Changed

- Rebuild the generated services against a newer boto3 and botocore.

## [0.30.0] - 2026-05-29

### Added

- Add DataSync, SES, SESv2, Kinesis, EFS, and CodeConnections.
- Add EventBridge events for ElastiCache, and align the ELBv2, ECR, and ECS CloudTrail event models.

## [0.29.0] - 2026-05-26

### Changed

- Rebuild the generated services.
- Fold the separate ACM CloudTrail API-call events into one event model.

## [0.28.1] - 2026-05-26

### Fixed

- `TaskDefinitionManager.get()` works again.
- The test suite runs again.

## [0.28.0] - 2026-05-26

### Added

- Add CloudWatch and OpenSearch.
- Add ECS Exec on a task and on a service.
- Add tunnel-aware connection targets for private services.
- Add more EC2 primary models, with VPC, subnet, and security-group relations where those identifiers are on the object.
- Add EventBridge events for OpenSearch, Elasticsearch, and CodePipeline.

## [0.27.0] - 2026-05-18

### Added

- Add CodePipeline and CodeBuild.
- Add ECS daemons, Express gateway services, capacity providers, service revisions, and task sets.

### Fixed

- A model whose ARN field is literally `arn`, or whose name field is literally `name`, no longer grows a second property with that same name.
- Rebuild Bedrock against the boto3 and botocore shapes from this release.

## [0.26.0] - 2026-05-14

### Added

- Add Amazon Bedrock and the Bedrock Runtime. Streaming calls such as `converse_stream()` return iterators.
- Add the Schemas service and `botocraft eventbridge` commands for turning EventBridge payloads into models.
- Add Bedrock model relations and the SSM EventBridge events that the AWS schema library publishes.

### Fixed

- Schema list results come back as a queryset again.
- `botocraft botocore bootstrap` writes the filenames the rest of the tool expects.

## [0.25.1] - 2026-04-22

### Changed

- Rebuild the generated services against current dependencies.

### Fixed

- `TargetGroup.objects.get(TargetGroupArn=...)` works again.

## [0.25.0] - 2026-04-10

### Added

- Add ElastiCache users and user groups as primary models.

## [0.24.2] - 2026-04-07

### Fixed

- `LoadBalancer.objects.get()` works again.

## [0.24.1] - 2026-04-06

### Changed

- Rebuild the generated services against current dependencies.

### Fixed

- `AMIManager.in_use(tags=...)` uses the tags to choose which AMIs to inspect. The tags no longer filter the instances and groups that might be using those AMIs.

## [0.24.0] - 2026-04-03

### Added

- Add Secrets Manager. `Secret.objects.get()` returns a `Secret`.
- Add DocumentDB.
- An RDS instance that stores its master password in Secrets Manager can read that username and password through `credentials`.

### Fixed

- Botocraft imports and runs on Python 3.14.

## [0.23.2] - 2026-04-01

### Changed

- Rebuild the generated services against current dependencies.

## [0.23.1] - 2026-03-23

### Changed

- Rebuild the generated services against a newer boto3 and botocore.

## [0.23.0] - 2026-02-06

### Added

- Add ACM.

## [0.22.0] - 2026-02-06

### Added

- Add the first CloudWatch Logs models and managers.
- A container definition can identify the ECR image it uses.

### Changed

- A relation can declare extra imports when the related model lives in another service.

## [0.21.7] - 2026-01-20

### Fixed

- Remove a debugging print that could show up while checking whether an AMI is in use.

## [0.21.6] - 2026-01-20

### Changed

- Rebuild the generated services against a newer boto3 and botocore.

### Fixed

- `AMIManager.in_use()` honors the `tags` argument.

## [0.21.5] - 2026-01-14

### Changed

- Rebuild the generated services against current dependencies.
- Update the packaged license file for 2026.

## [0.21.4] - 2025-12-11

### Changed

- Rebuild the generated services against a newer boto3 and botocore.

## [0.21.3] - 2025-11-11

### Changed

- Rebuild the generated services against a newer boto3 and botocore.

### Fixed

- Listing unused AMIs and deleting them no longer crashes.

## [0.21.2] - 2025-10-21

### Changed

- Rebuild the generated services against a newer boto3 and botocore.

## [0.21.1] - 2025-10-09

### Added

- Download the bytes of an S3 object, not only its metadata.

## [0.21.0] - 2025-10-08

### Added

- Add S3.
- A model definition can force a response shape to be generated when the usual rules would skip it.

### Changed

- Rebuild the generated services against current dependencies.

## [0.20.3] - 2025-10-03

### Changed

- Rebuild the generated services.

### Fixed

- `TaskDefinition.delete()` works again, including a delete of more than ten task definitions.
- `RunTimePlatform.cpuArchitecture` accepts only `x86_64` and `ARM`.

## [0.20.2] - 2025-10-02

### Fixed

- Break a circular import introduced with the task-definition delete work.

## [0.20.1] - 2025-10-02

### Added

- `TaskDefinitionManager` has both `deregister()` and `delete()`.

### Changed

- Rebuild the generated services against current dependencies.

## [0.20.0] - 2025-09-18

### Added

- Add IAM.

### Fixed

- Tag handling is steadier when a tag class has no defaults.

## [0.19.1] - 2025-09-05

### Fixed

- `AMI.objects.in_use()` asks EC2 about AMIs in smaller groups, so a long list no longer exceeds the API limit.

## [0.19.0] - 2025-09-04

### Added

- Add an EC2 snapshot as a primary model.

## [0.18.1] - 2025-09-03

### Fixed

- An EBS volume attached to an instance may report status `in-use`. That value is accepted.

## [0.18.0] - 2025-09-03

### Added

- Models that have a primary key can be used in sets and as dictionary keys.

## [0.17.11] - 2025-09-03

### Changed

- Rebuild the generated services for boto3 1.40.22 and botocore 1.40.22.

### Fixed

- An AMI mixin starts its filter list empty instead of failing on first use.

## [0.17.10] - 2025-08-06

### Changed

- Rebuild the generated services.

### Fixed

- `AMI.Platform` is `windows` or empty. The value `Windows` is rejected.

## [0.17.9] - 2025-08-06

### Added

- You can add two primary-model querysets together.

### Changed

- Rebuild the generated services.

### Fixed

- `AMI.Platform` may be empty.

## [0.17.8] - 2025-08-06

### Changed

- Mixin and decorator methods that used to return a bare list of models now return a queryset.

## [0.17.7] - 2025-08-06

### Changed

- `AMI.in_use()` asks the manager, and that search also looks at Auto Scaling groups, not only EC2 instances.

### Fixed

- An EC2-instances filter survives a page that comes back empty.

## [0.17.6] - 2025-08-06

### Changed

- Rebuild the generated services against a newer botocore.

### Fixed

- A paged list keeps going until `NextToken` is absent. An empty token no longer stops the first page early.

## [0.17.5] - 2025-06-10

### Changed

- Refresh the locked requirements used by the semgrep tooling. No service behavior changes.

## [0.17.4] - 2025-06-10

### Changed

- A task definition load includes its tags.
- Rebuild the generated services against current dependencies.

### Fixed

- The generated ECS CloudTrail API-call event matches the payload fields it was dropping.

## [0.17.3] - 2025-06-03

### Added

- Add `botocraft botocore bootstrap` to scaffold a new service definition.

### Changed

- Rebuild the generated services.

### Fixed

- Reading tags on an ECR repository no longer crashes.
- `ECSServiceActionEvent` prints the event it actually received.

## [0.17.2] - 2025-06-02

### Added

- EventBridge events have a readable string form.
- An SQS message can carry the queue URL it came from. `receive()`, `poll()`, and `receive_messages()` can parse a message body with an EventBridge event class you pass in.

### Changed

- Rebuild the generated services against current dependencies.

### Fixed

- `PrimaryBoto3Model.delete()` calls the manager `delete()` that actually exists.
- The raw EventBridge event modules import again.

## [0.17.1] - 2025-05-28

### Changed

- Refresh the locked requirements. No service behavior changes.

## [0.17.0] - 2025-05-28

### Added

- `list()` and `get_many()` return a queryset you can keep filtering, in the style of a Django queryset.

## [0.16.0] - 2025-05-23

### Added

- Add AWS Inspector.
- Parse an EventBridge event into a Pydantic model.
- Add an ECS service deployment as a primary model.
- `botocraft botocore operations --names-only` prints operation names without the rest of the shape.

### Changed

- Require Python 3.10 or newer.
- Rebuild the generated services.
- Generated code is formatted with Ruff.

### Fixed

- Generated `list()` methods page correctly.
- `get_many()` keeps an optional return type when the call may find nothing.

## [0.15.0] - 2025-05-16

### Added

- Add Application Auto Scaling, including relations between its models.
- An SQS queue can poll forever with a generator of messages.
- A primary model may use a composite primary key.

### Fixed

- `Instance.open_tunnel()` returns only after the local port is accepting connections.
- Saving a model that AWS does not allow you to update raises an exception instead of calling a missing API.
- Service names that contain a dash still generate a valid Python module.
- Bespoke models get the same manager arguments as shape-backed models.
- SQS queue tags arrive in the shape the shared tag mixin expects.

## [0.14.0] - 2025-05-14

### Added

- Add SQS.
- Add an EventBridge event bus as a primary model.
- Open an SSM tunnel to an EC2 instance with `Instance.tunnel` / `open_tunnel()`.
- An RDS instance can reach its subnet group, security groups, and VPC.
- An ElastiCache replication group or cache cluster can report its tags, hostname, and port.
- A model can be defined by hand when AWS has no single shape for the thing you want to manage.

### Fixed

- Class docstrings are generated again.

## [0.13.0] - 2025-05-02

### Changed

- Rebuild the generated services.

### Fixed

- A renamed model field uses a Pydantic alias.
- The class-property helper works on Python 3.13.

## [0.12.5] - 2025-05-01

### Added

- An ElastiCache replication group exposes `engine_version`.

## [0.12.4] - 2025-05-01

### Fixed

- Importing the generated services no longer fails on a circular import from the botocore update in 0.12.3.

## [0.12.3] - 2025-05-01

### Changed

- Rebuild the generated services.

### Fixed

- Tag fields are detected more reliably during generation.
- An RDS instance's tag list is renamed so the shared tag mixin can read and write it.
- An optional list field uses an empty list as its default instead of `None`.

## [0.12.2] - 2025-05-01

### Changed

- Rebuild the generated services against a newer botocore.

## [0.12.1] - 2025-04-03

### Changed

- Rebuild the generated services against current dependencies.

## [0.12.0] - 2024-11-12

### Added

- Add STS and EventBridge (`events`).
- Ask whether an AMI, an ECR image, or a task definition is still in use.
- List ECS task-definition families, and list every service with `ServiceManager.all()`.
- An ECR image can list the services and task definitions that reference it.
- A relation can name the manager method that should load the related object.

### Changed

- Rebuild the generated services for botocore 1.35.58. A few model names moved so they still match those shapes.

### Fixed

- `ECRImage.objects.list()` no longer crashes.
- `botocraft botocore` prints list shapes without dropping their members.

## [0.11.0] - 2024-11-04

### Added

- A Classic ELB can list its EC2 instances.
- An Application Load Balancer can list its targets.
- An EC2 instance can reach its AMI, network interfaces, and instance type. A launch template can reach its AMI and instance type. A network ACL can reach its VPC and subnets.

### Changed

- Rebuild the generated services against a newer minimum boto3 and botocore.

### Fixed

- `set_session()` lives on every model, including ones that are not primary resources.
- An empty list or dict from AWS is left alone instead of breaking session setup.
- Related objects are loaded with the parent object's session.

## [0.10.0] - 2024-10-31

### Added

- Add Classic ELB, including tags on the load balancer.

### Fixed

- The Auto Scaling tag-description model no longer collides with the Classic ELB one.
- Nested values are serialized on the way to boto3, not only the top-level arguments.
- Older mixins load related objects with `.using(self.session)`.

## [0.9.0] - 2024-10-29

### Added

- Add Route 53.

### Changed

- A field marked required in the service definition stays required even when the botocore shape says otherwise.

### Fixed

- Setting a session on a frozen model thaws it for that assignment and freezes it again.
- Session setup walks lists and dicts of models, not only a single model.
- A create call whose response is the whole payload returns that payload.
- A paged list that ends with a metadata-only page no longer treats that page as another resource.

## [0.8.0] - 2024-10-28

### Added

- Add ElastiCache.

### Changed

- Require boto3 and botocore 1.35.50 or newer, and rebuild the generated services.
- `botocraft botocore model --operations` prints the input and output shapes for those operations.

### Fixed

- `KMSKey.objects.list()` returns keys.
- An ELBv2 name collision with another service is renamed.
- A primary model with an alternate name still generates a working manager.
- A manager method with no response class no longer invents one.

## [0.7.0] - 2024-10-18

### Added

- An ECS service can reach the load balancer and target group attached to it.
- A load balancer can read its logging-related attributes. `attributes` returns a dictionary of attribute names and values.

### Changed

- Rebuild the generated services.

## [0.6.0] - 2024-10-15

### Added

- Add KMS.

### Changed

- Rebuild the generated services.

### Fixed

- A manager method that AWS answers with an empty body returns `None` instead of an empty model.

## [0.5.5] - 2024-10-15

### Fixed

- `get_many()` is generated as a callable method again.
- A session set on a read-only model stays on that model.

## [0.5.4] - 2024-10-15

### Added

- An ECR image can reach its repository.

### Changed

- Rebuild the generated services.
- `botocraft botocore` prints list and enum shapes in more detail.

### Fixed

- Every manager method stamps the boto3 session onto the models it returns.
- Copying an AMI accepts a tag specification rather than the wrong tag type.

## [0.5.3] - 2024-10-04

### Added

- `Parameter.objects.get_many()` loads several SSM parameters in one call.

### Changed

- Rebuild the generated services.

### Fixed

- A model with an alternate name gets a manager class named after that public name.
- `Parameter.objects.list()` returns parameters.
- A session can be set on a read-only model.

## [0.5.2] - 2024-10-04

### Changed

- Dependency installs are managed with uv.
- Models loaded from AWS keep the boto3 session, and relations use that same session.
- `Model.objects` is a class property, so you can use it on the class.
- Rebuild the generated services.

## [0.5.1] - 2024-09-13

### Fixed

- Free CPU and free memory on an ECS container instance report the unused capacity.

## [0.5.0] - 2024-09-06

### Added

- Add an EC2 AMI as a primary model.
- An ECS service can report the CPU and memory it requires, the container instances it runs on, and whether it is stable. `wait_until_stable()` blocks until it is.
- An Auto Scaling group can report whether it is stable and wait until it is.
- A container instance can list the tasks running on it.
- `PrimaryBoto3Model.get_waiter()` returns a boto3 waiter for that model.

### Changed

- Require boto3 and botocore 1.35.12 or newer, and rebuild the generated services.
- The ECR image model is named `ECRImage`. The ECS container-instance resource model is named `ContainerInstanceResource`. The Auto Scaling activity model is named `AutoScalingActivity`.

### Fixed

- `Service.scale()` and `AutoScalingGroup.scale()` change the desired count.
- An Auto Scaling group's EC2 instances and launch configuration resolve.
- `Service.roleArn` and `TaskDefinition.taskRoleArn` are optional, matching AWS.
- A property built from a regular expression returns the groups it captured.
- Models and managers with alternate names generate against the public name.

## [0.4.0] - 2024-08-26

### Added

- A model can call manager methods such as `scale()` on itself.
- Scale an ECS service or an Auto Scaling group.
- An Auto Scaling group can report instance status.
- An ECR image can report replication status and scan findings.
- Reboot or terminate an EC2 instance from its manager.

### Changed

- Several ECR manager methods return the full result, including failures, instead of a thinner summary.
- The ECR attribute model is named `ECRAttribute` so it does not collide with the ECS attribute model.

### Fixed

- `Service.tasks` is read again each time, because the set of tasks changes.
- Listing ECS services pages in the groups AWS allows.
- A paginated call that returns a non-list payload no longer crashes.

## [0.3.0] - 2024-08-22

### Added

- Add `botocraft shell`, a Python shell with Botocraft imported.
- Expand ECR beyond the first repository and image models.

## [0.2.4] - 2024-08-07

### Fixed

- A related object is loaded with the same boto3 session as its parent.
- The return type of an Auto Scaling group's targets is the target type AWS sends back.

## [0.2.3] - 2024-08-02

### Added

- Set the boto3 session on a manager and use that session for its calls.

## [0.2.2] - 2024-07-31

### Added

- Start and stop an EC2 instance from `InstanceManager`.

### Changed

- Require a current boto3 and botocore, and rebuild the generated services.

### Fixed

- A model field that AWS returns under a different name still maps back onto the Python attribute.
- The ECS helper that fills in a task definition matches the payload boto3 returns.

## [0.2.1] - 2024-06-12

### Changed

- Rebuild the generated services against botocore 1.34.13.

## [0.2.0] - 2023-12-15

### Added

- First public release of the generator and the hand-written helpers around it.
- Add EC2 VPCs, subnets, security groups, and instances; ECS clusters, services, tasks, and task definitions; ECR repositories; RDS DB instances; Auto Scaling groups; launch templates; and network ACLs.
- `list()` for clusters, services, and task definitions returns those objects. It no longer returns a list of ARNs.
- Models can follow relations to other models, and models that carry a tag map can read and write those tags.

