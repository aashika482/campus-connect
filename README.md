# CamPulse — Campus Club & Event Discovery

> A Club and Events discovery platform for college students and club committees.

**Live Demo → [campus-connect-sooty-sigma.vercel.app](https://campus-connect-sooty-sigma.vercel.app)**

---

## What It Does

CamPulse helps students at MUJ discover clubs and events happening on campus. Everyone signs up with their college email, one account per person; the email's domain makes it a student or a faculty account.

**Account types** (one per person):

- **Student** — browse events, register, save favourites, join clubs, comment
- **Faculty** — can be made a club's faculty coordinator by the DSW
- **Alumni** — set by the DSW on graduation; team roles end, memberships stay
- **DSW** (Dean of Student Welfare office) — approves everything: club owners and editors, faculty coordinators, account types; creates clubs, features events as "hot", moderates any discussion
- **Platform admin** (tech team) — appoints DSW accounts; no business authority

**Club roles** (per club, a person can hold several):

- **Member** — joined the club (students; no leaving from the app)
- **Owner** — leads the club; a student asks on the club's page and the DSW approves. One per club
- **Editor** — proposed by the owner or an editor, approved by the DSW (up to `MAX_EDITORS_PER_CLUB`)
- **Faculty coordinator** — assigned by the DSW

Owners, editors and faculty coordinators are the club's *team*: they post events, see members and registrations, and moderate their club's discussions. A student is on one club's team at a time unless the DSW grants an exception. Every governance action goes to an audit log.

---

## Tech Stack

| Layer        | Technology                                                   |
| ------------ | ------------------------------------------------------------ |
| Frontend     | React 18 + TypeScript (Vite)                                 |
| Styling      | Inline CSS with CSS variables — no Tailwind, no UI libraries |
| State        | Zustand                                                      |
| Routing      | React Router v6                                              |
| Backend      | Python FastAPI (async)                                       |
| ORM          | SQLAlchemy async                                             |
| Database     | Neon (cloud PostgreSQL)                                      |
| Auth         | JWT (access + refresh tokens)                                |
| Image Upload | Cloudinary (browser uploads, signed by the backend)          |
| Deployment   | Railway (backend) + Vercel (frontend)                        |

---

## Features

- **Event discovery** — browse all campus events with filters by tag, search by title, club, description and tags
- **Event detail pages** — poster, description, venue, dates, registration fee, prize pool
- **Club pages** — club info, member count, join, social links, ask to run the club
- **Registration & saving** — register for events (and cancel until the event ends), save them for later
- **Discussions** — comment on events and reply to each other, with official club replies badged; 15-minute edit window and in-app reply notifications
- **Calendar** — month/year navigation over every event
- **Club dashboard** — for a club's approved team: post, edit and delete events, see members and registrations, moderate discussions
- **Club teams, verified** — owner/editor requests wait for the DSW; a club's dashboard opens only for its approved team
- **Yearly memberships** — students join a club for the academic year (until 31 July) as non-working members; joining again renews
- **Working teams** — while a club is recruiting, members apply; the owner/editors shortlist and recommend after an offline interview, the faculty coordinator approves. Last year's working members renew the same way. A club decides whether its working members may also work for other clubs
- **Club roster** — everyone sees this year's member names; the working team also sees course, interests and roles (never contact details)
- **Announcements** — the club's team posts updates for its working team, who react and comment
- **Team chat** — a live group chat per club for its working team (WebSockets on our own backend; history kept in Postgres)
- **Club settings** — taking new members (Open/Closed), private/public, recruiting on/off, the multi-club rule, and the yearly fees (default ₹500 member / ₹1000 working)
- **Private clubs** — hidden from outsiders' listings and search, along with their upcoming events; the page and past events stay viewable. The club's team or the DSW switches it
- **Leaving a club** — members ask the DSW to leave the working team (staying a member) or the club; the DSW approves or rejects
- **Member benefits** — perks a club lists for all members or only its working team, shown on the club page
- **New club requests** — students propose a club (with a founding team and a faculty coordinator); the coordinator confirms (the request waits if they haven't joined yet), then the DSW approves and the club is created with the student as owner and the founding team as editors
- **Real club data** — the 102 clubs from the DSW's audit; each year's audit (category, marks, remarks) is kept per academic year and visible only to the DSW (DSW Console → Evaluations). Coordinators named in the audit become their club's faculty coordinator when they sign in with their verified college account
- **Club profiles** — the club's team edits its short name, description, tags (or leaves it "Not categorized"), colour and social links
- **For You** — upcoming events ranked on the server by interests, clubs you're in, closing deadlines and popularity
- **DSW console** — review requests, see and end club teams, assign faculty, switch account types, deactivate or reactivate accounts, read the activity log
- **Platform console** — the tech team appoints DSW accounts
- **Verified sign-in** — "Sign in with Microsoft" (MUJ accounts; name from the university directory) or sign-up with a code emailed to the college address; one account per email, and the domain makes it a student or faculty account. Password logins take a second step (an emailed code or an authenticator app), remembered per browser for 30 days; 5 wrong passwords lock password login for 15 minutes. Microsoft accounts can add a password (e.g. to keep access as alumni)

---

## Project Structure

```
campus-connect/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, route registration
│   ├── requirements.txt         # + requirements-dev.txt for tests
│   ├── Procfile                 # Railway start command
│   ├── alembic/                 # database migrations
│   ├── tests/                   # pytest: auth and permissions
│   └── app/
│       ├── api/routes/          # auth, users, events, clubs, announcements, chat, club_requests,
│       │                        #   discussions, notifications, uploads, admin
│       ├── core/                # config, security (JWT, bcrypt, codes), governance rules, mail
│       ├── db/                  # async engine + session, club import, demo data, bootstrap_admin
│       ├── models/              # SQLAlchemy models
│       └── schemas/             # Pydantic schemas
└── frontend/
    ├── src/
    │   ├── api/client.ts        # Axios client, auto token refresh
    │   ├── context/             # Zustand auth + toast stores
    │   ├── hooks/useData.ts     # Data fetching hooks
    │   ├── pages/               # All page components
    │   ├── components/          # Nav, search, cards, modals
    │   └── styles/globals.css   # All CSS variables and shared classes
    └── vercel.json              # SPA routing fix for Vercel
```

---

## Running Locally

The project needs **Python 3.12** (the pinned packages don't install on 3.13+) and **Node 22**. Nothing has to be installed system-wide: both can live inside the project, with their caches, in the git-ignored `.tools/` folder and `backend/venv`.

### One-time setup

```bash
# Python 3.12 + backend packages (uv fetches 3.12 into .tools/, any system Python 3 can bootstrap it)
export UV_PYTHON_INSTALL_DIR=$PWD/.tools/python UV_CACHE_DIR=$PWD/.tools/cache/uv PIP_CACHE_DIR=$PWD/.tools/cache/pip
python3 -m venv .tools/bootstrap && .tools/bootstrap/bin/pip install uv
.tools/bootstrap/bin/uv venv --seed -p 3.12 backend/venv
VIRTUAL_ENV=$PWD/backend/venv .tools/bootstrap/bin/uv pip install -r backend/requirements-dev.txt nodeenv
rm -rf .tools/bootstrap

# Node 22 inside the same venv, with npm/pip caches kept in .tools/
source backend/venv/bin/activate
nodeenv -p -n 22.12.0 --prebuilt
cat >> backend/venv/bin/activate <<EOF
export npm_config_cache="$PWD/.tools/cache/npm" PIP_CACHE_DIR="$PWD/.tools/cache/pip"
EOF
```

From then on, `source backend/venv/bin/activate` gives you Python 3.12, `node` and `npm`. In VS Code, pick `backend/venv/bin/python` as the interpreter.

### Local database

A local Postgres 16 ships with the `pgserver` dev package; its data lives in `.tools/pgdata`. Start it once after every reboot (the first run also creates it):

```bash
cd backend
python -c "import pgserver; s = pgserver.get_server('../.tools/pgdata', cleanup_mode=None); s.psql('SELECT 1')"
python -c "import pgserver; pgserver.get_server('../.tools/pgdata', cleanup_mode=None).psql('CREATE DATABASE campulse;')"  # first time only
```

### Backend

Create `backend/.env` (copy from `.env.example`). For the local database:

```
DATABASE_URL=postgresql://postgres:@/campulse?host=/absolute/path/to/campus-connect/.tools/pgdata
DATABASE_SSL=False
JWT_SECRET_KEY=generate-with: python -c "import secrets; print(secrets.token_hex(32))"
```

```bash
cd backend
alembic upgrade head        # create / update the database tables
uvicorn main:app --reload
# API running at http://localhost:8000
```

**Fresh database:** after `alembic upgrade head`, load the real club list, then (optionally) demo data:

```bash
python -m app.db.import_clubs                                     # the 102 real clubs (names, short names, tags)
python -m app.db.import_clubs AUDIT.xlsx --year 2024-25           # or with the DSW's audit sheet: + that year's
                                                                  # evaluations and faculty coordinators
DEMO_MODE=true DEMO_PASSWORD=pick-one python -m app.db.demo        # wipes everything except clubs, adds demo
                                                                   # people, teams and events dated around today
```

Signing in with a password asks for a code: without `SMTP_HOST` it's printed in the backend's terminal ("No SMTP_HOST set, so this email was not sent"). Tick "Don't ask again on this browser" to skip it for 30 days.

The audit sheet is private (scores, remarks, faculty emails): keep it out of git (`*.xlsx` is ignored) and share it only with people who need it. Each year's sheet goes through the same command with its `--year`; running it again never duplicates anything, and clubs keep whatever their owners have edited. `--replace` also deletes clubs that aren't in the sheet (without a sheet: not in the real list, e.g. the old sample clubs).

**First platform admin:** only possible from the command line. They then appoint DSW accounts in the web app.

```bash
python -m app.db.bootstrap_admin tech@jaipur.manipal.edu           # creates or promotes; --revoke to undo
```

**Tests** (auth and permissions, against a throwaway Postgres that starts by itself):

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install                 # with backend/venv active, so the project's Node 22 is used
```

Create `frontend/.env` (copy from `.env.example`):

```
VITE_API_URL=http://localhost:8000
```

```bash
npm run dev
# App running at http://localhost:5173
```

---

## Environment Variables

### Backend (Railway)

| Variable         | Description                                      |
| ---------------- | ------------------------------------------------ |
| `DATABASE_URL`   | Neon PostgreSQL connection string                |
| `JWT_SECRET_KEY` | Secret key for signing JWTs                      |
| `DEBUG`          | `False` in production                            |
| `CORS_ORIGINS`   | Comma-separated allowed frontend origins (default `http://localhost:5173`) |
| `DATABASE_SSL`   | `True` (default, Neon). `False` only for a local Postgres without SSL |
| `STUDENT_EMAIL_DOMAINS` / `FACULTY_EMAIL_DOMAINS` | Comma-separated college domains allowed to sign up (defaults `muj.manipal.edu` / `jaipur.manipal.edu`) |
| `MAX_EDITORS_PER_CLUB` | Most active editors per club (default `5`; a club has one owner) |
| `TIMEZONE` | The college's time zone for "today" (deadlines, event endings, 31 July). Default `Asia/Kolkata` |
| `DEMO_MODE` / `DEMO_PASSWORD` | Only for `python -m app.db.demo`. Never set `DEMO_MODE` in production |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Signed poster uploads (optional) |
| `MICROSOFT_CLIENT_ID` / `MICROSOFT_TENANT_ID` | Sign in with Microsoft (see below). Empty: the button is hidden |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `MAIL_FROM` | Sending sign-up and login codes. Required in production; locally, leave `SMTP_HOST` empty and codes print in the backend terminal |

**Run one backend process.** The team chat keeps its live connections in the process's memory, so the
start command (`Procfile`) runs a single uvicorn process. Adding `--workers` or more Railway replicas would
need the chat to share messages between processes (e.g. Postgres `LISTEN/NOTIFY`) first.

### Sign in with Microsoft (for the DSW / IT)

In the Microsoft Entra admin center of the university's tenant: **App registrations → New registration**
- Supported account types: *Accounts in this organizational directory only*
- Redirect URI: platform **Single-page application**, `https://<the deployed site>/msal-redirect.html` (and `http://localhost:5173/msal-redirect.html` for local development)

Then set `MICROSOFT_CLIENT_ID` (Application / client ID) and `MICROSOFT_TENANT_ID` (Directory / tenant ID, the GUID) on the backend. The frontend reads them from the backend; it needs nothing extra. The app only needs the default `openid profile email` permissions.

### Frontend (Vercel)

| Variable                        | Description                  |
| ------------------------------- | ---------------------------- |
| `VITE_API_URL`                  | Deployed Railway backend URL |

---

## Database Schema

| Table           | Purpose                             |
| --------------- | ----------------------------------- |
| `users`         | One account per person, with its account type |
| `clubs`         | Club profiles                       |
| `events`        | Events posted by clubs              |
| `club_roles`    | A person's roles in a club (member, working member, editor, owner, faculty coordinator), their status, and for memberships the academic year's end |
| `club_applications` | Members applying to (or renewing their place on) a club's working team |
| `leave_requests` | Members asking the DSW to leave a club's working team, or the club |
| `club_benefits` | Perks a club lists for its members or working team |
| `club_requests` | Students proposing new clubs, with the coordinator's and the DSW's decisions |
| `chat_messages` | Each club's working-team chat |
| `club_evaluations` | The DSW's yearly audit of each club (DSW only) |
| `coordinator_invites` | Faculty the audit names as coordinators, until they sign in |
| `club_announcements` / `announcement_comments` / `announcement_reactions` | The working team's updates |
| `audit_log`     | Who did what, when (governance actions) |
| `registrations` | User ↔ Event registrations          |
| `saved_events`  | User saved events                   |
| `discussions`   | Comments and replies on events      |
| `notifications` | In-app reply/comment notifications  |

---

## Roadmap

### Next

- **Going live** — Neon, Railway and Vercel; the Microsoft app registration and the college's email service; the final pre-handoff check (build, smoke test of every flow, secrets and `.env.example`)

### Future updates

- **Payments** — paid event registration and yearly membership fees through a split-payout gateway (e.g. Razorpay Route): the member fee on joining, the rest of the working fee once accepted; club bank-account KYC, orders, webhooks, refunds and a finance ledger; member discounts on paid events
- **Smarter recommendations** — "students who went to X also went to Y" from registration history
- **Semantic search** — embedding search over events and clubs with pgvector on Postgres

---
