# backend/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

# ── Engine
# pool_pre_ping=True: tests connection before using it (handles Supabase timeouts)
# pool_size=5: max 5 permanent connections (safe for Supabase free tier: 60 max)
# max_overflow=10: allow 10 extra connections during traffic spikes
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# ── Session factory
# autocommit=False: we manually commit so we control when data is saved
# autoflush=False:  we manually flush to avoid accidental partial writes
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ── Base class
# All our database models (User, Chat, Message, Document) will inherit from this
class Base(DeclarativeBase):
    pass

# ── Dependency for FastAPI routes
# Usage in a route:  db: Session = Depends(get_db)
# This gives the route a db session, and closes it when the request finishes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Test connection utility
def test_connection():
    """Returns True if we can reach the Supabase database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"DB connection failed: {e}")
        return False    