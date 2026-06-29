# backend/config.py
from dotenv import load_dotenv
import os

# Load .env file from the project root (one level above backend/)
load_dotenv()

class Settings:
    # ── Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ── Supabase
    SUPABASE_URL: str            = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str       = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # ── Clerk
    CLERK_SECRET_KEY: str      = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_PUBLISHABLE_KEY: str = os.getenv("CLERK_PUBLISHABLE_KEY", "")

    # ── OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ── Google Gemini
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # ── Pinecone
    PINECONE_API_KEY: str    = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rag-chatbot")

    # ── App
    UPLOAD_DIR: str      = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))

# Single instance imported everywhere
settings = Settings()