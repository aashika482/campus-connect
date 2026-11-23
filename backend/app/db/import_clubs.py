"""
The real club list, and the DSW's yearly audit.

  cd backend
  python -m app.db.import_clubs                                   # the clubs only (names, short names, tags)
  python -m app.db.import_clubs AUDIT.xlsx --year 2024-25         # + that year's evaluations and coordinators
  python -m app.db.import_clubs AUDIT.xlsx --year 2024-25 --replace   # also delete clubs not in the sheet
  python -m app.db.import_clubs --replace                         # (no sheet) delete clubs not in the real list

The audit sheet stays out of git (scores, remarks and faculty emails are the DSW's). Its
"Consolidated Marks" tab is read: clubs without a category are skipped, blank marks count as 0.
For each club:
  - created if new, with the short name and tags below (or a plain default) and a placeholder
    description; clubs that already exist keep whatever their owners have edited
  - the year's evaluation (category, marks, remarks) is stored or replaced, for the DSW only
  - every coordinator email becomes an invite: that faculty member becomes the club's coordinator
    when they sign in with their verified college account
Running it again is safe: nothing is duplicated.
"""
import argparse
import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import delete, func, select, text

from app.db.database import AsyncSessionLocal, engine
from app.models.club import Club, ClubEvaluation, ClubRequest, CoordinatorInvite
from app.core.governance import CLUB_COLORS

