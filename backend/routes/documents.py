from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi import status as http_status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.chat import Chat
from backend.models.document import Document
from backend.schemas.document import DocumentResponse, DocumentListResponse
from backend.services.storage_service import (
    build_storage_path,
    upload_pdf,
    get_signed_url,
    delete_pdf,
)
from backend.config import settings

router = APIRouter(prefix="/chats", tags=["Documents"])

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # convert MB → bytes


# ─────────────────────────────────────────────
# POST /chats/{chat_id}/documents — upload PDFs
# ─────────────────────────────────────────────
@router.post(
    "/{chat_id}/documents",
    response_model=List[DocumentResponse],
    status_code=201,
)
async def upload_documents(
    chat_id: str,
    files: List[UploadFile] = File(..., description="One or more PDF files"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload one or more PDFs to a chat.
    - Validates file type (PDF only) and size (max 50 MB)
    - Uploads each file to Supabase Storage
    - Saves document metadata to the documents table
    - Returns list of created document records
    """
    user_id = current_user.get("sub")

    # Make sure this chat exists and belongs to the logged-in user
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    uploaded_docs = []
    errors        = []

    for file in files:
        try:
            # ── 1. Validate file type
            if file.content_type not in ["application/pdf", "application/x-pdf"]:
                errors.append(f"{file.filename}: Only PDF files are allowed")
                continue

            # ── 2. Read file bytes
            file_bytes = await file.read()

            # ── 3. Validate file size
            file_size = len(file_bytes)
            if file_size == 0:
                errors.append(f"{file.filename}: File is empty")
                continue

            if file_size > MAX_FILE_SIZE:
                errors.append(
                    f"{file.filename}: File too large "
                    f"({round(file_size / 1024 / 1024, 1)} MB). "
                    f"Max is {settings.MAX_FILE_SIZE_MB} MB"
                )
                continue

            # ── 4. Build storage path and upload to Supabase Storage
            storage_path = build_storage_path(user_id, chat_id, file.filename)
            upload_pdf(file_bytes, storage_path)

            # ── 5. Generate signed URL (valid 1 hour — regenerated on demand later)
            try:
                file_url = get_signed_url(storage_path)
            except Exception:
                file_url = None  # non-critical — can regenerate later

            # ── 6. Save document record to Supabase PostgreSQL
            doc = Document(
                chat_id      = chat_id,
                user_id      = user_id,
                filename     = file.filename,
                storage_path = storage_path,
                file_url     = file_url,
                file_size    = file_size,
                page_count   = None,        # filled in on Day 10 after text extraction
                is_processed = False,       # set to True after Pinecone indexing (Day 12)
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            uploaded_docs.append(DocumentResponse(
                id           = doc.id,
                chat_id      = doc.chat_id,
                filename     = doc.filename,
                file_url     = doc.file_url,
                file_size    = doc.file_size,
                page_count   = doc.page_count,
                is_processed = doc.is_processed,
                created_at   = doc.created_at,
            ))

        except Exception as e:
            # Don't let one failed file stop the rest
            errors.append(f"{file.filename}: Upload failed — {str(e)}")
            continue

    # If every file failed, return an error
    if not uploaded_docs and errors:
        raise HTTPException(
            status_code=400,
            detail={"message": "All uploads failed", "errors": errors},
        )

    # If some succeeded and some failed — return what worked + log errors
    if errors:
        print(f"[Upload] Partial errors for chat {chat_id}: {errors}")

    return uploaded_docs


# ─────────────────────────────────────────────
# GET /chats/{chat_id}/documents — list documents
# ─────────────────────────────────────────────
@router.get("/{chat_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all documents uploaded to a specific chat."""
    user_id = current_user.get("sub")

    # Verify chat ownership
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    documents = (
        db.query(Document)
        .filter(Document.chat_id == chat_id)
        .order_by(Document.created_at.desc())
        .all()
    )

    result = []
    for doc in documents:
        # Refresh signed URL (they expire after 1 hour)
        try:
            fresh_url = get_signed_url(doc.storage_path)
        except Exception:
            fresh_url = doc.file_url  # fallback to stored URL

        result.append(DocumentResponse(
            id           = doc.id,
            chat_id      = doc.chat_id,
            filename     = doc.filename,
            file_url     = fresh_url,
            file_size    = doc.file_size,
            page_count   = doc.page_count,
            is_processed = doc.is_processed,
            created_at   = doc.created_at,
        ))

    return DocumentListResponse(documents=result, total=len(result))


# ─────────────────────────────────────────────
# DELETE /chats/{chat_id}/documents/{doc_id}
# ─────────────────────────────────────────────
@router.delete("/{chat_id}/documents/{doc_id}", status_code=200)
async def delete_document(
    chat_id: str,
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a single document — removes it from both
    Supabase Storage and the documents table.
    Note: Pinecone vector cleanup happens on Day 18.
    """
    user_id = current_user.get("sub")

    # Verify chat ownership
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Find the document
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.chat_id == chat_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from Supabase Storage
    delete_pdf(doc.storage_path)

    # Delete from database
    db.delete(doc)
    db.commit()

    return {"status": "deleted", "document_id": doc_id}