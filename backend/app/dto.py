from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator


class VerifyRequest(BaseModel):
    provider: str = Field(..., example="provider_a")
    member_id: str
    dob: date
    last_name: str

    @field_validator("dob")
    @classmethod
    def dob_not_before_1950(cls, v: date) -> date:
        if v < date(1950, 1, 1):
            raise ValueError("Date of Birth cannot be before 1950-01-01")
        return v


class VerifyResponse(BaseModel):
    status: str
    verified_at: datetime
    source: str
    provider_response: dict


class PolicyInfoRequest(BaseModel):
    member_id: str
    dob: date
    last_name: str

    @field_validator("dob")
    @classmethod
    def dob_not_before_1950(cls, v: date) -> date:
        if v < date(1950, 1, 1):
            raise ValueError("Date of Birth cannot be before 1950-01-01")
        return v


class PolicyInfoResponse(BaseModel):
    policy_number: str
    coverage_status: str
    expiry_date: date
    source: str


