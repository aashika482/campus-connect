from datetime import datetime
from typing import Any

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class AuditLog(Base):
    """Who did what to which record, and when. Written for every governance action
    (role requests and reviews, account-type changes, club creation, hot flags) and,
    in later phases, approvals and payments. Append-only: nothing updates or deletes rows.
    """
    __tablename__ = "audit_log"

    id:          Mapped[int]             = mapped_column(primary_key=True)
    # Kept when the actor's account is deleted, so history survives
    actor_id:    Mapped[int | None]      = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action:      Mapped[str]             = mapped_column(String(60), index=True)   # e.g. "club_role.approve"
    entity_type: Mapped[str]             = mapped_column(String(40))               # "club_role", "user", "club", "event"
    entity_id:   Mapped[int | None]      = mapped_column(Integer, nullable=True)
    details:     Mapped[dict[str, Any]]  = mapped_column(JSONB, default=dict, server_default="{}")
    created_at:  Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    actor: Mapped["User | None"] = relationship("User", lazy="joined")

    @classmethod
    def record(cls, db: AsyncSession, actor: "User | None", action: str, entity_type: str,
               entity_id: int | None, **details: Any) -> None:
        """Add an entry to the current transaction (it commits with the change it describes)."""
        db.add(cls(actor_id=actor.id if actor else None, action=action,
                   entity_type=entity_type, entity_id=entity_id, details=details))
