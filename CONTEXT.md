# Botocraft

Botocraft models AWS services as Python objects and managers. This glossary
captures project-specific language that affects the public model.

## AWS Managed Grafana

**AMG service account token**:
A one-time-visible credential created for an AWS Managed Grafana service
account. Botocraft uses this term for the token returned to automation that
needs to call Grafana HTTP APIs.
_Avoid_: client token

**AMG service account token rotation**:
Creating a replacement AMG service account token and deleting the previous token
id supplied by the caller. Botocraft treats token update as rotation because AWS
Managed Grafana has no token update operation.
_Avoid_: token update

**Workspace API key**:
Legacy AWS Managed Grafana API key. Botocraft does not use this for the AMG
token rotation workflow.
_Avoid_: client token
