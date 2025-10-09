from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict
from .dto import VerifyRequest, PolicyInfoRequest


class ProviderClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def verify(self, payload: VerifyRequest) -> Dict[str, Any]:
        # Stubbed provider response
        return {
            "status": "verified",
            "policy_number": "POL12345",
            "coverage_status": "active",
            "expiry_date": "2024-12-31",
            "provider": "test_provider",
            "source": "provider" if self.api_key else "mock",
        }

    async def get_policy_info(self, payload: PolicyInfoRequest) -> Dict[str, Any]:
        # Stubbed policy info
        expiry = (datetime.utcnow() + timedelta(days=365)).date().isoformat()
        return {
            "policy_number": f"POL-{payload.member_id[-4:]}-001",
            "coverage_status": "active",
            "expiry_date": expiry,
            "source": "provider" if self.api_key else "mock",
        }


