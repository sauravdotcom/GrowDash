import logging
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.api.ai import router as ai_router
from app.api.analytics import router as analytics_router
from app.api.trades import router as trades_router
from app.config import settings
from app.db.session import Base, engine


logger = logging.getLogger(__name__)

app = FastAPI(title="GrowDash API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as exc:
        # Local DX: if the configured PostgreSQL DB is missing, create it once.
        if _ensure_database_exists_for_postgres(exc):
            Base.metadata.create_all(bind=engine)
            return
        logger.error("Failed to connect to PostgreSQL at %s", settings.database_url)
        raise RuntimeError(
            "Database connection failed. Start PostgreSQL and verify DATABASE_URL."
        ) from exc
    except SQLAlchemyError as exc:
        logger.error("Failed to connect to PostgreSQL at %s", settings.database_url)
        raise RuntimeError(
            "Database connection failed. Start PostgreSQL and verify DATABASE_URL."
        ) from exc


def _ensure_database_exists_for_postgres(connect_error: OperationalError) -> bool:
    message = str(connect_error).lower()
    if "database" not in message or "does not exist" not in message:
        return False

    try:
        db_url = make_url(settings.database_url)
    except Exception:
        return False

    if not db_url.drivername.startswith("postgresql") or not db_url.database:
        return False

    database_name = db_url.database
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        logger.error("Unsafe database name '%s'. Skipping auto-create.", database_name)
        return False

    admin_url = db_url.set(database="postgres")
    admin_engine = create_engine(
        admin_url.render_as_string(hide_password=False),
        pool_pre_ping=True,
        isolation_level="AUTOCOMMIT",
    )

    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": database_name},
            ).scalar()
            if exists:
                return True
            conn.execute(text(f'CREATE DATABASE "{database_name}"'))
            logger.info("Created missing database '%s'.", database_name)
            return True
    except Exception as exc:
        logger.error("Auto-create database failed: %s", exc)
        return False
    finally:
        admin_engine.dispose()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(trades_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)
app.include_router(ai_router, prefix=settings.api_v1_prefix)
