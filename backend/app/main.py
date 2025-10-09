from datetime import datetime, timedelta
import json
import uuid
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from .dto import VerifyRequest, VerifyResponse, PolicyInfoRequest, PolicyInfoResponse
from .core.config import settings
from .auth import verify_bearer_token
from .provider_client import ProviderClient
from fastapi.middleware.cors import CORSMiddleware
from .core.database import init_redis, close_redis, RedisHelper


app = FastAPI(title="Insurance Verification API", version="0.1.0")

# Dev CORS: fully open for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup"""
    await init_redis()

@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection on shutdown"""
    await close_redis()


def get_provider_client() -> ProviderClient:
    return ProviderClient(api_key=settings.PROVIDER_A_API_KEY)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.options("/api/verify")
async def options_verify() -> JSONResponse:
    return JSONResponse(status_code=204, content=None)

@app.options("/api/policy-info")
async def options_policy_info() -> JSONResponse:
    return JSONResponse(status_code=204, content=None)


@app.post("/api/verify", response_model=VerifyResponse)
async def verify(
    payload: VerifyRequest,
    authorization: str | None = Header(default=None),
    _=Depends(verify_bearer_token),
    provider_client: ProviderClient = Depends(get_provider_client),
    force_refresh: bool = Query(default=False),
) -> VerifyResponse:
    # Generate cache key
    cache_key = f"cache:verify:{hash(str(payload.model_dump()))}"
    
    # Check cache first
    if not force_refresh:
        cached = await RedisHelper.get_string(cache_key)
        if cached:
            data = json.loads(cached)
            return VerifyResponse(**data)

    try:
        provider_response = await provider_client.verify(payload)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Provider error: {exc}")

    now = datetime.utcnow()
    request_id = str(uuid.uuid4())
    
    resp = VerifyResponse(
        status=provider_response.get("status", "unknown"),
        verified_at=now,
        source=provider_response.get("source", "provider"),
        provider_response=provider_response,
    )
    
    # Store in cache
    await RedisHelper.set_with_ttl(cache_key, resp.model_dump_json(), settings.DEFAULT_CACHE_TTL)
    
    # Store verification record
    verification_key = f"verifications:{request_id}"
    verification_data = {
        "id": request_id,
        "request_id": request_id,
        "provider_id": "provider_a",
        "member_key_hash": hash(f"{payload.member_id}{payload.dob}"),
        "normalized_request": payload.model_dump_json(),  # Use JSON string instead
        "provider_response": provider_response,
        "source": "provider",
        "verified_at": now,
        "created_at": now,
        "updated_at": now
    }
    await RedisHelper.set_hash(verification_key, verification_data)
    
    return resp


@app.post("/api/policy-info", response_model=PolicyInfoResponse)
async def policy_info(
    payload: PolicyInfoRequest,
    authorization: str | None = Header(default=None),
    _=Depends(verify_bearer_token),
    provider_client: ProviderClient = Depends(get_provider_client),
    force_refresh: bool = Query(default=False),
) -> PolicyInfoResponse:
    # Generate member hash for policy lookup
    member_hash = hash(f"{payload.member_id}{payload.dob}")
    policy_key = f"policies:{member_hash}"
    cache_key = f"cache:policy:{member_hash}"
    
    # Check cache first
    if not force_refresh:
        cached = await RedisHelper.get_string(cache_key)
        if cached:
            data = json.loads(cached)
            return PolicyInfoResponse(**data)

    try:
        policy = await provider_client.get_policy_info(payload)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Provider error: {exc}")

    # Fallback defaults for robustness in early phases
    policy_number = policy.get("policy_number", "UNKNOWN")
    coverage_status = policy.get("coverage_status", "inactive")
    expiry_date_raw = policy.get("expiry_date") or (datetime.utcnow() + timedelta(days=365)).date()
    # Convert to string for JSON serialization
    expiry_date = expiry_date_raw.isoformat() if hasattr(expiry_date_raw, 'isoformat') else str(expiry_date_raw)
    source = policy.get("source", "provider")
    
    now = datetime.utcnow()

    resp = PolicyInfoResponse(
        policy_number=policy_number,
        coverage_status=coverage_status,
        expiry_date=expiry_date_raw,  # Use original date object for response
        source=source,
    )
    
    # Store in cache
    await RedisHelper.set_with_ttl(cache_key, resp.model_dump_json(), settings.DEFAULT_CACHE_TTL)
    
    # Store policy record
    policy_data = {
        "id": str(uuid.uuid4()),
        "member_id": str(member_hash),
        "policy_number": policy_number,
        "coverage_status": coverage_status,
        "expiry_date": expiry_date,  # Use string version for Redis
        "source": source,
        "verified_at": now,
        "created_at": now,
        "updated_at": now
    }
    await RedisHelper.set_hash(policy_key, policy_data)
    
    return resp


if settings.SENTRY_DSN:
    try:
        import sentry_sdk  # type: ignore

        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
    except Exception:
        pass


