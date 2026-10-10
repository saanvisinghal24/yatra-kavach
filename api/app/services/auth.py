from datetime import datetime, timezone, timedelta
from typing import Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.db import get_db
from app.models.user import User

settings = get_settings()
ph = PasswordHasher()
security = HTTPBearer(auto_error=False)
STAFF_ROLES = frozenset(("admin", "health", "police", "rescue", "volunteer"))

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHashError):
        return False

def create_access_token(user_id: int, email: str, role: str, route_scope: Optional[int] = None) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "route_scope": route_scope,
        "exp": expires
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM], options={"require": ["exp", "sub"]})
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isascii() or not subject.isdecimal() or not 0 < int(subject) <= 2147483647:
            raise jwt.InvalidTokenError("Invalid subject")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials."
        )

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials if credentials else request.cookies.get("staff_session")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required."
        )
    payload = decode_access_token(token)
    user_id = int(payload["sub"])
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    return user

async def require_control_user(user: User = Depends(get_current_user)) -> User:
    if user.role not in ('admin','health','police','rescue'):
        raise HTTPException(403, 'Control-room role required')
    return user

def enforce_route(user, route_id):
    if user.route_scope is not None and user.route_scope != route_id:
        raise HTTPException(403, 'Outside staff route scope')
