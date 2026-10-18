"""
The real club list, for a fresh database (after the tables exist):
  cd backend
  alembic upgrade head
  python -m app.db.seed
Demo users, events and activity come from app.db.demo, not from here.
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.database import AsyncSessionLocal
from app.models.club import Club


CLUBS_DATA = [
  {"id":1,  "name":"IEEE Computer Society",  "abbr":"IEEE CS",  "tags":"tech,coding",       "color":"#3B82F6","is_open":True,  "description":"The campus hub for engineers, developers, and future tech leaders. From embedded systems to machine learning — IEEE CS bridges theory with real-world application through workshops, coding contests, and industry speaker sessions."},
  {"id":2,  "name":"The Music Club",          "abbr":"TMC",      "tags":"music",             "color":"#EF4444","is_open":True,  "description":"A home for every kind of musician. TMC performs at every major fest, hosts open mics, jam sessions, and studio recordings. Instrumentalists, vocalists, composers — all welcome."},
  {"id":3,  "name":"Coreografia",             "abbr":"Coreo",    "tags":"dance",             "color":"#F59E0B","is_open":True,  "description":"MUJ's official dance collective. Classical, contemporary, hip-hop, and everything in between. We take the stage at fests, flash mobs, and competition circuits across the country."},
  {"id":4,  "name":"ACM Student Chapter",     "abbr":"ACM",      "tags":"tech,coding",       "color":"#10B981","is_open":True,  "description":"Where coders compete, collaborate, and grow. ACM drives competitive programming culture at MUJ through hackathons, DSA bootcamps, and inter-college challenges."},
  {"id":5,  "name":"Cinefilia",               "abbr":"Cine",     "tags":"film,art",          "color":"#8B5CF6","is_open":False, "description":"A space for film lovers and storytellers. Cinefilia runs monthly screenings of cult cinema, short film workshops, and screenplay labs — nurturing the next generation of visual artists."},
  {"id":6,  "name":"Rotaract Club",           "abbr":"RAC",      "tags":"social",            "color":"#EC4899","is_open":True,  "description":"Leadership through service. Rotaract drives community impact initiatives, skill-building programs, and social campaigns that extend well beyond the campus gates."},
  {"id":7,  "name":"Robotics & Automation",   "abbr":"RAS",      "tags":"robotics,tech",     "color":"#06B6D4","is_open":True,  "description":"Builders, tinkerers, and automation enthusiasts. RAS runs drone racing, robo-war leagues, and automation workshops — pushing hardware boundaries every semester."},
  {"id":8,  "name":"CodingNinjas 10x",        "abbr":"CN 10x",   "tags":"coding,tech",       "color":"#F97316","is_open":False, "description":"Placement-focused, peer-driven. Code reviews, mock interviews, DSA drills — everything you need to land your dream role, built by students who've been there."},
  {"id":9,  "name":"Enactus MUJ",             "abbr":"Enactus",  "tags":"social,tech",       "color":"#EAB308","is_open":True,  "description":"Entrepreneurial action for real-world impact. Enactus MUJ builds sustainable ventures addressing community challenges — turning ideas into social enterprises."},
  {"id":10, "name":"Litmus",                  "abbr":"Litmus",   "tags":"literature,art",    "color":"#A855F7","is_open":True,  "description":"The literary pulse of campus. Poetry slams, debate tournaments, creative writing workshops, and the annual lit mag that doesn't pull any punches."},
  {"id":11, "name":"CyberSpace",              "abbr":"Cyber",    "tags":"tech,coding",       "color":"#14B8A6","is_open":True,  "description":"Ethical hackers, CTF competitors, and digital defenders. CyberSpace runs bug bounty hunts, cybersecurity workshops, and the beloved Breached CTF series."},
  {"id":12, "name":"Manan Photography",       "abbr":"Manan",    "tags":"photography,art",   "color":"#E879F9","is_open":True,  "description":"Visual storytelling through every lens. Photo walks, editing masterclasses, studio sessions, and annual exhibitions — Manan captures the soul of campus life."},
  {"id":13, "name":"MUJ Sports Council",      "abbr":"MSC",      "tags":"sports",            "color":"#22C55E","is_open":False, "description":"The backbone of campus athletics. Football, cricket, badminton, table tennis — MSC runs full inter-department leagues, tournaments, and the annual Sports Week."},
  {"id":14, "name":"Samvaad — Debate Club",   "abbr":"Samvaad",  "tags":"literature,social", "color":"#6366F1","is_open":True,  "description":"Sharpen your arguments. Samvaad runs MUN simulations, parliamentary debate circuits, elocution events, and a growing inter-college presence."},
  {"id":15, "name":"DesignX",                 "abbr":"DesignX",  "tags":"art,tech",          "color":"#F43F5E","is_open":True,  "description":"Designers, strategists, and visual thinkers. DesignX runs UI/UX sprints, branding workshops, and design critique sessions that treat creativity as a discipline."},
  {"id":16, "name":"GreenMUJ",                "abbr":"Green",    "tags":"social",            "color":"#34D399","is_open":True,  "description":"Sustainability is not a trend — it's a practice. GreenMUJ drives campus tree drives, zero-waste campaigns, and climate awareness initiatives that make a measurable difference."},
]


async def seed():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        if (await db.execute(select(func.count()).select_from(Club))).scalar() > 0:
            print("OK: clubs already seeded, skipping.")
            return
        print("Seeding clubs...")
        for c in CLUBS_DATA:
            db.add(Club(**c))
        await db.commit()
        print(f"OK: seeded {len(CLUBS_DATA)} clubs. For demo users and events: python -m app.db.demo")


if __name__ == "__main__":
    asyncio.run(seed())
