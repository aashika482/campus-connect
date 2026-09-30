# One-off data fix: phone became required at sign-up, but older accounts have no
# phone (NULL, or "" from an old sign-up form). Give them an obvious placeholder
# they can replace from their Profile page. Safe to run more than once.
#
#   cd backend
#   python -m app.db.backfill_phone_placeholders

import asyncio
from sqlalchemy import text

from app.db.database import engine

PLACEHOLDER = "0000000000"


async def main():
    async with engine.begin() as conn:
        result = await conn.execute(
            text("UPDATE users SET phone = :p WHERE phone IS NULL OR TRIM(phone) = ''"),
            {"p": PLACEHOLDER},
        )
        print(f"OK: set placeholder phone on {result.rowcount} accounts")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
