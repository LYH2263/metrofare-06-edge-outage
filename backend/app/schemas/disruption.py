from pydantic import BaseModel, Field


class DisruptionCreate(BaseModel):
    a: str = Field(min_length=1)
    b: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=200)


class DisruptionLift(BaseModel):
    a: str = Field(min_length=1)
    b: str = Field(min_length=1)
