import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    # Which chat this PDF belongs to
    chat_id = Column(String, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)

    # Which user uploaded it
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Original filename e.g. "research_paper.pdf"
    filename = Column(String, nullable=False)

    # Path inside Supabase Storage bucket
    # e.g. "user_2abc123/chat_550e84.../research_paper.pdf"
    storage_path = Column(String, nullable=False)

    # Public or signed URL to access the file in Supabase Storage
    file_url = Column(String, nullable=True)

    # File size in bytes (BigInteger supports files > 2GB just in case)
    file_size = Column(BigInteger, nullable=True)

    # Number of pages extracted from the PDF (set on Day 10)
    page_count = Column(Integer, nullable=True)

    # Has this PDF been chunked, embedded, and stored in Pinecone?
    # Starts as False — set to True after Day 12 processing
    is_processed = Column(Boolean, default=False, nullable=False)

    # If processing failed, we store the error message here
    processing_error = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship back to chat
    chat = relationship("Chat", back_populates="documents")

    def __repr__(self):
        return f"<Document id={self.id} filename={self.filename} processed={self.is_processed}>"