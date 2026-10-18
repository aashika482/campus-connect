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
| Image Upload | Cloudinary (direct frontend upload)                          |
| Deployment   | Railway (backend) + Vercel (frontend)                        |

---

## Features

- **Event discovery** — browse all campus events with filters by tag, search by name
- **Event detail pages** — poster, description, venue, dates, registration fee, prize pool
- **Club pages** — club info, member count, join, social links, ask to run the club
- **Registration & saving** — register for events, save them for later
- **Discussions** — comment on events and reply to each other, with official club replies badged; 15-minute edit window and in-app reply notifications
- **Admin dashboard** — post events, view registrations, manage discussion feed
- **Club teams, verified** — owner/editor requests wait for the DSW; a club's dashboard opens only for its approved team
- **DSW console** — review requests, see and end club teams, assign faculty, switch account types, read the activity log
- **Platform console** — the tech team appoints DSW accounts
- **Auth** — separate registration flows for students and club committee members

---

## Project Structure

```
Club_Discovery_App/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, route registration
│   ├── requirements.txt
│   ├── Procfile                 # Railway start command
│   └── app/
│       ├── api/routes/          # auth, events, clubs, users, discussions
│       ├── core/                # config, security (JWT + bcrypt)
│       ├── db/                  # async engine, session, table creation
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

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env` (copy from `.env.example`):

```
DATABASE_URL=your_neon_connection_string
JWT_SECRET_KEY=your_secret_key
DEBUG=False
```

```bash
alembic upgrade head        # create / update the database tables
uvicorn main:app --reload
# API running at http://localhost:8000
```

**Fresh database:** after `alembic upgrade head`, load the real club list, then (optionally) demo data:

```bash
python -m app.db.seed                                             # the real clubs (skips if any exist)
DEMO_MODE=true DEMO_PASSWORD=pick-one python -m app.db.demo        # wipes everything except clubs, adds demo
                                                                   # people, teams and events dated around today
```

**First platform admin:** only possible from the command line. They then appoint DSW accounts in the web app.

```bash
python -m app.db.bootstrap_admin tech@jaipur.manipal.edu           # creates or promotes; --revoke to undo
```

**Tests** (auth and permissions, against a real Postgres that starts by itself):

```bash
pip install -r requirements-dev.txt
pytest
```

### Frontend

```bash
cd frontend
npm install
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
| `DEMO_MODE` / `DEMO_PASSWORD` | Only for `python -m app.db.demo`. Never set `DEMO_MODE` in production |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Signed poster uploads (optional) |

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
| `club_roles`    | A person's roles in a club (member, editor, owner, faculty coordinator) and their status |
| `audit_log`     | Who did what, when (governance actions) |
| `registrations` | User ↔ Event registrations          |
| `saved_events`  | User saved events                   |
| `discussions`   | Comments and replies on events      |
| `notifications` | In-app reply/comment notifications  |

---
