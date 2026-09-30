# One-off data fix: clubs.member_count started from made-up seed numbers (e.g. 410)
# and was then +1/-1'd on join/leave. This resets every club to its real number of
# memberships. join/leave now recount, so it stays correct afterwards.
# Safe to run more than once.
#
#   cd backend
#   python -m app.db.sync_member_counts

import asyncio
from sqlalchemy import text

from app.db.database import engine


async def main():
    async with engine.begin() as conn:
        rows = (await conn.execute(text("""
            UPDATE clubs c
            SET member_count = (SELECT COUNT(*) FROM memberships m WHERE m.club_id = c.id)
            RETURNING c.name, c.member_count
        """))).all()
        for name, count in sorted(rows):
            print(f"  {count:>3}  {name}")
        print(f"OK: synced {len(rows)} clubs")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
