# One-off data fix: some events stored a short club name ("TMC", "ACM") in
# events.club_name instead of the club's real name ("The Music Club"). Admin
# ownership checks compare users.club_name to events.club_name as strings, so
# those clubs' admins couldn't see/moderate their own events.
# Safe to run more than once.
#
#   cd backend
#   python -m app.db.fix_event_club_names

import asyncio
from sqlalchemy import text

from app.db.database import engine

STATEMENTS = [
    # 1. Copy the real name from the linked club (club_id is already correct)
    """
    UPDATE events e SET club_name = c.name
    FROM clubs c
    WHERE e.club_id = c.id AND e.club_name <> c.name
    """,
    # 2. Existing comments by an admin of the event's club now get the Admin badge
    """
    UPDATE discussions d SET is_official = TRUE
    FROM events e, users u
    WHERE d.event_id = e.id
      AND d.user_id = u.id
      AND u.role = 'member'
      AND u.club_name = e.club_name
      AND d.is_official = FALSE
    """,
]


async def main():
    async with engine.begin() as conn:  # one transaction: both succeed or neither does
        for sql in STATEMENTS:
            result = await conn.execute(text(sql))
            print(f"OK ({result.rowcount} rows): {' '.join(sql.split())[:70]}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
