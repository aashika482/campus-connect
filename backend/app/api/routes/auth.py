# Signing up and in. Every account proves it owns its college mailbox:
#   - Sign in with Microsoft (the university's Microsoft 365): POST /microsoft creates the account on
#     first use (name from the university directory) and signs in afterwards
#   - or an emailed code: POST /register/code, then POST /register with that code
# Password logins (e.g. alumni, whose college account is closed) take a second step: a code emailed to
# them or from their authenticator app, remembered on that browser for 30 days if they ask.
# Faculty named as coordinators in the DSW's records become coordinators on these verified sign-ins.

import hmac
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update

from app.db.database import get_db
from app.core.config import settings
from app.core.governance import claim_coordinator_invites
from app.core.mail import send_mail
from app.models.user import User, AccountType, EmailCode
from app.models.club import ClubRequest, ClubRequestStatus
from app.models.notification import Notification
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token, decode_token,
    new_code, hash_code, verify_totp, create_challenge_token, create_device_token, device_token_valid,
    verify_microsoft_id_token,
)
from app.schemas.user import (
    LoginRequest, LoginVerify, LoginResponse, ChallengeRequest, EmailRequest, MicrosoftLogin,
    RegisterRequest, TokenResponse, RefreshRequest, UserOut, AuthConfig,
)

router = APIRouter()
CODE_MINUTES, CODE_TRIES, RESEND_SECONDS = 10, 5, 60
LOGIN_TRIES, LOCK_MINUTES = 5, 15
# The same answer for a wrong email, a wrong password and a Microsoft-only account, so the login form
# can't be used to find out who has an account
BAD_LOGIN = "Wrong email or password. If you joined with Microsoft, use Sign in with Microsoft."


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def _make_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.account_type.value),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


async def _start_session(db: AsyncSession, user: User, device_token: str | None = None) -> LoginResponse:
    """A verified sign-in: claim any coordinator roles the DSW's records give them, then the tokens."""
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is deactivated")
    if await claim_coordinator_invites(db, user):
        await db.commit()
        await db.refresh(user)
    t = _make_token_response(user)
    return LoginResponse(access_token=t.access_token, refresh_token=t.refresh_token, user=t.user, device_token=device_token)


# ── Emailed codes ────────────────────────────────────────
async def _send_code(db: AsyncSession, email: str, purpose: str) -> None:
    """Email a fresh code, unless an unused one went out under a minute ago (it's still in their inbox)."""
    recent = (await db.execute(select(EmailCode.id).where(
        EmailCode.email == email, EmailCode.purpose == purpose, EmailCode.used == False,  # noqa: E712
        EmailCode.created_at > datetime.now(timezone.utc) - timedelta(seconds=RESEND_SECONDS),
    ).limit(1))).first()
    if recent:
        return
    # Housekeeping: codes older than a day are useless
    await db.execute(delete(EmailCode).where(EmailCode.created_at < datetime.now(timezone.utc) - timedelta(days=1)))
    await db.execute(update(EmailCode).where(EmailCode.email == email, EmailCode.purpose == purpose,
                                             EmailCode.used == False).values(used=True))  # noqa: E712  (one live code)
    code = new_code()
    db.add(EmailCode(email=email, purpose=purpose, code_hash=hash_code(code),
                     expires_at=datetime.now(timezone.utc) + timedelta(minutes=CODE_MINUTES)))
    await db.commit()
    what = "create your CamPulse account" if purpose == "signup" else "finish signing in to CamPulse"
    await send_mail(email, f"Your CamPulse code: {code}",
                    f"Your code to {what} is {code}. It works for {CODE_MINUTES} minutes.\n\n"
                    "If you didn't ask for it, ignore this email.")


async def _use_code(db: AsyncSession, email: str, purpose: str, code: str) -> bool:
    row = (await db.execute(select(EmailCode).where(
        EmailCode.email == email, EmailCode.purpose == purpose, EmailCode.used == False,  # noqa: E712
        EmailCode.expires_at > datetime.now(timezone.utc),
    ).order_by(EmailCode.id.desc()).limit(1))).scalar_one_or_none()
    if row is None or row.attempts >= CODE_TRIES:
        return False
    row.attempts += 1
    if not hmac.compare_digest(row.code_hash, hash_code(code)):
        await db.commit()   # count the wrong try
        return False
    row.used = True
    return True


# ── Config ───────────────────────────────────────────────
@router.get("/config", response_model=AuthConfig)
async def auth_config():
    """Which email domains can sign up, and as what; and whether Microsoft sign-in is set up."""
    return AuthConfig(
        email_domains=settings.email_domains,
        microsoft_client_id=settings.MICROSOFT_CLIENT_ID if settings.microsoft_enabled else None,
        microsoft_tenant_id=settings.MICROSOFT_TENANT_ID if settings.microsoft_enabled else None,
    )


