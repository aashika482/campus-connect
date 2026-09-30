from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import engine
from app.api.routes import auth, events, clubs, users, discussions, notifications, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The schema is managed by Alembic migrations (`alembic upgrade head`), not created here
    yield
    # Close pooled DB connections on shutdown (including each --reload restart)
    await engine.dispose()


app = FastAPI(
    title="CamPulse API",
    description="Campus life discovery platform for MUJ",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,   prefix="/api/auth",   tags=["Auth"])
app.include_router(users.router,  prefix="/api/users",  tags=["Users"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(clubs.router,  prefix="/api/clubs",  tags=["Clubs"])
app.include_router(discussions.router, prefix="/api/discussions", tags=["Discussions"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["Uploads"])

@app.get("/")
async def root():
    return {"message": "CamPulse API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
