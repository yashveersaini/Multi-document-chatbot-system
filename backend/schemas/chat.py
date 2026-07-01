# backend/schemas/chat.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ChatCreate(BaseModel):
    """What the frontend sends when creating a new chat."""
    title: Optional[str] = Field(default="New Chat", max_length=100)


class ChatRename(BaseModel):
    """What the frontend sends when renaming a chat."""
    title: str = Field(min_length=1, max_length=100)


class ChatResponse(BaseModel):
    """What we send back to the frontend for a single chat."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0   # filled in manually in the route
    message_count: int = 0    # filled in manually in the route

    class Config:
        from_attributes = True  # allows reading directly from SQLAlchemy objects


class ChatListResponse(BaseModel):
    """What we send back when listing all chats."""
    chats: list[ChatResponse]
    total: int