from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.core.deps import get_current_active_user
from app.core.security import hash_password, verify_password, new_totp_secret, totp_uri, verify_totp
from app.schemas.user import UserOut, UserUpdate, PasswordUpdate, TotpSetup, SecondStepUpdate

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_active_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    data = payload.model_dump(exclude_unset=True)
    if "interests" in data and data["interests"] is not None:
        data["interests"] = ",".join(data["interests"])
    for k, v in data.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


# ── Sign-in security ─────────────────────────────────────
@router.post("/me/password", response_model=UserOut)
async def set_password(
    payload: PasswordUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Add a password (accounts made with Microsoft, e.g. to keep access as alumni) or change it.
    Changing it also forgets every remembered browser."""
    if user.has_password and not verify_password(payload.current_password or "", user.password):
        raise HTTPException(status_code=400, detail="Your current password is wrong")
    first = not user.has_password
    user.password = hash_password(payload.new_password)
    AuditLog.record(db, user, "user.add_password" if first else "user.change_password", "user", user.id)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/me/two-step/totp", response_model=TotpSetup)
async def start_totp(user: User = Depends(get_current_active_user)):
    """A new authenticator secret to add to their app. Nothing changes until they confirm a code."""
    secret = new_totp_secret()
    return TotpSetup(secret=secret, uri=totp_uri(secret, user.email))


@router.put("/me/two-step", response_model=UserOut)
async def choose_second_step(
    payload: SecondStepUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """The second step after a password: emailed codes, or an authenticator app (confirmed with a code)."""
    if payload.method == "totp":
        if not (payload.secret and payload.code and verify_totp(payload.secret, payload.code)):
            raise HTTPException(status_code=400, detail="That code doesn't match. Check the app and try again.")
        user.totp_secret = payload.secret
    else:
        user.totp_secret = None
    user.second_factor = payload.method
    AuditLog.record(db, user, "user.second_step", "user", user.id, method=payload.method)
    await db.commit()
    await db.refresh(user)
    return user
