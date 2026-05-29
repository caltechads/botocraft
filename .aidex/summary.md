## Architecture
Classic SES service added as generated Botocraft service from source-of-truth YAML under botocraft/data/ses. Public models/managers use SES-prefixed names to avoid collisions with existing sesv2 surface (for example SESConfigurationSet, SESTemplate, SESReceiptRuleSet). Handwritten behavior lives in botocraft/mixins/ses.py and is responsible for classic SES irregularities where nested request/response shapes are more naturally handled from raw boto payloads than from generated wrappers alone.

## Patterns
SES authoring pattern: when classic AWS APIs use nested request payloads like create_configuration_set(ConfigurationSet={...}) or describe payloads that bury resource identity under nested Name fields, prefer handwritten manager mixins over forcing awkward generated method signatures. Also preempt cross-service collisions by aliasing public models and forcing generation of secondary models used only by extra_fields on primary models.
