# S3 object bodies are requested through `contents()`, never retained on `S3Object`

`S3Object` is metadata only: `S3ObjectManager.get()`, `list()` and `create()` always return it with `BucketName` and `Key` set, and `get()` drops the `Body` stream. Bytes are fetched only by `S3Object.contents()`, which issues its own `get_object` and returns a `GetObjectOutput` holding an unread `StreamingBody`. Object bodies can be enormous, and a `StreamingBody` is single-use, so a field on a copyable model would be a trap. The cost is one extra request when a caller does `get()` and then `contents()`.

## Considered Options

- **Keep the live `StreamingBody` on the `S3Object` from `get()`.** Rejected: a second `contents()` call would find a consumed stream, and the model would hold an open connection.
- **Read the body eagerly into a `bytes` field.** Rejected: unbounded memory use for large objects.

## Consequences

- `contents()` lives in `S3ObjectMixin` (`botocraft.mixins.s3`), not in the generated `manager_methods`, because the generated `get` returns `S3Object`.
- `S3ObjectManager.create()` returns the `S3Object` that was passed in (previously `PutObjectOutput`), so `ETag` and `VersionId` from `put_object` are no longer returned.
- The generated `create` is annotated `-> S3Object` through `return_type: '"S3Object"'` in `botocraft/data/s3/managers.yml`. The value must be quoted, because an unquoted name becomes a forward reference to a class that is not yet defined and breaks generation. No `botocraft.sync` change was needed. The generated body still builds a `PutObjectOutput` and casts it; the `object_create_return_model` decorator discards that and returns the model.
