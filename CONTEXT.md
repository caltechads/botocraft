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

## Amplify Hosting

**Amplify app**:
The Amplify Hosting root resource. Botocraft's unit of ownership for this service.
_Avoid_: Amplify artifact, Amplify project

**Amplify branch**:
A named deploy target that belongs to one Amplify app.
_Avoid_: environment, git branch

**Manual deploy**:
Publishing an already-built zip or S3 prefix onto an Amplify branch. Amplify does not compile the source.
_Avoid_: build, release job

**Amplify build**:
An Amplify-run compile of repository source. Out of scope for this service.
_Avoid_: manual deploy, job

**Amplify artifact**:
A file produced by an Amplify job. Readable only. Not something Botocraft creates or updates.
_Avoid_: Amplify app, deployment package

**Amplify job**:
The record of work on an Amplify branch, including a manual deploy. Botocraft can read it and delete it. Botocraft does not start or stop it.
_Avoid_: Amplify build, release
