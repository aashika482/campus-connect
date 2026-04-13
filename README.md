# CamPulse — Campus Club & Event Discovery

> A Club and Events discovery platform for college students and club committees.

**Live Demo → [campus-connect-sooty-sigma.vercel.app](https://campus-connect-sooty-sigma.vercel.app)**

---

## What It Does

CamPulse helps students at MUJ discover clubs and events happening on campus. There are two types of users:

- **Students** — browse events, register, save favourites, join clubs, and leave comments
- **Club Members** — manage their club profile, post events with poster images, view registrations, and reply to student discussions via a dashboard

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
- **Club pages** — club info, member count, join/leave, social links
- **Registration & saving** — register for events, save them for later
- **Discussions** — comment on events, club admins can reply
- **Admin dashboard** — post events, view registrations, manage discussion feed
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
uvicorn main:app --reload
# API running at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env` (copy from `.env.example`):

```
VITE_API_URL=http://localhost:8000
VITE_CLOUDINARY_CLOUD_NAME=your_cloud_name
VITE_CLOUDINARY_UPLOAD_PRESET=your_preset
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
| `FRONTEND_URLS`  | Comma-separated list of allowed frontend origins |

### Frontend (Vercel)

| Variable                        | Description                  |
| ------------------------------- | ---------------------------- |
| `VITE_API_URL`                  | Deployed Railway backend URL |
| `VITE_CLOUDINARY_CLOUD_NAME`    | Cloudinary cloud name        |
| `VITE_CLOUDINARY_UPLOAD_PRESET` | Unsigned upload preset name  |

---

## Database Schema

| Table           | Purpose                             |
| --------------- | ----------------------------------- |
| `users`         | Students and club committee members |
| `clubs`         | Club profiles                       |
| `events`        | Events posted by clubs              |
| `memberships`   | User ↔ Club joins                   |
| `registrations` | User ↔ Event registrations          |
| `saved_events`  | User saved events                   |
| `discussions`   | Comments and replies on events      |

---
