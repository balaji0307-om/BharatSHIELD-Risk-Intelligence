"""
SQLAlchemy database connection setup supporting PostgreSQL and SQLite.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

db_url = settings.effective_db_url

# SQLite requires check_same_thread=False
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency that provides an active DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Creates all database tables and ensures newly added schema columns exist."""
    Base.metadata.create_all(bind=engine)
    
    # Auto-migration to ensure columns added in updates exist without dropping data
    with engine.connect() as conn:
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(engine)
            if "transactions" in inspector.get_table_names():
                existing_cols = [c["name"] for c in inspector.get_columns("transactions")]
                if "provider" not in existing_cols:
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN provider VARCHAR(32) DEFAULT 'razorpay' NOT NULL"))
                if "customer_id" not in existing_cols:
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN customer_id VARCHAR(64)"))
                if "ip_address" not in existing_cols:
                    conn.execute(text("ALTER TABLE transactions ADD COLUMN ip_address VARCHAR(45)"))
                conn.commit()
        except Exception as e:
            import logging
            logging.getLogger("bharatshield").warning(f"Schema column migration notice: {e}")
