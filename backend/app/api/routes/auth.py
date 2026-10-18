from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.config import settings
from app.models.user import User, AccountType
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.schemas.user import (
    LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, UserOut, AuthConfig,
)

router = APIRouter()


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def _make_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.account_type.value),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.get("/config", response_model=AuthConfig)
async def auth_config():
    """Which email domains can sign up, and as what (shown on the sign-up page)."""
    return AuthConfig(email_domains=settings.email_domains)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await _get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _make_token_response(user)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Sign up with a college email. Its domain makes the account a student or faculty one;
    every other account type (alumni, DSW, platform admin) is assigned later, never chosen."""
    kind = settings.account_kind_for(payload.email)
    if kind is None:
        allowed = ", ".join(f"@{d}" for ds in settings.email_domains.values() for d in ds)
        raise HTTPException(status_code=400, detail=f"Sign up with your college email ({allowed})")
    if await _get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    is_student = kind == "student"
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        account_type=AccountType(kind),
        phone=payload.phone,
        # Academic details only mean something for students
        reg_no=payload.reg_no if is_student else None,
        course=payload.course if is_student else None,
        interests=",".join(payload.interests) if is_student and payload.interests else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _make_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    decoded = decode_token(payload.refresh_token, "refresh")
    user_id = int(decoded["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return _make_token_response(user)


@router.post("/logout")
async def logout():
    # Stateless JWT — client should delete tokens.
    # For refresh token revocation, store a blocklist in Redis.
    return {"message": "Logged out successfully"}
