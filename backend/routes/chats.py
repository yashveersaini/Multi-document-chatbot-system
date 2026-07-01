# backend/routes/chats.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.chat import Chat
from backend.models.message import Message
from backend.models.document import Document
from backend.schemas.chat import ChatCreate, ChatRename, ChatResponse, ChatListResponse

router = APIRouter(prefix="/chats", tags=["Chats"])


# ─────────────────────────────────────────────
# GET /chats — list all chats for the logged-in user
# ─────────────────────────────────────────────
@router.get("", response_model=ChatListResponse)
async def list_chats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all chats belonging to the logged-in user,
    newest first, with document and message counts.
    """
    user_id = current_user.get("sub")

    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.updated_at.desc())
        .all()
    )

    # Build response with counts for each chat
    result = []
    for chat in chats:
        doc_count = db.query(func.count(Document.id)).filter(Document.chat_id == chat.id).scalar()
        msg_count = db.query(func.count(Message.id)).filter(Message.chat_id == chat.id).scalar()

        result.append(ChatResponse(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            document_count=doc_count or 0,
            message_count=msg_count or 0,
        ))

    return ChatListResponse(chats=result, total=len(result))


# ─────────────────────────────────────────────
# POST /chats — create a new chat
# ─────────────────────────────────────────────
@router.post("", response_model=ChatResponse, status_code=201)
async def create_chat(
    chat_data: ChatCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new empty chat for the logged-in user.
    Title defaults to "New Chat" — auto-renamed later (Day 7) based on first message.
    """
    user_id = current_user.get("sub")

    new_chat = Chat(
        user_id=user_id,
        title=chat_data.title or "New Chat",
    )

    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    return ChatResponse(
        id=new_chat.id,
        title=new_chat.title,
        created_at=new_chat.created_at,
        updated_at=new_chat.updated_at,
        document_count=0,
        message_count=0,
    )


# ─────────────────────────────────────────────
# GET /chats/{chat_id} — get a single chat's details
# ─────────────────────────────────────────────
@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns details for one chat — only if it belongs to the logged-in user."""
    user_id = current_user.get("sub")

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    doc_count = db.query(func.count(Document.id)).filter(Document.chat_id == chat.id).scalar()
    msg_count = db.query(func.count(Message.id)).filter(Message.chat_id == chat.id).scalar()

    return ChatResponse(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        document_count=doc_count or 0,
        message_count=msg_count or 0,
    )


# ─────────────────────────────────────────────
# PATCH /chats/{chat_id} — rename a chat
# ─────────────────────────────────────────────
@router.patch("/{chat_id}", response_model=ChatResponse)
async def rename_chat(
    chat_id: str,
    rename_data: ChatRename,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Renames a chat — only the owner can rename it."""
    user_id = current_user.get("sub")

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat.title = rename_data.title.strip()
    db.commit()
    db.refresh(chat)

    doc_count = db.query(func.count(Document.id)).filter(Document.chat_id == chat.id).scalar()
    msg_count = db.query(func.count(Message.id)).filter(Message.chat_id == chat.id).scalar()

    return ChatResponse(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        document_count=doc_count or 0,
        message_count=msg_count or 0,
    )


# ─────────────────────────────────────────────
# DELETE /chats/{chat_id} — delete a chat
# ─────────────────────────────────────────────
@router.delete("/{chat_id}", status_code=200)
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes a chat and ALL its messages + documents (cascade delete,
    configured in the Chat model on Day 4).
    Note: this does NOT yet delete the PDF files from Supabase Storage
    or vectors from Pinecone — we handle that on Day 18.
    """
    user_id = current_user.get("sub")

    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(chat)
    db.commit()

    return {"status": "deleted", "chat_id": chat_id}