# EC2 Case Study

EC2 is advanced reference, not default always-loaded context.

## Why EC2 matters

EC2 concentrates many patterns future services hit:

- several strong primary models
- primary and secondary naming collisions
- identifier-only and wrapped describe/list results
- manager mixins for odd create/update args
- relation-rich models
- lifecycle helpers beyond CRUDL

## Primary-model selection

Good first-pass EC2 models were clear resources with usable identity and read
surface:

- `Vpc`
- `Subnet`
- `SecurityGroup`
- `Instance`
- `Image -> AMI`

Not every useful shape became primary. Many remained nested helpers.

## Alternate naming

`Image` became `AMI` because `Image` already exists in ECR and public meaning is
clearer for EC2 callers.

EC2 also renames many secondary shapes, such as:

- `BlockDeviceMapping -> EC2BlockDeviceMapping`
- `LaunchTemplateSpecification -> EC2LaunchTemplateSpecification`

## `get` and `list` shaping

EC2 uses plain describe patterns for many resources:

- `describe_vpcs`
- `describe_subnets`
- `describe_security_groups`

But `describe_instances` returns Reservations, not instances directly.
That requires decorators:

- `ec2_instance_only`
- `ec2_instances_only`

## Tags

EC2 keeps model field named `Tags`, but create/update often must translate that
to `TagSpecifications`. That logic lives naturally in manager mixin:

- `EC2TagsManagerMixin`

## Relations

EC2 shows dense but still readable relations:

- instance -> AMI, VPC, subnet, security groups, network interfaces
- VPC -> subnets, security groups, network ACLs
- subnet -> VPC, instances

Prefer mapping-based relations. Regex is exception, not baseline.

## Generic lifecycle helpers

EC2 managers add real ergonomic methods beyond CRUDL:

- start/stop/reboot/terminate
- deregistration protection
- lock/unlock flows

Add these only when operation clearly scopes to model identity and improves
object API meaningfully.

Recent EC2 slices also added YAML-only helpers with strict return-shape rules:

- routes: `create_route` uses `Return`; `delete_route` / `replace_route` use
  empty output (`return_type: None`)
- volumes: `attach` / `detach` use top-level `VolumeAttachment` (`response_attr: None`);
  `update` uses nested `VolumeModification` plus `EC2VolumeModification` alias
- route tables: `associate` returns `AssociateRouteTableResult`; `disassociate`
  is empty output
- security groups: `authorize_egress` / `revoke_egress` mirror ingress `Return`

Load `generator-yaml-pitfalls.md` before adding similar helpers on other services.

## Takeaway

If new service feels EC2-like, slow down. Start narrow, load collision and
manager-pattern references, then escalate only specific complex pieces.
