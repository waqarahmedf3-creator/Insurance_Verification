from datetime import datetime, date
from pydantic import BaseModel, Field


class VerifyRequest(BaseModel):
    provider: str = Field(..., example="provider_a")
    member_id: str
    dob: str
    last_name: str


class VerifyResponse(BaseModel):
    status: str
    verified_at: datetime
    source: str
    provider_response: dict


class PolicyInfoRequest(BaseModel):
    member_id: str
    dob: str
    last_name: str


class PolicyInfoResponse(BaseModel):
    policy_number: str
    coverage_status: str
    expiry_date: date
    source: str


