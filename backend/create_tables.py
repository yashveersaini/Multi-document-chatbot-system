import sys
import os

# Make sure Python can find the backend/ package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, engine, test_connection

# Import ALL models so SQLAlchemy knows about them before creating tables
# If you skip this, the tables won't be created
from backend.models import User, Chat, Message, Document

def create_all_tables():
    print("\n🔌 Testing database connection...")

    if not test_connection():
        print("❌ Cannot connect to Supabase. Check your DATABASE_URL in .env")
        sys.exit(1)

    print("✅ Connected to Supabase PostgreSQL\n")
    print("📦 Creating tables...")

    # This reads all models that inherit from Base and creates their tables
    # checkfirst=True means: skip if the table already exists (safe to re-run)
    Base.metadata.create_all(bind=engine, checkfirst=True)

    print("\n✅ Tables created successfully:")
    print("   → users")
    print("   → chats")
    print("   → messages")
    print("   → documents")
    print("\n🎉 Done! Check your Supabase dashboard → Table Editor to see them.")

if __name__ == "__main__":
    create_all_tables()