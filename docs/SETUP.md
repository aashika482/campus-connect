# CamPulse — Setup Guide

Complete fullstack setup: React + Vite frontend, FastAPI backend, Neon PostgreSQL.

---

## Project Structure

```
campulse/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── requirements.txt
│   ├── .env.example               # Copy to .env
│   └── app/
│       ├── api/routes/
│       │   ├── auth.py            # /api/auth  — login, register, refresh
│       │   ├── events.py          # /api/events — CRUD + register + save
│       │   ├── clubs.py           # /api/clubs  — list + join/leave
│       │   └── users.py           # /api/users  — profile
│       ├── core/
│       │   ├── config.py          # Pydantic settings (.env)
│       │   ├── security.py        # JWT (access + refresh), bcrypt
│       │   └── deps.py            # FastAPI dependencies (get_current_user)
│       ├── db/
│       │   ├── database.py        # Async SQLAlchemy + Neon setup
│       │   └── seed.py            # Seeds 16 clubs + 25 events
│       ├── models/                # SQLAlchemy ORM models
│       └── schemas/               # Pydantic request/response schemas
│
└── frontend/
    ├── index.html
    ├── vite.config.ts             # Proxies /api → localhost:8000
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx                # Router + protected routes
    │   ├── api/client.ts          # Axios + auto token refresh
    │   ├── context/
    │   │   ├── authStore.ts       # Zustand auth store
    │   │   └── toastStore.ts      # Zustand toast store
    │   ├── hooks/useData.ts       # useEvents, useClubs, useUserEvents…
    │   ├── types/index.ts         # All TypeScript types
    │   ├── styles/globals.css     # Design tokens (identical to prototype)
    │   ├── components/
    │   │   ├── layout/Nav.tsx     # Nav with search + notifications
    │   │   ├── layout/GlobalSearch.tsx
    │   │   └── ui/Toast.tsx
    │   └── pages/
    │       ├── LoginPage.tsx
    │       ├── RegisterPage.tsx   # 2-step student / 1-step member
    │       ├── HomePage.tsx       # Hot events + For You + Upcoming
    │       ├── EventsPage.tsx     # Filterable grid
    │       ├── ClubsPage.tsx      # Club cards with join
    │       └── OtherPages.tsx     # Saved, Profile, Calendar, Admin
```

---

## Step 1 — Create a Neon Database

1. Go to **[neon.tech](https://neon.tech)** → New Project
2. Name it `campulse` (or anything you like)
3. Choose a region close to you (e.g. `AWS ap-south-1` for India)
4. Once created, click **"Connection string"** → copy the `postgresql://...` URL
5. Keep this tab open — you'll paste it into `.env` next

---

## Step 2 — Backend Setup

```bash
cd campulse/backend

# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file
cp .env.example .env
```

Open `.env` and fill in your values:

```env
DATABASE_URL=postgresql://your-neon-connection-string-here
JWT_SECRET_KEY=your-secret-key-here
```

Generate a strong JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

```bash
# 4. Seed the database (creates tables + inserts all 16 clubs & 25 events)
python -m app.db.seed

# 5. Start the server
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** — you should see the full Swagger UI.

---

## Step 3 — Frontend Setup

```bash
cd campulse/frontend

# 1. Install dependencies
npm install

# 2. Create your .env file
cp .env.example .env
# Default: VITE_API_URL=http://localhost:8000
# (Vite also proxies /api → 8000, so either works)

# 3. Start the dev server
npm run dev
```

Open **http://localhost:5173** — the app is live.

---

## Step 4 — First Login

The seed script creates data but no users. Register directly in the app:

- Go to `/register`
- Pick **Student** → fill in details → pick interests
- Or pick **Club Member** → enter your club name

Everything hooks into the real Neon database from here.

---

## API Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | ✗ | Login → access + refresh tokens |
| POST | `/api/auth/register/student` | ✗ | Register as student |
| POST | `/api/auth/register/member` | ✗ | Register as club member |
| POST | `/api/auth/refresh` | ✗ | Refresh access token |
| GET  | `/api/events` | ✗ | List events (filter: `?tag=tech&hot=true`) |
| POST | `/api/events/{id}/register` | ✓ | Register for event |
| POST | `/api/events/{id}/save` | ✓ | Save/bookmark event |
| GET  | `/api/events/me/registered` | ✓ | My registered event IDs |
| GET  | `/api/events/me/saved` | ✓ | My saved event IDs |
| GET  | `/api/clubs` | ✗ | List all clubs |
| POST | `/api/clubs/{id}/join` | ✓ | Join a club |
| GET  | `/api/users/me` | ✓ | Get my profile |
| PATCH| `/api/users/me` | ✓ | Update my profile |

Full docs: **http://localhost:8000/docs**

---

## Auth Flow (JWT)

```
Login / Register
      │
      ▼
  access_token (30 min)   ← attached to every API request
  refresh_token (7 days)  ← stored in localStorage

When access_token expires:
  Axios interceptor → POST /api/auth/refresh → new token pair
  All queued requests automatically retry with the new token
  If refresh fails → redirect to /login
```

---

## Deployment (later)

**Backend — Railway or Render:**
```bash
# Set these env vars in your platform dashboard:
DATABASE_URL=...   # same Neon URL
JWT_SECRET_KEY=... # same secret
```

**Frontend — Vercel or Netlify:**
```bash
npm run build   # outputs to dist/
# Set in platform: VITE_API_URL=https://your-api.railway.app
```

---

## Common Issues

**`asyncpg.exceptions.InvalidCatalogNameError`**  
→ The database name in your Neon URL doesn't exist. Use the exact URL from the Neon dashboard.

**CORS error in browser**  
→ Make sure `http://localhost:5173` is in `CORS_ORIGINS` in `config.py`.

**`ModuleNotFoundError: No module named 'app'`**  
→ Run `uvicorn` from the `backend/` directory, not from `campulse/`.

**Tables not created**  
→ Run the seed script first: `python -m app.db.seed`

---

## Next Steps (when you're ready)

- Wire `EventModal` and `ClubModal` from your prototype into `App.tsx`
- Add image upload for event posters (Cloudinary or Supabase Storage)
- Add email verification on registration
- Add a "Create Event" form in the Admin dashboard
- Deploy with Railway (backend) + Vercel (frontend)
