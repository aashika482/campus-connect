from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, update

from app.db.database import get_db
from app.models.club import Club
from app.models.membership import Membership
from app.models.user import User
from app.core.deps import get_current_active_user, require_club_member
from app.schemas.event import ClubOut, ClubCreate, ClubMembershipStatus

router = APIRouter()


@router.get("/", response_model=list[ClubOut])
async def list_clubs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Club).order_by(Club.name))
    return result.scalars().all()


@router.get("/{club_id}", response_model=ClubOut)
async def get_club(club_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@router.post("/", response_model=ClubOut, status_code=201)
async def create_club(
    payload: ClubCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    club = Club(**payload.model_dump(exclude={"tags"}), tags=",".join(payload.tags))
    db.add(club)
    await db.flush()
    return club


# ── Membership ───────────────────────────────────────────
@router.post("/{club_id}/join", response_model=ClubMembershipStatus)
async def join_club(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    existing = await db.execute(
        select(Membership).where(Membership.user_id == user.id, Membership.club_id == club_id)
    )
    if not existing.scalar_one_or_none():
        db.add(Membership(user_id=user.id, club_id=club_id))
        new_count = club.member_count + 1
        await db.execute(update(Club).where(Club.id == club_id).values(member_count=new_count))
        club.member_count = new_count

    return ClubMembershipStatus(club_id=club_id, is_member=True, member_count=club.member_count)


@router.delete("/{club_id}/join", response_model=ClubMembershipStatus)
async def leave_club(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    await db.execute(
        delete(Membership).where(Membership.user_id == user.id, Membership.club_id == club_id)
    )
    new_count = max(0, club.member_count - 1)
    await db.execute(update(Club).where(Club.id == club_id).values(member_count=new_count))

    return ClubMembershipStatus(club_id=club_id, is_member=False, member_count=new_count)


@router.get("/me/joined", response_model=list[int])
async def my_clubs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Membership.club_id).where(Membership.user_id == user.id)
    )
    return [r for r in result.scalars().all()]