# ── Sign in with Microsoft ───────────────────────────────
@router.post("/microsoft", response_model=LoginResponse)
async def microsoft_sign_in(payload: MicrosoftLogin, db: AsyncSession = Depends(get_db)):
    """Signs in, creating the account on first use: name from the university directory, student or
    faculty from the email's domain. Students then finish their profile (profile_complete)."""
    claims = await verify_microsoft_id_token(payload.id_token)
    email = str(claims.get("email") or claims.get("preferred_username") or "").strip().lower()
    kind = settings.account_kind_for(email)
    if kind is None:
        raise HTTPException(status_code=403, detail="Sign in with your MUJ Microsoft account")
    user = await _get_user_by_email(db, email)
    if user is None:
        user = User(name=str(claims.get("name") or email.split("@")[0]).strip()[:120], email=email,
                    password=None, account_type=AccountType(kind))
        db.add(user)
        await db.flush()
        await _notify_waiting_club_requests(db, user)
        await db.commit()
        await db.refresh(user)
    return await _start_session(db, user)


# ── Sign up with an emailed code ─────────────────────────
def _college_kind(email: str) -> str:
    kind = settings.account_kind_for(email)
    if kind is None:
        allowed = ", ".join(f"@{d}" for ds in settings.email_domains.values() for d in ds)
        raise HTTPException(status_code=400, detail=f"Sign up with your college email ({allowed})")
    return kind


@router.post("/register/code", status_code=202)
async def send_signup_code(payload: EmailRequest, db: AsyncSession = Depends(get_db)):
    """Step 1: email a code to the address, proving they own it."""
    _college_kind(payload.email)
    if await _get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered. Sign in instead.")
    await _send_code(db, payload.email, "signup")
    return {"sent": True}


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Step 2: the code and the account details. The email's domain makes it a student or faculty
    account; every other account type (alumni, DSW, platform admin) is assigned later, never chosen."""
    kind = _college_kind(payload.email)
    if await _get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if not await _use_code(db, payload.email, "signup", payload.code):
        raise HTTPException(status_code=400, detail="That code is wrong or has expired. Ask for a new one.")

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
    await db.flush()
    await _notify_waiting_club_requests(db, user)
    await claim_coordinator_invites(db, user)
    await db.commit()
    await db.refresh(user)
    return _make_token_response(user)


async def _notify_waiting_club_requests(db: AsyncSession, user: User) -> None:
    """A new faculty account: tell them about club requests that were waiting for them to join."""
    if user.account_type != AccountType.faculty:
        return
    waiting = (await db.execute(select(ClubRequest.name).where(
        ClubRequest.coordinator_email == user.email,
        ClubRequest.status == ClubRequestStatus.awaiting_coordinator,
    ))).scalars().all()
    for name in waiting:
        Notification.send(db, [user.id], "club_request",
                          f"You're named faculty coordinator of a proposed club, {name}. Please confirm or decline.")


# ── Password login, then the second step ─────────────────
@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """A correct password returns the second step to do (a challenge), unless this browser was remembered."""
    user = await _get_user_by_email(db, payload.email)
    now = datetime.now(timezone.utc)
    if user and user.locked_until and user.locked_until > now:
        minutes = int((user.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(status_code=429, detail=f"Too many wrong passwords. Try again in {minutes} minutes.")
    if not user or not verify_password(payload.password, user.password):
        if user:
            user.failed_logins += 1
            if user.failed_logins >= LOGIN_TRIES:
                user.failed_logins, user.locked_until = 0, now + timedelta(minutes=LOCK_MINUTES)
            await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=BAD_LOGIN)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is deactivated")
    user.failed_logins, user.locked_until = 0, None
    if device_token_valid(payload.device_token, user.id, user.password):
        return await _start_session(db, user)
    user.failed_codes = 0
    await db.commit()
    method = "totp" if user.second_factor == "totp" and user.totp_secret else "email"
    if method == "email":
        await _send_code(db, user.email, "login")
    return LoginResponse(second_step=method, challenge=create_challenge_token(user.id))


async def _challenged_user(db: AsyncSession, challenge: str) -> User:
    user = await db.get(User, int(decode_token(challenge, "2fa")["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in again")
    return user


@router.post("/login/verify", response_model=LoginResponse)
async def login_verify(payload: LoginVerify, db: AsyncSession = Depends(get_db)):
    """The code from their authenticator app, or the one emailed to them (always accepted, so a lost
    phone isn't a locked account)."""
    user = await _challenged_user(db, payload.challenge)
    if user.failed_codes >= CODE_TRIES:
        raise HTTPException(status_code=429, detail="Too many wrong codes. Sign in with your password again.")
    if not (verify_totp(user.totp_secret, payload.code) or await _use_code(db, user.email, "login", payload.code)):
        user.failed_codes += 1
        await db.commit()
        raise HTTPException(status_code=400, detail="That code is wrong or has expired")
    user.failed_codes = 0
    await db.commit()
    device = create_device_token(user.id, user.password) if payload.remember else None
    return await _start_session(db, user, device_token=device)


@router.post("/login/email-code", status_code=202)
async def login_email_code(payload: ChallengeRequest, db: AsyncSession = Depends(get_db)):
    """Email a (new) code for the second step: to resend it, or instead of the authenticator app."""
    user = await _challenged_user(db, payload.challenge)
    await _send_code(db, user.email, "login")
    return {"sent": True}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    decoded = decode_token(payload.refresh_token, "refresh")
    user_id = int(decoded["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Sign in again")
    return _make_token_response(user)


@router.post("/logout")
async def logout():
    # Stateless JWT — client should delete tokens.
    # For refresh token revocation, store a blocklist in Redis.
    return {"message": "Logged out successfully"}
