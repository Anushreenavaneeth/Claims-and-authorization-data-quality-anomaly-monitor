from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
import app.models  # noqa: F401
from app.routers import auth, protected, admin, anomalies, ml, datasets, audit

from sqlalchemy import text

# Ensure database tables exist
try:
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        for col_sql in [
            "ALTER TABLE users ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE users ADD COLUMN invite_token VARCHAR(255);",
            "ALTER TABLE users ADD COLUMN invite_token_expires_at TIMESTAMP;",
        ]:
            try:
                conn.execute(text(col_sql))
                conn.commit()
            except Exception:
                pass  # Column already exists
except Exception as e:
    print(f"[DB] Table creation warning: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend API for Healthcare Data Operations Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",  # allow all localhost ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(protected.router)
app.include_router(admin.router)
app.include_router(anomalies.router)
app.include_router(ml.router)
app.include_router(datasets.router)
app.include_router(audit.router)


@app.get("/")
def read_root():
    return {"message": "Healthcare Data Operations Platform API"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "env": settings.ENV}
