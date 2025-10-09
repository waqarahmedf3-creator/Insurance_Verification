from typing import Optional
from fastapi import Header, HTTPException
from .core.config import settings


async def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not settings.JWT_SECRET:
        return  # Auth disabled in early phase if secret not provided
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    # Minimal check: token equals secret for early development; replace with JWT later
    if token != settings.JWT_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")


