# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import test_connection

# ── Create the FastAPI app
app = FastAPI(
    title="RAG PDF Chatbot API",
    description="Backend API for the RAG PDF Chatbot",
    version="1.0.0",
)

# ── CORS Middleware
# This allows your HTML frontend (running on a different port/file)
# to make requests to this FastAPI backend without getting blocked.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────
# ROUTES
# ────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    """Root endpoint — just confirms the API is alive."""
    return {
        "message": "RAG PDF Chatbot API is running 🚀",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    Returns the status of the API and the database connection.
    """
    db_ok = test_connection()

    return {
        "status": "ok" if db_ok else "degraded",
        "api": "ok",
        "database": "connected" if db_ok else "unreachable",
        "supabase_url": settings.SUPABASE_URL or "not set",
    }


@app.get("/health/env", tags=["Health"])
def env_check():
    """
    Shows which environment variables are set (not their values — safe to call).
    Useful for debugging during development.
    """
    def is_set(val: str) -> str:
        return "✅ set" if val else "❌ missing"

    return {
        "DATABASE_URL":            is_set(settings.DATABASE_URL),
        "SUPABASE_URL":            is_set(settings.SUPABASE_URL),
        "SUPABASE_ANON_KEY":       is_set(settings.SUPABASE_ANON_KEY),
        "SUPABASE_SERVICE_ROLE_KEY": is_set(settings.SUPABASE_SERVICE_ROLE_KEY),
        "CLERK_SECRET_KEY":        is_set(settings.CLERK_SECRET_KEY),
        "OPENAI_API_KEY":          is_set(settings.OPENAI_API_KEY),
        "GOOGLE_API_KEY":          is_set(settings.GOOGLE_API_KEY),
        "PINECONE_API_KEY":        is_set(settings.PINECONE_API_KEY),
    }