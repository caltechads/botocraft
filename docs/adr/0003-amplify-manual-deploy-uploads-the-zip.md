# Amplify manual deploy uploads the zip

`CreateDeployment` returns a presigned `zipUploadUrl`. Amplify does not accept the zip bytes. Botocraft's manual deploy helper PUTs the local zip to that URL, then calls `StartDeployment` with the returned `jobId`. Callers do not perform the upload themselves. `StartJob` and `StopJob` stay out of the service, so this helper is not an Amplify build.
