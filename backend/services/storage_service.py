import uuid
import httpx
from backend.config import settings

BUCKET_NAME = "pdfs"


def _base_url() -> str:
    """Always strip trailing slash to prevent double-slash in URLs."""
    return settings.SUPABASE_URL.rstrip("/")


def _storage_url(storage_path: str) -> str:
    return f"{_base_url()}/storage/v1/object/{BUCKET_NAME}/{storage_path}"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
    }


def build_storage_path(user_id: str, chat_id: str, filename: str) -> str:
    """
    Build a unique file path inside the bucket.
    Format: user_id/chat_id/uuid_filename.pdf
    """
    safe_name     = filename.replace(" ", "_").replace("/", "_")
    unique_prefix = str(uuid.uuid4())[:8]
    return f"{user_id}/{chat_id}/{unique_prefix}_{safe_name}"


def upload_pdf(file_bytes: bytes, storage_path: str) -> str:
    """
    Upload PDF bytes directly via Supabase Storage REST API.
    Bypasses supabase-py storage client to avoid version bugs.
    """
    url = _storage_url(storage_path)

    # Debug — remove after confirming upload works
    print(f"[DEBUG] Upload URL : {url}")
    print(f"[DEBUG] Path       : {storage_path}")
    print(f"[DEBUG] Size       : {len(file_bytes)} bytes")

    headers = {
        **_headers(),
        "Content-Type": "application/pdf",
        "x-upsert":     "false",
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, content=file_bytes, headers=headers)

    print(f"[DEBUG] Response   : {response.status_code} — {response.text[:200]}")

    if response.status_code in (200, 201):
        return storage_path

    try:
        error_body = response.json()
        error_msg  = (
            error_body.get("message")
            or error_body.get("error")
            or str(error_body)
        )
    except Exception:
        error_msg = response.text or f"HTTP {response.status_code}"

    raise Exception(f"Storage upload failed ({response.status_code}): {error_msg}")


def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a signed URL for a private file.
    Returns empty string on failure — non-critical.
    """
    url = f"{_base_url()}/storage/v1/object/sign/{BUCKET_NAME}/{storage_path}"

    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            url,
            json={"expiresIn": expires_in},
            headers={**_headers(), "Content-Type": "application/json"},
        )

    if response.status_code == 200:
        data       = response.json()
        signed_url = data.get("signedURL") or data.get("signedUrl") or ""
        # Some Supabase versions return a relative path — make it absolute
        if signed_url and not signed_url.startswith("http"):
            signed_url = f"{_base_url()}/storage/v1{signed_url}"
        return signed_url

    print(f"[WARN] Signed URL failed ({response.status_code}): {response.text}")
    return ""


def delete_pdf(storage_path: str) -> bool:
    """Delete a single PDF from Supabase Storage."""
    url = f"{_base_url()}/storage/v1/object/remove/{BUCKET_NAME}"

    headers = {
        **_headers(),
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            url,
            json={"prefixes": [storage_path]},
            headers=headers,
        )

    print(f"[DELETE] URL: {url}")
    print(f"[DELETE] Path: {storage_path}")
    print(f"[DELETE] Status: {response.status_code}")
    print(f"[DELETE] Body: {response.text}")

    return response.status_code == 200


def delete_all_pdfs_for_chat(user_id: str, chat_id: str) -> bool:
    """Delete all PDFs for a chat folder."""
    folder   = f"{user_id}/{chat_id}"
    list_url = f"{_base_url()}/storage/v1/object/list/{BUCKET_NAME}"

    with httpx.Client(timeout=10.0) as client:
        list_resp = client.post(
            list_url,
            json={"prefix": folder, "limit": 100, "offset": 0},
            headers={**_headers(), "Content-Type": "application/json"},
        )

    if list_resp.status_code != 200:
        print(f"[WARN] List failed: {list_resp.text}")
        return False

    files = list_resp.json()
    if not files:
        return True

    paths      = [f"{folder}/{f['name']}" for f in files if f.get("name")]
    delete_url = f"{_base_url()}/storage/v1/object/remove/{BUCKET_NAME}"

    with httpx.Client(timeout=10.0) as client:
        del_resp = client.post(
            delete_url,
            json={"prefixes": paths},
            headers={**_headers(), "Content-Type": "application/json"},
        )

        print(f"[DELETE ALL] {del_resp.status_code}: {del_resp.text}")

    return del_resp.status_code in (200, 204)