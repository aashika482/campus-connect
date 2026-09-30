# Signed Cloudinary uploads.
#
# The browser still uploads the file straight to Cloudinary (the file never passes
# through this server), but Cloudinary only accepts it with a signature that only
# this server can make, because it needs CLOUDINARY_API_SECRET. So only logged-in
# club admins can upload, and only with the options signed here (folder + formats).

import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.deps import require_club_member
from app.models.user import User
from app.schemas.event import UploadStatus, UploadSignature

router = APIRouter()

POSTER_FOLDER = "campulse/posters"
POSTER_FORMATS = "jpg,jpeg,png,webp"


def _sign(params: dict[str, str]) -> str:
    """Cloudinary's signature: SHA-1 of the params sorted by name as "a=1&b=2", with the
    API secret appended. https://cloudinary.com/documentation/authentication_signatures"""
    to_sign = "&".join(f"{k}={params[k]}" for k in sorted(params))
    return hashlib.sha1((to_sign + settings.CLOUDINARY_API_SECRET).encode()).hexdigest()


@router.get("/status", response_model=UploadStatus)
async def upload_status(user: User = Depends(require_club_member)):
    """Lets the poster field decide between upload and paste-a-URL mode."""
    return UploadStatus(enabled=settings.cloudinary_enabled)


@router.post("/signature", response_model=UploadSignature)
async def upload_signature(user: User = Depends(require_club_member)):
    """A one-time signature for one poster upload. Cloudinary rejects it after 1 hour."""
    if not settings.cloudinary_enabled:
        raise HTTPException(status_code=503, detail="Image uploads aren't configured on the server")
    # Every param here must be sent to Cloudinary unchanged, or the signature won't match
    params = {
        "allowed_formats": POSTER_FORMATS,
        "folder": POSTER_FOLDER,
        "timestamp": str(int(time.time())),
    }
    return UploadSignature(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        signature=_sign(params),
        **params,
    )
