import asyncio
import os
import pytest
from httpx import AsyncClient
from fastapi import status

os.environ.setdefault("JWT_SECRET", "dev-secret")

from app.main import app  # noqa: E402


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_verify_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "provider": "provider_a",
            "member_id": "1234567890",
            "dob": "1990-01-01",
            "last_name": "Doe",
        }
        headers = {"Authorization": "Bearer dev-secret"}
        resp = await client.post("/api/verify", json=payload, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] in {"verified", "unknown"}
        assert "provider_response" in data


@pytest.mark.asyncio
async def test_policy_info_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "member_id": "1234567890",
            "dob": "1990-01-01",
            "last_name": "Doe",
        }
        headers = {"Authorization": "Bearer dev-secret"}
        resp = await client.post("/api/policy-info", json=payload, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "policy_number" in data
        assert data["coverage_status"] in {"active", "inactive"}


