from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.user import User, UserRole
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.schemas.user import (
    LoginRequest, RegisterStudentRequest, RegisterMemberRequest,
    TokenResponse, RefreshRequest, UserOut,
)

router = APIRouter()


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def _make_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await _get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.role != payload.role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"This account is registered as '{user.role.value}', not '{payload.role.value}'")
    return _make_token_response(user)


@router.post("/register/student", response_model=TokenResponse, status_code=201)
async def register_student(payload: RegisterStudentRequest, db: AsyncSession = Depends(get_db)):
    if await _get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role=UserRole.student,
        reg_no=payload.reg_no,
        course=payload.course,
        phone=payload.phone,
        interests=",".join(payload.interests) if payload.interests else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _make_token_response(user)


@router.post("/register/member", response_model=TokenResponse, status_code=201)
async def register_member(payload: RegisterMemberRequest, db: AsyncSession = Depends(get_db)):
    if await _get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role=UserRole.member,
        club_name=payload.club_name,
        position=payload.position,
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
