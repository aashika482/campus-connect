from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import time

import bcrypt
import httpx
import pyotp
import jwt
from jwt import PyJWTError as JWTError
from fastapi import HTTPException, status

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str | None) -> bool:
    """False for accounts without a password (they sign in with Microsoft)."""
    return bool(hashed) and bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    payload = data.copy()
    payload.update({
        "exp": datetime.now(timezone.utc) + expires_delta,
        "type": token_type,
    })
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        {"sub": str(user_id), "role": role},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id)},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )


def decode_token(token: str, expected_type: str) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise credentials_error
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
        return payload
    except JWTError:
        raise credentials_error


# ── One-time codes (emailed) ─────────────────────────────
def new_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_code(code: str) -> str:
    """Codes are stored hashed (keyed with the JWT secret), like passwords but cheap: they live 10 minutes."""
    return hmac.new(settings.JWT_SECRET_KEY.encode(), code.strip().encode(), hashlib.sha256).hexdigest()


# ── Authenticator apps (TOTP, RFC 6238) ──────────────────
def new_totp_secret() -> str:
    return pyotp.random_base32()


def totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="CamPulse")


def verify_totp(secret: str | None, code: str) -> bool:
    return bool(secret) and pyotp.TOTP(secret).verify(code.strip(), valid_window=1)


# ── Short-lived and device tokens ────────────────────────
def create_challenge_token(user_id: int) -> str:
    """Between a correct password and the second step: proves the password part was done (10 minutes)."""
    return _create_token({"sub": str(user_id)}, timedelta(minutes=10), "2fa")


def _password_stamp(password_hash: str | None) -> str:
    return hashlib.sha256((password_hash or "").encode()).hexdigest()[:16]


def create_device_token(user_id: int, password_hash: str | None) -> str:
    """"Remember this browser": skips the second step for 30 days, until the password changes."""
    return _create_token({"sub": str(user_id), "pw": _password_stamp(password_hash)}, timedelta(days=30), "device")


def device_token_valid(token: str | None, user_id: int, password_hash: str | None) -> bool:
    if not token:
        return False
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return False
    return (payload.get("type") == "device" and payload.get("sub") == str(user_id)
            and payload.get("pw") == _password_stamp(password_hash))


# ── Sign in with Microsoft ───────────────────────────────
_jwks: dict = {"keys": [], "fetched": 0.0}


async def _microsoft_key(kid: str) -> dict | None:
    """Microsoft's public signing key with this id (cached for 6 hours; refetched for a new id)."""
    def find():
        return next((k for k in _jwks["keys"] if k.get("kid") == kid), None)
    if find() is None or time.time() - _jwks["fetched"] > 6 * 3600:
        url = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/discovery/v2.0/keys"
        async with httpx.AsyncClient(timeout=10) as client:
            _jwks["keys"] = (await client.get(url)).raise_for_status().json()["keys"]
        _jwks["fetched"] = time.time()
    return find()


async def verify_microsoft_id_token(id_token: str) -> dict:
    """The claims of a Microsoft ID token, after checking its signature, audience (our app), issuer
    (the university's tenant) and expiry. Raises 401 if any check fails."""
    if not settings.microsoft_enabled:
        raise HTTPException(status_code=503, detail="Sign in with Microsoft isn't set up on this server")
    invalid = HTTPException(status_code=401, detail="Microsoft sign-in couldn't be verified. Try again.")
    try:
        key = await _microsoft_key(jwt.get_unverified_header(id_token).get("kid", ""))
        if key is None:
            raise invalid
        return jwt.decode(
            id_token, jwt.PyJWK(key).key, algorithms=["RS256"], audience=settings.MICROSOFT_CLIENT_ID,
            issuer=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/v2.0",
        )
    except (JWTError, httpx.HTTPError, KeyError):
        raise invalid
