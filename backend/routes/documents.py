# backend/routes/documents.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post(
    "/{chat_id}/documents",
    response_model=List[DocumentResponse],
    status_code=201,
)
async def upload_documents(
    chat_id: str,
    # ✅ FIX — use File(...) correctly for multiple files
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("sub")

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    uploaded_docs = []
    errors        = []

    for file in files:
        try:
            # ✅ FIX — check filename extension too, not just content_type
            # Browsers sometimes send "application/octet-stream" for PDFs
            filename_lower = (file.filename or "").lower()
            content_type   = file.content_type or ""

            is_pdf = (
                content_type in ["application/pdf", "application/x-pdf"]
                or filename_lower.endswith(".pdf")
            )

            if not is_pdf:
                errors.append(f"{file.filename}: Only PDF files are allowed")
                continue

            file_bytes = await file.read()
            file_size  = len(file_bytes)

            if file_size == 0:
                errors.append(f"{file.filename}: File is empty")
                continue

            if file_size > MAX_FILE_SIZE:
                errors.append(
                    f"{file.filename}: Too large "
                    f"({round(file_size/1024/1024, 1)} MB). "
                    f"Max {settings.MAX_FILE_SIZE_MB} MB"
                )
                continue

            storage_path = build_storage_path(user_id, chat_id, file.filename)
            upload_pdf(file_bytes, storage_path)

            try:
                file_url = get_signed_url(storage_path)
            except Exception:
                file_url = None

            doc = Document(
                chat_id      = chat_id,
                user_id      = user_id,
                filename     = file.filename,
                storage_path = storage_path,
                file_url     = file_url,
                file_size    = file_size,
                page_count   = None,
                is_processed = False,
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
            print(f"[UPLOAD ERROR] {file.filename}: {str(e)}")
            errors.append(f"{file.filename}: {str(e)}")
            continue

    if not uploaded_docs and errors:
        raise HTTPException(
            status_code=400,
            detail={"message": "All uploads failed", "errors": errors},
        )

    return uploaded_docs


@router.get("/{chat_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("sub")

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
        try:
            fresh_url = get_signed_url(doc.storage_path)
        except Exception:
            fresh_url = doc.file_url

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


@router.delete("/{chat_id}/documents/{doc_id}", status_code=200)
async def delete_document(
    chat_id: str,
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("sub")

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.chat_id == chat_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_pdf(doc.storage_path)
    db.delete(doc)
    db.commit()

    return {"status": "deleted", "document_id": doc_id}