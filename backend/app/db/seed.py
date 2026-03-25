"""
Run once to seed the database:
  cd backend
  python -m app.db.seed
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.database import AsyncSessionLocal, create_tables
from app.models.club import Club
from app.models.event import Event


CLUBS_DATA = [
  {"id":1,  "name":"IEEE Computer Society",  "abbr":"IEEE CS",  "tags":"tech,coding",       "color":"#3B82F6","member_count":320,"is_open":True,  "description":"The campus hub for engineers, developers, and future tech leaders. From embedded systems to machine learning — IEEE CS bridges theory with real-world application through workshops, coding contests, and industry speaker sessions."},
  {"id":2,  "name":"The Music Club",          "abbr":"TMC",      "tags":"music",             "color":"#EF4444","member_count":280,"is_open":True,  "description":"A home for every kind of musician. TMC performs at every major fest, hosts open mics, jam sessions, and studio recordings. Instrumentalists, vocalists, composers — all welcome."},
  {"id":3,  "name":"Coreografia",             "abbr":"Coreo",    "tags":"dance",             "color":"#F59E0B","member_count":150,"is_open":True,  "description":"MUJ's official dance collective. Classical, contemporary, hip-hop, and everything in between. We take the stage at fests, flash mobs, and competition circuits across the country."},
  {"id":4,  "name":"ACM Student Chapter",     "abbr":"ACM",      "tags":"tech,coding",       "color":"#10B981","member_count":410,"is_open":True,  "description":"Where coders compete, collaborate, and grow. ACM drives competitive programming culture at MUJ through hackathons, DSA bootcamps, and inter-college challenges."},
  {"id":5,  "name":"Cinefilia",               "abbr":"Cine",     "tags":"film,art",          "color":"#8B5CF6","member_count":190,"is_open":False, "description":"A space for film lovers and storytellers. Cinefilia runs monthly screenings of cult cinema, short film workshops, and screenplay labs — nurturing the next generation of visual artists."},
  {"id":6,  "name":"Rotaract Club",           "abbr":"RAC",      "tags":"social",            "color":"#EC4899","member_count":260,"is_open":True,  "description":"Leadership through service. Rotaract drives community impact initiatives, skill-building programs, and social campaigns that extend well beyond the campus gates."},
  {"id":7,  "name":"Robotics & Automation",   "abbr":"RAS",      "tags":"robotics,tech",     "color":"#06B6D4","member_count":175,"is_open":True,  "description":"Builders, tinkerers, and automation enthusiasts. RAS runs drone racing, robo-war leagues, and automation workshops — pushing hardware boundaries every semester."},
  {"id":8,  "name":"CodingNinjas 10x",        "abbr":"CN 10x",   "tags":"coding,tech",       "color":"#F97316","member_count":340,"is_open":False, "description":"Placement-focused, peer-driven. Code reviews, mock interviews, DSA drills — everything you need to land your dream role, built by students who've been there."},
  {"id":9,  "name":"Enactus MUJ",             "abbr":"Enactus",  "tags":"social,tech",       "color":"#EAB308","member_count":200,"is_open":True,  "description":"Entrepreneurial action for real-world impact. Enactus MUJ builds sustainable ventures addressing community challenges — turning ideas into social enterprises."},
  {"id":10, "name":"Litmus",                  "abbr":"Litmus",   "tags":"literature,art",    "color":"#A855F7","member_count":130,"is_open":True,  "description":"The literary pulse of campus. Poetry slams, debate tournaments, creative writing workshops, and the annual lit mag that doesn't pull any punches."},
  {"id":11, "name":"CyberSpace",              "abbr":"Cyber",    "tags":"tech,coding",       "color":"#14B8A6","member_count":220,"is_open":True,  "description":"Ethical hackers, CTF competitors, and digital defenders. CyberSpace runs bug bounty hunts, cybersecurity workshops, and the beloved Breached CTF series."},
  {"id":12, "name":"Manan Photography",       "abbr":"Manan",    "tags":"photography,art",   "color":"#E879F9","member_count":245,"is_open":True,  "description":"Visual storytelling through every lens. Photo walks, editing masterclasses, studio sessions, and annual exhibitions — Manan captures the soul of campus life."},
  {"id":13, "name":"MUJ Sports Council",      "abbr":"MSC",      "tags":"sports",            "color":"#22C55E","member_count":380,"is_open":False, "description":"The backbone of campus athletics. Football, cricket, badminton, table tennis — MSC runs full inter-department leagues, tournaments, and the annual Sports Week."},
  {"id":14, "name":"Samvaad — Debate Club",   "abbr":"Samvaad",  "tags":"literature,social", "color":"#6366F1","member_count":115,"is_open":True,  "description":"Sharpen your arguments. Samvaad runs MUN simulations, parliamentary debate circuits, elocution events, and a growing inter-college presence."},
  {"id":15, "name":"DesignX",                 "abbr":"DesignX",  "tags":"art,tech",          "color":"#F43F5E","member_count":160,"is_open":True,  "description":"Designers, strategists, and visual thinkers. DesignX runs UI/UX sprints, branding workshops, and design critique sessions that treat creativity as a discipline."},
  {"id":16, "name":"GreenMUJ",                "abbr":"Green",    "tags":"social",            "color":"#34D399","member_count":140,"is_open":True,  "description":"Sustainability is not a trend — it's a practice. GreenMUJ drives campus tree drives, zero-waste campaigns, and climate awareness initiatives that make a measurable difference."},
]

EVENTS_DATA = [
  {"id":1,  "title":"HackX 3.0",            "club_id":4,  "club_name":"ACM",       "date_display":"Oct 29–31","start_date":"2025-10-29","end_date":"2025-10-31","reg_deadline":"2025-10-26","tags":"hackathon,tech,coding","team_size":"2–4",      "is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1607799279861-4dd421887fb3?w=400&h=600&fit=crop","description":"MUJ's flagship 36-hour international hackathon. 50+ universities, 2,000+ participants. Build something that matters — six weeks of mentorship, access to cloud infrastructure, and a stage that gets watched."},
  {"id":2,  "title":"Indian Ocean Live",     "club_id":2,  "club_name":"TMC",       "date_display":"Nov 1",   "start_date":"2025-11-01","end_date":"2025-11-01","reg_deadline":"2025-10-28","tags":"music",               "team_size":None,       "is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=600&fit=crop","description":"The legendary Indian Ocean plays live at Dr. Ramdas Pai Amphitheatre."},
  {"id":3,  "title":"Breached 5.0",         "club_id":11, "club_name":"CyberSpace","date_display":"Nov 7–8", "start_date":"2025-11-07","end_date":"2025-11-08","reg_deadline":"2025-11-04","tags":"tech,coding",         "team_size":"1–3",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400&h=600&fit=crop","description":"Online cryptic hunt — decode, navigate, unravel. 25+ levels of cryptography, OSINT, and logic."},
  {"id":4,  "title":"Rewind & Recode",      "club_id":1,  "club_name":"IEEE CS",   "date_display":"Oct 10–11","start_date":"2025-10-10","end_date":"2025-10-11","reg_deadline":"2025-10-07","tags":"tech,hackathon",      "team_size":"2–4",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1517180102446-f3ece451e9d8?w=400&h=600&fit=crop","description":"D3 Tech Fest flagship. Retro-themed challenges, modern problem-solving."},
  {"id":5,  "title":"Pirates of Code 2.0",  "club_id":4,  "club_name":"ACM",       "date_display":"Oct 10",  "start_date":"2025-10-10","end_date":"2025-10-10","reg_deadline":"2025-10-08","tags":"coding",              "team_size":"Solo",     "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=400&h=600&fit=crop","description":"Treasure hunt meets competitive programming."},
  {"id":6,  "title":"Hymns of Joy",         "club_id":12, "club_name":"Manan",     "date_display":"Oct 3–6", "start_date":"2025-10-03","end_date":"2025-10-06","reg_deadline":"2025-10-01","tags":"photography",         "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=400&h=600&fit=crop","description":"Photography competition by DSW. Submit your best frame across any genre."},
  {"id":7,  "title":"TechnoUtsav '25",      "club_id":1,  "club_name":"IEEE CS",   "date_display":"Nov 15–16","start_date":"2025-11-15","end_date":"2025-11-16","reg_deadline":"2025-11-10","tags":"tech,robotics",       "team_size":"2–5",      "is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=600&fit=crop","description":"Annual tech mega-fest. Robo-wars, drone racing, AI art battles, CTF, and 15+ events across two full days."},
  {"id":8,  "title":"Groove Nation",        "club_id":3,  "club_name":"Coreo",     "date_display":"Nov 22",  "start_date":"2025-11-22","end_date":"2025-11-22","reg_deadline":"2025-11-18","tags":"dance",               "team_size":"6–12",     "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1547153760-18fc86324498?w=400&h=600&fit=crop","description":"Inter-college group dance battle. Western, classical, freestyle."},
  {"id":9,  "title":"Open Mic Night",       "club_id":2,  "club_name":"TMC",       "date_display":"Oct 17",  "start_date":"2025-10-17","end_date":"2025-10-17","reg_deadline":"2025-10-15","tags":"music,art",           "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=400&h=600&fit=crop","description":"Monthly open mic — originals, covers, poetry, spoken word."},
  {"id":10, "title":"Flash Mob @ Atrium",   "club_id":3,  "club_name":"Coreo",     "date_display":"Oct 24",  "start_date":"2025-10-24","end_date":"2025-10-24","reg_deadline":None,         "tags":"dance",               "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1574169208507-84376144848b?w=400&h=600&fit=crop","description":"Surprise flash mob at the central atrium."},
  {"id":11, "title":"RoboWars 2025",        "club_id":7,  "club_name":"RAS",       "date_display":"Nov 8–9", "start_date":"2025-11-08","end_date":"2025-11-09","reg_deadline":"2025-11-03","tags":"robotics,tech",       "team_size":"2–4",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=600&fit=crop","description":"Bot battles, drone races, and sumo-bots."},
  {"id":12, "title":"Cinéclub Screening",   "club_id":5,  "club_name":"Cine",      "date_display":"Oct 14",  "start_date":"2025-10-14","end_date":"2025-10-14","reg_deadline":None,         "tags":"film,art",            "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400&h=600&fit=crop","description":"Monthly cult classic screening followed by an open discussion."},
  {"id":13, "title":"DSA Bootcamp",         "club_id":8,  "club_name":"CN 10x",    "date_display":"Oct 20–22","start_date":"2025-10-20","end_date":"2025-10-22","reg_deadline":"2025-10-17","tags":"coding,tech",         "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=600&fit=crop","description":"3-day intensive data structures and algorithms workshop."},
  {"id":14, "title":"Football League S2",   "club_id":13, "club_name":"MSC",       "date_display":"Oct 6–12","start_date":"2025-10-06","end_date":"2025-10-12","reg_deadline":"2025-10-03","tags":"sports",              "team_size":"11",       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400&h=600&fit=crop","description":"Campus football league, season two."},
  {"id":15, "title":"MUN 2025",             "club_id":14, "club_name":"Samvaad",   "date_display":"Oct 25–26","start_date":"2025-10-25","end_date":"2025-10-26","reg_deadline":"2025-10-20","tags":"literature,social",   "team_size":"Solo/Pair","is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1606761568499-6d2451b23c66?w=400&h=600&fit=crop","description":"Two-day Model United Nations with 8 committees."},
  {"id":16, "title":"UI/UX Design Sprint",  "club_id":15, "club_name":"DesignX",   "date_display":"Oct 16–17","start_date":"2025-10-16","end_date":"2025-10-17","reg_deadline":"2025-10-13","tags":"art,tech",            "team_size":"1–2",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1561070791-2526d30994b5?w=400&h=600&fit=crop","description":"48-hour design challenge. Prototype a real product."},
  {"id":17, "title":"Campus Clean Drive",   "club_id":16, "club_name":"GreenMUJ",  "date_display":"Oct 2",   "start_date":"2025-10-02","end_date":"2025-10-02","reg_deadline":None,         "tags":"social",              "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400&h=600&fit=crop","description":"Join 200+ volunteers to clean up campus, plant saplings."},
  {"id":18, "title":"Literary Fest 2025",   "club_id":10, "club_name":"Litmus",    "date_display":"Nov 5–6", "start_date":"2025-11-05","end_date":"2025-11-06","reg_deadline":"2025-11-01","tags":"literature",          "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=600&fit=crop","description":"Poetry slam, creative writing contest, storytelling showcase."},
  {"id":19, "title":"Salsa & Bachata Night","club_id":3,  "club_name":"Coreo",     "date_display":"Nov 13",  "start_date":"2025-11-13","end_date":"2025-11-13","reg_deadline":"2025-11-10","tags":"dance",               "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1519742866993-66d3cfef4bbd?w=400&h=600&fit=crop","description":"A proper evening of salsa, bachata, and freestyle."},
  {"id":20, "title":"Startup Pitch Day",    "club_id":9,  "club_name":"Enactus",   "date_display":"Oct 28",  "start_date":"2025-10-28","end_date":"2025-10-28","reg_deadline":"2025-10-24","tags":"social,tech",         "team_size":"2–5",      "is_hot":True,  "poster_url":"https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=400&h=600&fit=crop","description":"Pitch your social venture to investors and industry leaders."},
  {"id":21, "title":"Drone Racing Cup",     "club_id":7,  "club_name":"RAS",       "date_display":"Oct 31",  "start_date":"2025-10-31","end_date":"2025-10-31","reg_deadline":"2025-10-27","tags":"robotics",            "team_size":"Solo",     "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=400&h=600&fit=crop","description":"FPV drone racing through a custom obstacle course."},
  {"id":22, "title":"Jazz & Blues Evening", "club_id":2,  "club_name":"TMC",       "date_display":"Nov 20",  "start_date":"2025-11-20","end_date":"2025-11-20","reg_deadline":None,         "tags":"music",               "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?w=400&h=600&fit=crop","description":"Intimate evening of jazz and blues at the open-air courtyard."},
  {"id":23, "title":"Photo Walk: Old City", "club_id":12, "club_name":"Manan",     "date_display":"Oct 19",  "start_date":"2025-10-19","end_date":"2025-10-19","reg_deadline":"2025-10-17","tags":"photography",         "team_size":None,       "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400&h=600&fit=crop","description":"Guided photo walk through Jaipur's walled city."},
  {"id":24, "title":"Badminton Open",       "club_id":13, "club_name":"MSC",       "date_display":"Nov 10–11","start_date":"2025-11-10","end_date":"2025-11-11","reg_deadline":"2025-11-07","tags":"sports",              "team_size":"Solo/Pair","is_hot":False, "poster_url":"https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=400&h=600&fit=crop","description":"Inter-department badminton open. Singles and doubles."},
  {"id":25, "title":"Short Film Fest",      "club_id":5,  "club_name":"Cine",      "date_display":"Nov 28–29","start_date":"2025-11-28","end_date":"2025-11-29","reg_deadline":"2025-11-20","tags":"film",               "team_size":"2–8",      "is_hot":False, "poster_url":"https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=400&h=600&fit=crop","description":"Submit your short film (max 15 minutes). Jury screening and awards ceremony."},
]


async def seed():
    await create_tables()
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        count = await db.execute(select(func.count()).select_from(Club))
        if count.scalar() > 0:
            print("✓ Database already seeded, skipping.")
            return

        print("Seeding clubs...")
        for c in CLUBS_DATA:
            db.add(Club(**c))
        await db.flush()

        print("Seeding events...")
        from datetime import date
        for e in EVENTS_DATA:
            ev = Event(
                id=e["id"], title=e["title"], description=e["description"],
                club_id=e["club_id"], club_name=e["club_name"],
                date_display=e["date_display"],
                start_date=date.fromisoformat(e["start_date"]),
                end_date=date.fromisoformat(e["end_date"]),
                reg_deadline=date.fromisoformat(e["reg_deadline"]) if e["reg_deadline"] else None,
                tags=e["tags"], team_size=e["team_size"],
                poster_url=e["poster_url"], is_hot=e["is_hot"],
            )
            db.add(ev)

        await db.commit()
        print("✓ Seeding complete — 16 clubs, 25 events.")


if __name__ == "__main__":
    asyncio.run(seed())
