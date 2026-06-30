# backend/dependencies.py
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from backend.config import settings

# HTTPBearer reads the "Authorization: Bearer <token>" header automatically
security = HTTPBearer()

# We cache Clerk's public keys so we don't fetch them on every request
_clerk_jwks_cache: dict = {}

async def get_clerk_public_keys() -> dict:
    """
    Fetch Clerk's public JSON Web Key Set (JWKS).
    These keys are used to verify that a JWT token was really signed by Clerk.
    We cache them after the first fetch.
    """
    global _clerk_jwks_cache

    if _clerk_jwks_cache:
        return _clerk_jwks_cache

    # Clerk exposes public keys at this URL
    jwks_url = f"{settings.SUPABASE_URL}/../.well-known/jwks.json"

    # Better: use Clerk's own JWKS endpoint
    clerk_jwks_url = f"https://api.clerk.com/v1/jwks"

    try:
        async with httpx.AsyncClient() as client:
            # Use your Clerk Frontend API URL
            # Format: https://<your-clerk-domain>/.well-known/jwks.json
            frontend_api = settings.CLERK_PUBLISHABLE_KEY.replace("pk_test_", "").replace("pk_live_", "")
            # Decode the base64 frontend API URL
            import base64
            try:
                decoded = base64.b64decode(frontend_api + "==").decode("utf-8").rstrip("$")
                jwks_url = f"https://{decoded}/.well-known/jwks.json"
            except Exception:
                jwks_url = clerk_jwks_url

            response = await client.get(jwks_url, timeout=10)
            response.raise_for_status()
            _clerk_jwks_cache = response.json()
            return _clerk_jwks_cache
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not fetch Clerk public keys: {str(e)}"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency — verifies the JWT token from the Authorization header.

    Usage in any route:
        @app.get("/protected")
        async def my_route(user = Depends(get_current_user)):
            return {"user_id": user["sub"]}

    Returns a dict with the user's Clerk info:
        {
          "sub": "user_2abc123",       ← Clerk user ID
          "email": "user@example.com",
          "first_name": "John",
          ...
        }
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        # Get Clerk's public keys
        jwks = await get_clerk_public_keys()

        # Decode the JWT header to find which key was used (kid = key ID)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find the matching public key from Clerk's JWKS
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "n":   key["n"],
                    "e":   key["e"],
                }
                break

        if not rsa_key:
            raise credentials_exception

        # Verify the token signature and decode the payload
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk doesn't use audience claims by default
        )

        # Extract the Clerk user ID (stored in "sub" claim)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception

        return payload  # Contains sub, email, name, etc.

    except JWTError:
        raise credentials_exception