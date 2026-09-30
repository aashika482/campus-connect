# One-off data fix: move events that have already ended forward by SHIFT_DAYS so
# they show as upcoming again (Home "Coming Up", open registration, calendar).
# Only events whose end_date is before today are moved, so re-running it is safe:
# after the first run nothing is in the past, and newer future events are never touched.
#
#   cd backend
#   python -m app.db.shift_event_dates

import asyncio
from datetime import date, timedelta
from sqlalchemy import text

from app.db.database import engine

SHIFT_DAYS = 63  # 9 weeks, so every event keeps its weekday

# Titles that name a year, updated to match the new dates
TITLE_RENAMES = {
    "MUN 2025": "MUN 2026",
    "Literary Fest 2025": "Literary Fest 2026",
    "RoboWars 2025": "RoboWars 2026",
    "TechnoUtsav '25": "TechnoUtsav '26",
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def date_display(start: date, end: date) -> str:
    """Same format as autoDateDisplay() in the frontend's event form."""
    if start == end:
        return f"{MONTHS[start.month - 1]} {start.day}"
    if (start.year, start.month) == (end.year, end.month):
        return f"{MONTHS[start.month - 1]} {start.day}-{end.day}"
    return f"{MONTHS[start.month - 1]} {start.day} - {MONTHS[end.month - 1]} {end.day}"


async def main():
    shift = timedelta(days=SHIFT_DAYS)
    async with engine.begin() as conn:  # one transaction: all rows change or none do
        # Use this machine's date, not the DB's CURRENT_DATE: Neon runs in UTC,
        # which is still "yesterday" for part of the day in India
        rows = (await conn.execute(text(
            "SELECT id, title, start_date, end_date, reg_deadline FROM events "
            "WHERE end_date < :today ORDER BY start_date"
        ), {"today": date.today()})).all()

        for ev_id, title, start, end, deadline in rows:
            new_start, new_end = start + shift, end + shift
            new_deadline = deadline + shift if deadline else None
            new_title = TITLE_RENAMES.get(title, title)
            await conn.execute(text(
                "UPDATE events SET start_date = :s, end_date = :e, reg_deadline = :d, "
                "date_display = :dd, title = :t WHERE id = :id"
            ), {"s": new_start, "e": new_end, "d": new_deadline,
                "dd": date_display(new_start, new_end), "t": new_title, "id": ev_id})
            print(f"#{ev_id:<3} {start} -> {new_start}  {date_display(new_start, new_end):<16} {new_title}")

        print(f"OK: moved {len(rows)} events forward {SHIFT_DAYS} days")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
