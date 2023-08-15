from pydantic import BaseModel, ConfigDict


class Boto3Model(BaseModel):
    model_config = ConfigDict(validate_assignment=True)


class ReadonlyBoto3Model(Boto3Model):
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True
    )
