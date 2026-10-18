# Demo data: rebuild everything except the clubs, with dates relative to today.
#
# Keeps every club row (the club data is real). Deletes all users, events, roles,
# registrations, discussions, notifications and the audit log, then generates:
#   - a platform admin and a DSW account
#   - two faculty coordinators per club
#   - students: most clubs get an owner and editors, a few requests wait for the DSW
#   - memberships, events (some past, some live, some upcoming), registrations,
#     saved events and discussions
# Event dates are re-anchored to today on every run, so demos never show stale dates.
# Every run produces the same people (fixed random seed).
#
# Refuses to run unless DEMO_MODE=true, so it can never wipe a production database.
#   cd backend
#   DEMO_MODE=true DEMO_PASSWORD=<pick one> python -m app.db.demo

import asyncio
import random
import sys
from datetime import date

from sqlalchemy import select, text

from app.core.config import settings
from app.core.governance import sync_member_count
from app.core.security import hash_password
from app.db.database import AsyncSessionLocal, engine
from app.models.audit import AuditLog
from app.models.club import Club
from app.models.discussion import Discussion
from app.models.event import Event
from app.models.membership import ClubRole, ClubRoleKind, ClubRoleStatus, Registration, SavedEvent
from app.models.user import User, AccountType

# Everything except clubs
WIPE = ("TRUNCATE notifications, discussions, saved_events, registrations, club_roles, "
        "audit_log, events, users RESTART IDENTITY CASCADE")

FACULTY = ["Dr. Meenakshi Rao", "Dr. Arvind Sharma", "Dr. Kavita Joshi", "Prof. Rahul Verma",
           "Dr. Sunita Agarwal", "Prof. Imran Khan", "Dr. Neha Kapoor", "Prof. Vikram Singh"]
FIRST = ["Aarav", "Diya", "Kabir", "Ananya", "Vihaan", "Isha", "Arjun", "Meera", "Rohan", "Saanvi",
         "Aditya", "Kavya", "Krish", "Riya", "Ishaan", "Tara", "Dhruv", "Nisha", "Yash", "Pooja",
         "Aryan", "Sneha", "Kunal", "Aditi", "Rehan", "Simran", "Varun", "Jhanvi", "Harsh", "Mahi"]
LAST = ["Sharma", "Verma", "Gupta", "Mehta", "Iyer", "Nair", "Reddy", "Singh", "Jain", "Patel",
        "Bose", "Kulkarni", "Chopra", "Malhotra", "Saxena"]
COURSES = ["B.Tech CSE", "B.Tech IT", "B.Tech ECE", "B.Tech ME", "BBA", "B.Des", "BA Journalism", "B.Arch"]
TAGS = ["tech", "hackathon", "photography", "dance", "music", "coding", "art", "robotics", "film",
        "literature", "sports", "social"]
COMMENTS = ["Is this open to first-years?", "Can we register as a team of 3?", "Will there be certificates?",
            "What should we bring?", "Is there a dress code?", "Can students from other branches join?",
            "Will it be recorded?", "Is food arranged?"]
REPLIES = ["Yes, everyone's welcome!", "Details are on the poster: check the venue section.",
           "Certificates for all participants.", "We'll post an update on the club page soon."]

# The demo event dates below were written around this day; it maps to today on every run
ANCHOR = date(2025, 10, 15)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def shifted(iso: str | None) -> date | None:
    return date.today() + (date.fromisoformat(iso) - ANCHOR) if iso else None


def date_display(start: date, end: date) -> str:
    """Oct 29 / Oct 29–31 / Oct 29 – Nov 2: the same format the event form produces."""
    first = f"{MONTHS[start.month - 1]} {start.day}"
    if start == end:
        return first
    if start.month == end.month:
        return f"{first}–{end.day}"
    return f"{first} – {MONTHS[end.month - 1]} {end.day}"


