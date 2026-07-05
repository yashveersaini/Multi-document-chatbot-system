from supabase import create_client, Client
from backend.config import settings
import uuid
import os

# ── Supabase client using Service Role key
# Service Role bypasses Row Level Security — safe to use only on the backend
def get_supabase() -> Client:
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )

BUCKET_NAME = "pdfs"


def build_storage_path(user_id: str, chat_id: str, filename: str) -> str:
    """
    Build a unique path for the file inside the bucket.
    Format: user_id/chat_id/uuid_filename.pdf
    Example: user_2abc/550e84.../a1b2c3_report.pdf

    Using user_id/chat_id as folders keeps files organized
    and makes it easy to delete all files for a chat.
    """
    # Sanitize filename — remove spaces and special chars
    safe_filename = filename.replace(" ", "_").replace("/", "_")
    unique_prefix = str(uuid.uuid4())[:8]
    return f"{user_id}/{chat_id}/{unique_prefix}_{safe_filename}"


def upload_pdf(file_bytes: bytes, storage_path: str) -> str:
    """
    Upload a PDF to Supabase Storage.
    Returns the storage path on success.
    Raises an exception if upload fails.
    """
    supabase = get_supabase()

    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf"},
        )
        return storage_path

    except Exception as e:
        error_msg = str(e)
        # If file already exists (shouldn't happen with UUID prefix, but just in case)
        if "already exists" in error_msg.lower():
            raise ValueError(f"File already exists at path: {storage_path}")
        raise Exception(f"Supabase Storage upload failed: {error_msg}")


def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a temporary signed URL to access a private file.
    expires_in = seconds until the URL expires (default 1 hour).
    The frontend uses this URL to display the PDF or download it.
    """
    supabase = get_supabase()

    try:
        response = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            path=storage_path,
            expires_in=expires_in,
        )
        return response.get("signedURL") or response.get("signedUrl", "")

    except Exception as e:
        raise Exception(f"Failed to generate signed URL: {str(e)}")


def delete_pdf(storage_path: str) -> bool:
    """
    Delete a PDF from Supabase Storage.
    Returns True if deleted, False if file not found.
    Used on Day 18 when user removes a document.
    """
    supabase = get_supabase()

    try:
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        return True
    except Exception as e:
        print(f"Storage delete warning: {str(e)}")
        return False


def delete_all_pdfs_for_chat(user_id: str, chat_id: str) -> bool:
    """
    Delete all PDFs for a specific chat from Supabase Storage.
    Used on Day 18 when user deletes a chat entirely.
    """
    supabase = get_supabase()

    try:
        # List all files in the chat's folder
        folder_path = f"{user_id}/{chat_id}"
        files = supabase.storage.from_(BUCKET_NAME).list(folder_path)

        if not files:
            return True

        # Build full paths and delete all at once
        paths_to_delete = [f"{folder_path}/{f['name']}" for f in files]
        supabase.storage.from_(BUCKET_NAME).remove(paths_to_delete)
        return True

    except Exception as e:
        print(f"Bulk storage delete warning: {str(e)}")
        return False