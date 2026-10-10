from fastapi import APIRouter, Depends, HTTPException, status, Response
from app.config import get_settings
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models.user import User
from app.services.auth import verify_password, create_access_token, get_current_user, STAFF_ROLES

router = APIRouter(prefix="/auth", tags=["Staff Authentication"])

class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=1024)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    route_scope: int | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    route_scope: int | None = None

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Authenticate staff member and issue JWT session token."""
    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()
    if not user or user.role not in STAFF_ROLES or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token(user.id, user.email, user.role, user.route_scope)
    response.set_cookie("staff_session", token, httponly=True, secure=get_settings().ENVIRONMENT == "production", samesite="strict", max_age=get_settings().JWT_EXPIRE_MINUTES * 60, path="/")
    return TokenResponse(
        access_token=token,
        role=user.role,
        email=user.email,
        route_scope=user.route_scope
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: User = Depends(get_current_user)):
    """Retrieve logged in staff profile."""
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        route_scope=user.route_scope
    )

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("staff_session", path="/")
    return {"status": "signed_out"}
