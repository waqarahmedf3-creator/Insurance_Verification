"""
Authentication service for user management and JWT handling
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import uuid
import structlog

from app.core.config import settings
from app.models.users import User
from app.schemas.auth import UserCreate

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to fetch user by email", error=str(e))
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to fetch user by ID", error=str(e))
            return None
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            # Hash password
            hashed_password = self.get_password_hash(user_data.password)
            
            # Create user
            user = User(
                id=str(uuid.uuid4()),
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                is_active=True
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info("User created successfully", user_id=user.id, email=user.email)
            return user
            
        except Exception as e:
            logger.error("Failed to create user", error=str(e))
            await self.db.rollback()
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_user_by_email(email)
            if not user:
                return None
            
            if not self.verify_password(password, user.hashed_password):
                return None
            
            if not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error("Authentication failed", error=str(e))
            return None
    
    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        try:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode = {
                "sub": user_id,
                "exp": expire,
                "iat": datetime.utcnow()
            }
            
            encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
            return encoded_jwt
            
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError as e:
            logger.error("Token verification failed", error=str(e))
            return None
