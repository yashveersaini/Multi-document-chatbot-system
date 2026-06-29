from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

# ── Engine
# pool_pre_ping=True : pings the DB before each use — handles Supabase idle timeouts
# pool_size=5        : max 5 permanent connections (safe for free tier's 60 limit)
# max_overflow=10    : up to 10 extra connections during spikes, then closed
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# ── Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ── Base class — all models inherit from this
class Base(DeclarativeBase):
    pass

# ── FastAPI dependency
# Add  db: Session = Depends(get_db)  to any route to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Connection test utility (used in main.py and create_tables.py)
def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"DB connection error: {e}")
        return False