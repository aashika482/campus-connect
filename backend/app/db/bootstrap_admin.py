# Create the first platform admin (tech team), or promote / demote an existing account.
# Run on the server: this is the only way to make a platform admin. Platform admins then
# appoint DSW accounts from the web app, and the DSW governs everything else.
#
#   cd backend
#   python -m app.db.bootstrap_admin tech@jaipur.manipal.edu            # promote, or create (asks name + password)
#   python -m app.db.bootstrap_admin tech@jaipur.manipal.edu --revoke   # back to its email domain's type

import asyncio
import getpass
import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.database import AsyncSessionLocal, engine
from app.models.audit import AuditLog
from app.models.membership import TEAM_ROLES, ClubRoleStatus
from app.models.user import User, AccountType


async def main(email: str, revoke: bool):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if revoke:
            if not user or user.account_type != AccountType.platform_admin:
                sys.exit(f"{email} isn't a platform admin")
            user.account_type = AccountType(settings.account_kind_for(email) or "student")
            action = "user.remove_platform_admin"
        else:
            if user is None:
                name = input("Name: ").strip()
                password = getpass.getpass("Password (min 6 chars): ")
                if not name or len(password) < 6:
                    sys.exit("A name and a password of at least 6 characters are required")
                user = User(name=name, email=email, password=hash_password(password))
                db.add(user)
            # A platform admin runs the system, not a club
            for r in user.roles(*TEAM_ROLES):
                r.status = ClubRoleStatus.ended
            user.account_type = AccountType.platform_admin
            action = "user.grant_platform_admin"
        await db.flush()
        AuditLog.record(db, None, action, "user", user.id, user=email, via="command line")
        await db.commit()
        print(f"OK: {user.name} <{email}> is now '{user.account_type.value}'")
    await engine.dispose()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--revoke"]
    if len(args) != 1:
        sys.exit("Usage: python -m app.db.bootstrap_admin <email> [--revoke]")
    asyncio.run(main(args[0].strip().lower(), "--revoke" in sys.argv))
