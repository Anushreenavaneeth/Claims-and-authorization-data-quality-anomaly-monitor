from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Use SQLite if no real DATABASE_URL is configured (no PostgreSQL available)
_url = settings.DATABASE_URL
if _url.startswith("postgresql") or _url.startswith("postgres"):
    try:
        import psycopg2  # noqa: F401
        engine = create_engine(_url, pool_pre_ping=True)
        # Quick connection check
        with engine.connect():
            pass
    except Exception:
        import os
        from pathlib import Path
        _db_path = Path(__file__).resolve().parents[2] / "data" / "app.db"
        _db_path.parent.mkdir(parents=True, exist_ok=True)
        _sqlite_url = f"sqlite:///{_db_path}"
        print(f"[DB] PostgreSQL unavailable — falling back to SQLite: {_sqlite_url}")
        engine = create_engine(
            _sqlite_url,
            connect_args={"check_same_thread": False, "timeout": 30},
        )
else:
    _connect_args = {"check_same_thread": False, "timeout": 30} if _url.startswith("sqlite") else {}
    engine = create_engine(_url, pool_pre_ping=True, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Create all tables if they don't exist (used by SQLite fallback and startup)."""
    # Import all models so Base.metadata knows about them
    from app.models import user, anomaly, dataset_version, review, action  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
