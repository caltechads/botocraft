# Common Manager Patterns

Repo truth from current `botocraft/data/*/managers.yml`.

## `get` buckets

### 1. Plain `describe_*` with plural ID arg

Use when boto3 exposes only describe/list-style operation but accepts a list of
IDs or ARNs. Botocraft should usually expose singular public arg and transform
to one-item list.

Example shape:

```yaml
Vpc:
  methods:
    get:
      boto3_name: describe_vpcs
      args:
        VpcIds:
          required: true
          rename: VpcId
          python_type: str
          source_arg: "[VpcId]"
```

Seen on EC2 VPCs, subnets, security groups, network ACLs, many autoscaling and
RDS-style describe calls.

### 2. Plain `get_*` with `response_attr`

Use when boto3 already has direct singular getter.

Example families:

- IAM `get_group -> Group`
- IAM `get_policy -> Policy`
- IAM `get_instance_profile -> InstanceProfile`

### 3. Plain `describe_*` with `response_attr`

Use when describe returns collection field and generator can take first/only
element cleanly.

Example families:

- Application Auto Scaling policies/targets/actions
- ElastiCache clusters/subnet groups/users

### 4. Decorated `describe_*`

Use decorator when raw response shape is not final Botocraft object surface.

Common reasons:

- wrapper collection must collapse to single model
- tags need follow-up enrichment
- reservations must flatten to instances
- response object needs conversion to different public model

Examples:

- EC2 `describe_instances` + `ec2_instance_only`
- ECR repository get + tag enrichment decorator
- DocDB single-object describe + include-tags decorator
- Events describe response -> public rule model

### 5. Special-case getters

These are signals to slow down and inspect:

- `batch_get_image`
- `get_parameters`
- `list_findings` used as de facto get-by-arns

## `list` buckets

### 1. Plain paginated `describe_*` full response

Use when paginator yields full model objects already.

Examples:

- EC2 VPCs/subnets/security groups/network ACLs
- autoscaling groups
- many classic describe APIs

### 2. Plain `list_*` with `response_attr`

Use when API returns summaries or direct object list.

Examples:

- IAM list methods
- EventBridge buses/rules
- Bedrock foundation models

### 3. Decorated identifier list

Use when AWS returns ARNs or IDs but Botocraft should return models.

Examples:

- ECS `list_services` -> service ARNs -> models
- ECS `list_clusters` -> cluster ARNs -> models
- ECS `list_task_definitions` -> task definition models
- ECR `list_images` -> image IDs -> models

### 4. Decorated enrichment list

Use when list returns objects but missing tags or other user-facing fields.

Examples:

- DocDB list + include-tags
- ElastiCache user/user-group tag enrichment
- logs log-group tag conversion

### 5. Context-required list

Some list methods are only meaningful with required context:

- S3 objects need `Bucket`
- EventBridge targets need `Rule`

Do not force global list semantics when AWS surface is inherently scoped.

### 6. Enumerate then describe via manager mixin

Use a manager mixin when AWS splits global enumeration from full-object describe
and the generated `list` method would otherwise require a mandatory identifier
argument.

OpenSearch domain example:

- `list_domain_names` returns lightweight `DomainInfo` items
- `describe_domains` returns full `DomainStatus` objects
- `describe_domains` requires a non-empty `DomainNames` argument, so a generated
  zero-arg `list()` is wrong
- correct pattern: handwritten manager mixin calls `list_domain_names`, extracts
  names, then calls `describe_domains`, then applies any enrichment like tags

This is a manager-mixin case, not a simple decorator, because the public
Botocraft `list()` needs multiple AWS calls before it has model instances.

## Non-CRUD helpers (attach, routes, associate, egress)

Repo EC2 patterns for mutations beyond CRUDL are defined in YAML with careful
`return_type` / `response_attr` choices. Wrong choices produce broken generated
code (especially empty boto outputs vs `Return`).

Load `generator-yaml-pitfalls.md` before adding helpers such as:

- `attach` / `detach` on volumes or gateways
- `create_route` / `delete_route` / `replace_route`
- `associate` / `disassociate` on route tables
- `authorize_egress` / `revoke_egress` on security groups

## Rule of thumb

- Prefer decorator over mixin when one call plus reshaping is enough.
- Prefer mixin when list/get needs several AWS calls or higher-level workflow.
- Keep Botocraft public contract model-centric even when boto3 is identifier-
  centric.