# Name as in the audit sheet → (short name, tags). Tags "" = not categorized yet: the owner picks them.
CLUBS: dict[str, tuple[str, str]] = {
    "180 Degrees Consulting MUJ Club": ("180DC", "business,social"),
    "Abhigya Club": ("Abhigya", ""),
    "ACM MUJ STUDENT CHAPTER": ("ACM", "coding,tech"),
    "Goonj- The Radio Society/ Advent": ("Goonj", "film"),
    "Nexus (Satellite Club MUJ)": ("Nexus", "science,tech"),
    "Aperture": ("Aperture", "photography"),
    "ASHRAE Chapter": ("ASHRAE", "tech"),
    "Autonomous Initiative (ROBOTICS CLUB)": ("AI Robotics", "robotics,tech"),
    "Cinefilia - The Dramatics and Filmmaking Society of Manipal University Jaipur": ("Cinefilia", "film,art"),
    "CONVERGENCE": ("Convergence", ""),
    "Coreografia": ("Coreo", "dance"),
    "COSMOS – The Science Club of MUJ": ("COSMOS", "science"),
    "Cypher Club": ("Cypher", ""),
    "D-Club": ("D-Club", ""),
    "De Artistry Club": ("De Artistry", "art"),
    "Developer Student Clubs Manipal University Jaipur": ("DSC", "tech,coding"),
    "ENACTUS Chapter": ("Enactus", "business,social"),
    "Enviroclub": ("Enviro", "environment"),
    "ESTRELLA - The Astronomy Club": ("Estrella", "science"),
    "Finance Club": ("Finance", "business"),
    "Glitch! The eSports Society": ("Glitch", "gaming"),
    "Hercampus": ("Her Campus", "literature"),
    "Heritage Club": ("Heritage", "culture"),
    "Humans of Manipal Jaipur": ("HoMJ", "film,photography"),
    "IE(I) MUJ Civil Engineering Students' Chapter": ("IEI Civil", "tech"),
    "IE(I) MUJ Mechatronics Chapter": ("IEI Mechatronics", "robotics,tech"),
    "IEEE APS Student Chapter": ("IEEE APS", "tech,science"),
    "IEEE MTTS Student Chapter": ("IEEE MTTS", "tech"),
    "IEEE RAS Student Chapter": ("IEEE RAS", "robotics,tech"),
    "IEEE MUJ STUDENT CHAPTER": ("IEEE", "tech"),
    "INSTITUTE OF ENGINEERS (INDIA) MECHANICAL (IEI STUDENT'S CHAPTER)": ("IEI Mechanical", "tech"),
    "International Relations Council": ("IRC", "quizzing,social"),
    "International Society of Automation (ISA)": ("ISA", "tech,robotics"),
    "LearnIT": ("LearnIT", ""),
    "LITMUS": ("Litmus", "literature"),
    "MarkSoc": ("MarkSoc", "business"),
    "Mind Over Matter": ("MoM", "wellness"),
    "MUJ OSA Student Chapter": ("OSA", "science,tech"),
    "Olympism Club": ("Olympism", "sports"),
    "OMPHALOS": ("Omphalos", ""),
    "PANACEA": ("Panacea", ""),
    "PHI Phenomenon": ("PHI", ""),
    "Qureka- The Quzzing club of Manipal University Jaipur": ("Qureka", "quizzing"),
    "Randomize": ("Randomize", ""),
    "Rennaissance": ("Rennaissance", ""),
    "ROTARACT CLUB": ("Rotaract", "social"),
    "RPM-SAE MUJ": ("RPM-SAE", "tech"),
    "SCRIBBLES": ("Scribbles", "literature"),
    "SPICMACAY": ("SPIC MACAY", "music,culture"),
    "SPIE Student Chapter Manipal University Jaipur": ("SPIE", "science,tech"),
    "The Music Club": ("TMC", "music"),
    "Turing Sapiens": ("Turing Sapiens", "coding,tech"),
    "Wings - The - Aeromodelling Club": ("Wings", "robotics,tech"),
    "YES!+ Student Chapter": ("YES!+", "wellness"),
    "ANOVA": ("ANOVA", ""),
    "MUJ ACM SIGAI STUDENT CHAPTER": ("ACM SIGAI", "tech,coding"),
    "MUJ ACM SIGBED STUDENT CHAPTER": ("ACM SIGBED", "tech"),
    "CYBER SPACE": ("CyberSpace", "tech"),
    "IEEE SENSORS COUNCIL CHAPTER MUJ": ("IEEE Sensors", "tech"),
    "TYWI MUJ CHAPTER": ("TYWI", ""),
    "CACTUS CLUB": ("Cactus", ""),
    "I G B C STUDENT CHAPTER": ("IGBC", "environment,tech"),
    "CHESS SOCIETY": ("Chess", "sports"),
    "AIML COMMUNITY": ("AIML", "tech,coding"),
    "HR INSIGHTS": ("HR Insights", "business"),
    "INDGenus MUJ Chapter": ("INDGenus", ""),
    "Pitcher's Craft": ("Pitcher's Craft", "business"),
    "Standards Club": ("Standards", "tech"),
    "EMANATE COMMUNITY": ("Emanate", ""),
    "GRAM ASHA CLUB MUJ": ("Gram Asha", "social"),
    "HOLISTIC HEALTH YOGA CLUB MUJ": ("Yoga Club", "wellness"),
    "MANAGIA CLUB MUJ": ("Managia", "business"),
    "DevForge Club MUJ": ("DevForge", "coding,tech"),
    "KISHORI CLUB MUJ": ("Kishori", "social"),
    "IEEE GRSS STUDENTS CHAPTER": ("IEEE GRSS", "tech,science"),
    "IEEE CASS": ("IEEE CASS", "tech"),
    "MUJ ORIGINS CLUB MUJ": ("Origins", ""),
    "THE BIODIVERSITY CONSERVATION CLUB": ("Biodiversity", "environment"),
    "GREEN HORIZON CLUB MUJ": ("Green Horizon", "environment"),
    "INDIAN PLUMBING ASSOCIATION (IPA)": ("IPA", "tech"),
    "MANIPAL RUNNERS CLUB": ("Runners", "sports,wellness"),
    "10X CLUB MUJ CHAPTER": ("10X", "coding,tech"),
    "TECH FOR INDIA": ("Tech for India", "tech,social"),
    "CENTAURUS ARENA CLUB MUJ": ("Centaurus", ""),
    "EARTH Club MUJ": ("EARTH", "environment"),
    "Quality Club Manipal University Jaipur": ("Quality Club", "business"),
    "Garuda Club": ("Garuda", ""),
    "Wiki Tech Club": ("Wiki Tech", "tech"),
    "Shabad": ("Shabad", "music,culture"),
    "Martial Arts and Self-Defence Club (MASDC)": ("MASDC", "sports,wellness"),
    "Unstop Igniters Club MUJ": ("Unstop Igniters", "business"),
    "Epicurean Club": ("Epicurean", "culture"),
    "Toastmasters Club MUJ": ("Toastmasters", "quizzing,literature"),
    "MUJ Film Study Club": ("Film Study", "film"),
    "EIS Entrepreneur & Innovation Society": ("EIS", "business"),
    "Codience": ("Codience", "coding"),
    "Consumer Protection Cell": ("CPC", "social"),
    "APEX (Advanced Planning for Excellence in Sustainability": ("APEX", "environment"),
    "BIOCHEMIE CLUB MUJ": ("Biochemie", "science"),
    "AGENTABLAZER CLUB MUJ": ("AgentaBlazer", "tech"),
    "SoulRaga- the bhajan club": ("SoulRaga", "music,culture"),
    "Biotech Club": ("Biotech", "science"),
}

# Coordinator emails the DSW chose not to invite (club name → emails)
SKIP_INVITES = {
    # 2024-25 sheet names "Dr. Arpit Sharma" but gives this email: the DSW assigns Glitch's coordinator by hand
    "Glitch! The eSports Society": {"arvind.dhaka@jaipur.manipal.edu"},
}

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def clean(v) -> str:
    """Cell text with non-breaking spaces, line breaks and runs of spaces tidied."""
    return re.sub(r"\s+", " ", str(v).replace("\xa0", " ")).strip() if v is not None else ""


def mark(v) -> float:
    try:
        return float(clean(v) or 0)
    except ValueError:
        return 0.0


