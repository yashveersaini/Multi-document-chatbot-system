from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentResponse(BaseModel):
    """What we return to the frontend after a successful upload."""
    id: str
    chat_id: str
    filename: str
    file_url: Optional[str]
    file_size: Optional[int]
    page_count: Optional[int]
    is_processed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents for a chat."""
    documents: list[DocumentResponse]
    total: int