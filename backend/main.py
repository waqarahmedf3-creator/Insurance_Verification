"""
Insurance Verification System - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import structlog
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis
from app.api.routes import verification, policy_info, auth, chatbot, policies
from app.core.middleware import setup_middleware

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

logger = structlog.get_logger()

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Insurance Verification System")
    await init_db()
    await init_redis()
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(
    title="Insurance Verification System",
    description="Secure insurance verification with AI chatbot assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
setup_middleware(app)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(verification.router, prefix="/api", tags=["verification"])
app.include_router(policy_info.router, prefix="/api", tags=["policy-info"])
app.include_router(chatbot.router, prefix="/api", tags=["chatbot"])
app.include_router(policies.router, prefix="/api", tags=["policies"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Insurance Verification System API", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
