import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class Chat(Base):
    __tablename__ = "chats"

    # We generate a UUID for each chat — it's a random unique ID like
    # "550e8400-e29b-41d4-a716-446655440000"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    # Which user owns this chat
    # ForeignKey links to users.id — if user is deleted, chat is deleted too (CASCADE)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Chat title — e.g. "Research Paper Q&A"
    # Auto-title generation happens on Day 7 via the AI
    title = Column(String, nullable=False, default="New Chat")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user      = relationship("User", back_populates="chats")
    messages  = relationship("Message",  back_populates="chat", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="chat", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chat id={self.id} title={self.title}>"