def read_sheet(path: str) -> list[dict]:
    from openpyxl import load_workbook   # only needed with a sheet (requirements-dev.txt)
    ws = load_workbook(path, read_only=True, data_only=True)["Consolidated Marks"]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        name, category = clean(r[1]), clean(r[2])
        if not name or not category:
            continue
        rows.append(dict(
            name=name, category=category,
            emails=[e.lower() for e in EMAIL.findall(clean(r[4]))],
            marks=[mark(x) for x in r[5:11]], remarks=clean(r[11]) or None,
        ))
    return rows


async def run(path: str | None, year: str | None, replace: bool, assume_yes: bool = False) -> None:
    rows = read_sheet(path) if path else [dict(name=n) for n in CLUBS]
    async with AsyncSessionLocal() as db:
        # A handful of big queries, not a few per club: a cloud database can be ~0.5 s away per round trip
        existing = {c.name.lower(): c for c in (await db.execute(select(Club))).scalars().all()}
        new = []
        for row in rows:
            if row["name"].lower() not in existing:
                abbr, tags = CLUBS.get(row["name"], (row["name"].split()[0][:12], ""))
                club = Club(name=row["name"], abbr=abbr, tags=tags,
                            description=f"{row['name']} hasn't added a description yet.",
                            color=CLUB_COLORS[sum(map(ord, row["name"])) % len(CLUB_COLORS)])
                existing[club.name.lower()] = club
                new.append(club)
        db.add_all(new)
        await db.flush()   # one INSERT for every new club, giving them ids
        created = len(new)
        club_of = {row["name"]: existing[row["name"].lower()] for row in rows}
        keep: set[int] = {c.id for c in club_of.values()}

        evaluated = invited = 0
        if year:
            # This year's evaluations are replaced as a whole
            await db.execute(delete(ClubEvaluation).where(ClubEvaluation.year == year, ClubEvaluation.club_id.in_(keep)))
            invites = set((await db.execute(
                select(CoordinatorInvite.club_id, CoordinatorInvite.email).where(CoordinatorInvite.club_id.in_(keep))
            )).all())
            for row in rows:
                club = club_of[row["name"]]
                quality, sponsorship, engagement, dsw, faculty, total = row["marks"]
                db.add(ClubEvaluation(club_id=club.id, year=year, category=row["category"], quality_of_events=quality,
                                      sponsorship=sponsorship, student_engagement=engagement, dsw_component=dsw,
                                      faculty_component=faculty, total=total, remarks=row["remarks"]))
                evaluated += 1
                for email in [e for e in row["emails"] if e not in SKIP_INVITES.get(row["name"], set())]:
                    if (club.id, email) not in invites:
                        invites.add((club.id, email))
                        db.add(CoordinatorInvite(club_id=club.id, email=email))
                        invited += 1

        removed = 0
        if replace:
            # Clubs students created through approved requests aren't in any audit sheet yet: never delete them
            keep |= set((await db.execute(select(ClubRequest.club_id).where(ClubRequest.club_id.is_not(None)))).scalars().all())
            doomed = (await db.execute(select(Club.name).where(Club.id.not_in(keep)).order_by(Club.name))).scalars().all()
            if doomed:
                print(f"--replace would delete these {len(doomed)} clubs, with all their events, members and history:")
                print("".join(f"  - {name}\n" for name in doomed), end="")
                if not assume_yes and input("Type DELETE to go ahead: ").strip() != "DELETE":
                    await db.rollback()
                    await engine.dispose()
                    sys.exit("Nothing changed.")
                removed = (await db.execute(delete(Club).where(Club.id.not_in(keep)))).rowcount
        # Clubs may have been inserted with ids before: keep the id sequence ahead of them
        await db.execute(text("SELECT setval(pg_get_serial_sequence('clubs', 'id'), GREATEST((SELECT MAX(id) FROM clubs), 1))"))
        await db.commit()
        total = (await db.execute(select(func.count()).select_from(Club))).scalar()
    await engine.dispose()
    print(f"OK: {created} clubs created, {removed} removed, {total} in total."
          + (f" {year}: {evaluated} evaluations, {invited} new coordinator invites." if year else ""))
    if not path:
        print("Clubs only. With the DSW's audit sheet: python -m app.db.import_clubs SHEET.xlsx --year 2024-25")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import the real club list (and the DSW's audit sheet).")
    parser.add_argument("sheet", nargs="?", help="the DSW's audit .xlsx (its 'Consolidated Marks' tab)")
    parser.add_argument("--year", help="academic year of the audit, e.g. 2024-25 (needed with a sheet)")
    parser.add_argument("--replace", action="store_true", help="delete clubs that aren't in the sheet, or without one, "
                        "not in the real list (and all their data). Asks first, and never deletes clubs "
                        "created through approved new-club requests")
    parser.add_argument("--yes", action="store_true", help="don't ask before deleting (for scripts)")
    args = parser.parse_args()
    if args.sheet and not re.fullmatch(r"\d{4}-\d{2}", args.year or ""):
        parser.error("--year YYYY-YY is required with a sheet, e.g. --year 2024-25")
    asyncio.run(run(args.sheet, args.year, args.replace, args.yes))
