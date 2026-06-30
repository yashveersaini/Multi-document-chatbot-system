# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import test_connection

# Import routers
from backend.routes.auth import router as auth_router

# ── App
app = FastAPI(
    title="RAG PDF Chatbot API",
    description="Backend API for the RAG PDF Chatbot",
    version="1.0.0",
)

# ── CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers
app.include_router(auth_router)

# ── Routes
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "RAG PDF Chatbot API is running 🚀",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    db_ok = test_connection()
    return {
        "status":   "ok" if db_ok else "degraded",
        "api":      "ok",
        "database": "connected" if db_ok else "unreachable",
    }


@app.get("/health/env", tags=["Health"])
def env_check():
    def is_set(val: str) -> str:
        return "✅ set" if val else "❌ missing"
    return {
        "DATABASE_URL":              is_set(settings.DATABASE_URL),
        "SUPABASE_URL":              is_set(settings.SUPABASE_URL),
        "SUPABASE_ANON_KEY":         is_set(settings.SUPABASE_ANON_KEY),
        "SUPABASE_SERVICE_ROLE_KEY": is_set(settings.SUPABASE_SERVICE_ROLE_KEY),
        "CLERK_SECRET_KEY":          is_set(settings.CLERK_SECRET_KEY),
        "CLERK_PUBLISHABLE_KEY":     is_set(settings.CLERK_PUBLISHABLE_KEY),
        "OPENAI_API_KEY":            is_set(settings.OPENAI_API_KEY),
        "GOOGLE_API_KEY":            is_set(settings.GOOGLE_API_KEY),
        "PINECONE_API_KEY":          is_set(settings.PINECONE_API_KEY),
    }