DEMO_EVENTS = [
  {"id":1,  "title":"HackX 3.0",            "club_id":4,  "club_name":"ACM",       "date_display":"Oct 29–31","start_date":"2025-10-29","end_date":"2025-10-31","reg_deadline":"2025-10-26","tags":"hackathon,tech,coding","team_size":"2–4",      "is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1607799279861-4dd421887fb3?w=400&h=600&fit=crop","description":"MUJ's flagship 36-hour international hackathon. 50+ universities, 2,000+ participants. Build something that matters — six weeks of mentorship, access to cloud infrastructure, and a stage that gets watched."},
  {"id":2,  "title":"Indian Ocean Live",     "club_id":2,  "club_name":"TMC",       "date_display":"Nov 1",   "start_date":"2025-11-01","end_date":"2025-11-01","reg_deadline":"2025-10-28","tags":"music",               "team_size":None,       "is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=600&fit=crop","description":"The legendary Indian Ocean plays live at Dr. Ramdas Pai Amphitheatre."},
  {"id":3,  "title":"Breached 5.0",         "club_id":11, "club_name":"CyberSpace","date_display":"Nov 7–8", "start_date":"2025-11-07","end_date":"2025-11-08","reg_deadline":"2025-11-04","tags":"tech,coding",         "team_size":"1–3",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400&h=600&fit=crop","description":"Online cryptic hunt — decode, navigate, unravel. 25+ levels of cryptography, OSINT, and logic."},
  {"id":4,  "title":"Rewind & Recode",      "club_id":1,  "club_name":"IEEE CS",   "date_display":"Oct 10–11","start_date":"2025-10-10","end_date":"2025-10-11","reg_deadline":"2025-10-07","tags":"tech,hackathon",      "team_size":"2–4",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1517180102446-f3ece451e9d8?w=400&h=600&fit=crop","description":"D3 Tech Fest flagship. Retro-themed challenges, modern problem-solving."},
  {"id":5,  "title":"Pirates of Code 2.0",  "club_id":4,  "club_name":"ACM",       "date_display":"Oct 10",  "start_date":"2025-10-10","end_date":"2025-10-10","reg_deadline":"2025-10-08","tags":"coding",              "team_size":"Solo",     "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=400&h=600&fit=crop","description":"Treasure hunt meets competitive programming."},
  {"id":6,  "title":"Hymns of Joy",         "club_id":12, "club_name":"Manan",     "date_display":"Oct 3–6", "start_date":"2025-10-03","end_date":"2025-10-06","reg_deadline":"2025-10-01","tags":"photography",         "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=400&h=600&fit=crop","description":"Photography competition by DSW. Submit your best frame across any genre."},
  {"id":7,  "title":"TechnoUtsav '26",      "club_id":1,  "club_name":"IEEE CS",   "date_display":"Nov 15–16","start_date":"2025-11-15","end_date":"2025-11-16","reg_deadline":"2025-11-10","tags":"tech,robotics",       "team_size":"2–5",      "is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=600&fit=crop","description":"Annual tech mega-fest. Robo-wars, drone racing, AI art battles, CTF, and 15+ events across two full days."},
  {"id":8,  "title":"Groove Nation",        "club_id":3,  "club_name":"Coreo",     "date_display":"Nov 22",  "start_date":"2025-11-22","end_date":"2025-11-22","reg_deadline":"2025-11-18","tags":"dance",               "team_size":"6–12",     "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1547153760-18fc86324498?w=400&h=600&fit=crop","description":"Inter-college group dance battle. Western, classical, freestyle."},
  {"id":9,  "title":"Open Mic Night",       "club_id":2,  "club_name":"TMC",       "date_display":"Oct 17",  "start_date":"2025-10-17","end_date":"2025-10-17","reg_deadline":"2025-10-15","tags":"music,art",           "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=400&h=600&fit=crop","description":"Monthly open mic — originals, covers, poetry, spoken word."},
  {"id":10, "title":"Flash Mob @ Atrium",   "club_id":3,  "club_name":"Coreo",     "date_display":"Oct 24",  "start_date":"2025-10-24","end_date":"2025-10-24","reg_deadline":None,         "tags":"dance",               "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1574169208507-84376144848b?w=400&h=600&fit=crop","description":"Surprise flash mob at the central atrium."},
  {"id":11, "title":"RoboWars 2026",        "club_id":7,  "club_name":"RAS",       "date_display":"Nov 8–9", "start_date":"2025-11-08","end_date":"2025-11-09","reg_deadline":"2025-11-03","tags":"robotics,tech",       "team_size":"2–4",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=600&fit=crop","description":"Bot battles, drone races, and sumo-bots."},
  {"id":12, "title":"Cinéclub Screening",   "club_id":5,  "club_name":"Cine",      "date_display":"Oct 14",  "start_date":"2025-10-14","end_date":"2025-10-14","reg_deadline":None,         "tags":"film,art",            "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400&h=600&fit=crop","description":"Monthly cult classic screening followed by an open discussion."},
  {"id":13, "title":"DSA Bootcamp",         "club_id":8,  "club_name":"CN 10x",    "date_display":"Oct 20–22","start_date":"2025-10-20","end_date":"2025-10-22","reg_deadline":"2025-10-17","tags":"coding,tech",         "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=600&fit=crop","description":"3-day intensive data structures and algorithms workshop."},
  {"id":14, "title":"Football League S2",   "club_id":13, "club_name":"MSC",       "date_display":"Oct 6–12","start_date":"2025-10-06","end_date":"2025-10-12","reg_deadline":"2025-10-03","tags":"sports",              "team_size":"11",       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400&h=600&fit=crop","description":"Campus football league, season two."},
  {"id":15, "title":"MUN 2026",             "club_id":14, "club_name":"Samvaad",   "date_display":"Oct 25–26","start_date":"2025-10-25","end_date":"2025-10-26","reg_deadline":"2025-10-20","tags":"literature,social",   "team_size":"Solo/Pair","is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1606761568499-6d2451b23c66?w=400&h=600&fit=crop","description":"Two-day Model United Nations with 8 committees."},
  {"id":16, "title":"UI/UX Design Sprint",  "club_id":15, "club_name":"DesignX",   "date_display":"Oct 16–17","start_date":"2025-10-16","end_date":"2025-10-17","reg_deadline":"2025-10-13","tags":"art,tech",            "team_size":"1–2",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1561070791-2526d30994b5?w=400&h=600&fit=crop","description":"48-hour design challenge. Prototype a real product."},
  {"id":17, "title":"Campus Clean Drive",   "club_id":16, "club_name":"GreenMUJ",  "date_display":"Oct 2",   "start_date":"2025-10-02","end_date":"2025-10-02","reg_deadline":None,         "tags":"social",              "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400&h=600&fit=crop","description":"Join 200+ volunteers to clean up campus, plant saplings."},
  {"id":18, "title":"Literary Fest 2026",   "club_id":10, "club_name":"Litmus",    "date_display":"Nov 5–6", "start_date":"2025-11-05","end_date":"2025-11-06","reg_deadline":"2025-11-01","tags":"literature",          "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=600&fit=crop","description":"Poetry slam, creative writing contest, storytelling showcase."},
  {"id":19, "title":"Salsa & Bachata Night","club_id":3,  "club_name":"Coreo",     "date_display":"Nov 13",  "start_date":"2025-11-13","end_date":"2025-11-13","reg_deadline":"2025-11-10","tags":"dance",               "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1519742866993-66d3cfef4bbd?w=400&h=600&fit=crop","description":"A proper evening of salsa, bachata, and freestyle."},
  {"id":20, "title":"Startup Pitch Day",    "club_id":9,  "club_name":"Enactus",   "date_display":"Oct 28",  "start_date":"2025-10-28","end_date":"2025-10-28","reg_deadline":"2025-10-24","tags":"social,tech",         "team_size":"2–5",      "is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=400&h=600&fit=crop","description":"Pitch your social venture to investors and industry leaders."},
  {"id":21, "title":"Drone Racing Cup",     "club_id":7,  "club_name":"RAS",       "date_display":"Oct 31",  "start_date":"2025-10-31","end_date":"2025-10-31","reg_deadline":"2025-10-27","tags":"robotics",            "team_size":"Solo",     "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=400&h=600&fit=crop","description":"FPV drone racing through a custom obstacle course."},
  {"id":22, "title":"Jazz & Blues Evening", "club_id":2,  "club_name":"TMC",       "date_display":"Nov 20",  "start_date":"2025-11-20","end_date":"2025-11-20","reg_deadline":None,         "tags":"music",               "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?w=400&h=600&fit=crop","description":"Intimate evening of jazz and blues at the open-air courtyard."},
  {"id":23, "title":"Photo Walk: Old City", "club_id":12, "club_name":"Manan",     "date_display":"Oct 19",  "start_date":"2025-10-19","end_date":"2025-10-19","reg_deadline":"2025-10-17","tags":"photography",         "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400&h=600&fit=crop","description":"Guided photo walk through Jaipur's walled city."},
  {"id":24, "title":"Badminton Open",       "club_id":13, "club_name":"MSC",       "date_display":"Nov 10–11","start_date":"2025-11-10","end_date":"2025-11-11","reg_deadline":"2025-11-07","tags":"sports",              "team_size":"Solo/Pair","is_hot":False, "poster_url":"https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=400&h=600&fit=crop","description":"Inter-department badminton open. Singles and doubles."},
  {"id":25, "title":"Short Film Fest",      "club_id":5,  "club_name":"Cine",      "date_display":"Nov 28–29","start_date":"2025-11-28","end_date":"2025-11-29","reg_deadline":"2025-11-20","tags":"film",               "team_size":"2–8",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=400&h=600&fit=crop","description":"Submit your short film (max 15 minutes). Jury screening and awards ceremony."},
]


async def main():
    if not settings.DEMO_MODE:
        sys.exit("Refusing to run: set DEMO_MODE=true (this wipes every user and event).")
    if len(settings.DEMO_PASSWORD) < 6:
        sys.exit("Set DEMO_PASSWORD (at least 6 characters): every demo account signs in with it.")
    rnd = random.Random(2026)
    pw = hash_password(settings.DEMO_PASSWORD)   # hashed once: bcrypt per account would take ~15s
    student_domain = settings.email_domains["student"][0]
    staff_domain = settings.email_domains["faculty"][0]

    async with AsyncSessionLocal() as db:
        await db.execute(text(WIPE))
        clubs = list((await db.execute(select(Club).order_by(Club.id))).scalars().all())
        if not clubs:
            sys.exit("No clubs in the database. Run python -m app.db.seed first.")

        def account(name: str, email: str, kind: AccountType, **extra) -> User:
            u = User(name=name, email=email, password=pw, account_type=kind,
                     phone=f"9{rnd.randrange(10**8, 10**9)}", **extra)
            db.add(u)
            return u

        account("Tech Team", f"tech@{staff_domain}", AccountType.platform_admin)
        dsw = account("DSW Office", f"dsw@{staff_domain}", AccountType.dsw)
        faculty = [account(n, f"{n.split()[-1].lower()}.{n.split()[1].lower()}@{staff_domain}", AccountType.faculty)
                   for n in FACULTY]
        names = rnd.sample([f"{f} {l}" for f in FIRST for l in LAST], 60)
        students = [
            account(n, f"{n.lower().replace(' ', '.')}@{student_domain}", AccountType.student,
                    reg_no=f"22930{1000 + i}", course=rnd.choice(COURSES), interests=",".join(rnd.sample(TAGS, 3)))
            for i, n in enumerate(names)
        ]
        await db.flush()

        joined: dict[int, set[int]] = {}   # user id -> clubs they're a member of

        def role(u: User, club: Club, kind: ClubRoleKind, status=ClubRoleStatus.active, **extra):
            db.add(ClubRole(user_id=u.id, club_id=club.id, role=kind, status=status, **extra))
            if kind == ClubRoleKind.member:
                joined.setdefault(u.id, set()).add(club.id)

        # Teams: two faculty coordinators per club; an owner for every club but the last two
        # (their owner requests wait for the DSW); one or two editors; two editor proposals pending
        pool = iter(students)
        for i, club in enumerate(clubs):
            for f in {faculty[i % len(faculty)].id: faculty[i % len(faculty)],
                      faculty[(i + 3) % len(faculty)].id: faculty[(i + 3) % len(faculty)]}.values():
                role(f, club, ClubRoleKind.faculty_coordinator, proposed_by=dsw.id, reviewed_by=dsw.id)
            has_owner = i < len(clubs) - 2
            owner = next(pool)
            role(owner, club, ClubRoleKind.owner, ClubRoleStatus.active if has_owner else ClubRoleStatus.pending,
                 title="President", proposed_by=owner.id, reviewed_by=dsw.id if has_owner else None)
            role(owner, club, ClubRoleKind.member)
            if has_owner:
                for _ in range(1 + i % 2):
                    editor = next(pool)
                    role(editor, club, ClubRoleKind.editor, title="Coordinator", proposed_by=owner.id, reviewed_by=dsw.id)
                    role(editor, club, ClubRoleKind.member)
                if i in (0, 3):
                    role(next(pool), club, ClubRoleKind.editor, ClubRoleStatus.pending, title="Tech Lead", proposed_by=owner.id)

        # Every student is in one to three clubs
        for s in students:
            for club in rnd.sample(clubs, rnd.randint(1, 3)):
                if club.id not in joined.get(s.id, set()):
                    role(s, club, ClubRoleKind.member)

        # Events, re-anchored to today, for the clubs that exist
        by_id = {c.id: c for c in clubs}
        events = []
        for e in DEMO_EVENTS:
            club = by_id.get(e["club_id"])
            if club is None:
                continue
            start, end = shifted(e["start_date"]), shifted(e["end_date"])
            ev = Event(
                title=e["title"], description=e["description"], club_id=club.id, club_name=club.name,
                start_date=start, end_date=end, reg_deadline=shifted(e["reg_deadline"]),
                date_display=date_display(start, end), tags=e["tags"], team_size=e["team_size"],
                poster_url=e["poster_url"], is_hot=e["is_hot"],
            )
            db.add(ev)
            events.append(ev)
        await db.flush()

        # Activity: registrations, saves, and questions answered by a faculty coordinator
        coordinators = {i: faculty[i % len(faculty)] for i in range(len(clubs))}
        club_index = {c.id: i for i, c in enumerate(clubs)}
        for ev in events:
            for s in rnd.sample(students, rnd.randint(4, 18)):
                db.add(Registration(user_id=s.id, event_id=ev.id))
            for s in rnd.sample(students, rnd.randint(0, 6)):
                db.add(SavedEvent(user_id=s.id, event_id=ev.id))
            answerer = coordinators[club_index[ev.club_id]]
            for s in rnd.sample(students, rnd.randint(0, 3)):
                question = Discussion(event_id=ev.id, user_id=s.id, user_name=s.name, user_role="student",
                                      content=rnd.choice(COMMENTS))
                db.add(question)
                await db.flush()
                if rnd.random() < 0.6:
                    db.add(Discussion(event_id=ev.id, user_id=answerer.id, user_name=answerer.name,
                                      user_role="faculty", content=rnd.choice(REPLIES),
                                      parent_id=question.id, is_official=True))

        await db.flush()
        for club in clubs:
            await sync_member_count(db, club)
        AuditLog.record(db, None, "demo.reset", "database", None, clubs=len(clubs), events=len(events),
                        students=len(students), faculty=len(faculty))
        await db.commit()

    await engine.dispose()
    print(f"OK: demo data for {len(clubs)} clubs: {len(events)} events, {len(students)} students, {len(faculty)} faculty.")
    print(f"Every account's password is the DEMO_PASSWORD you set. Try:")
    print(f"  platform admin  tech@{staff_domain}")
    print(f"  DSW             dsw@{staff_domain}")
    print(f"  faculty         {faculty[0].email}")
    print(f"  club owner      {students[0].email}  ({clubs[0].name})")
    print(f"  student         {students[-1].email}")


if __name__ == "__main__":
    asyncio.run(main())
