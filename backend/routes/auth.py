# backend/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/sync")
async def sync_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Syncs the logged-in Clerk user to our Supabase users table.
    - Called automatically by auth.js right after login
    - Creates a new user row if first time logging in
    - Updates name/email if they changed it in Clerk
    """
    clerk_user_id = current_user.get("sub")
    email         = current_user.get("email", "")
    first_name    = current_user.get("first_name", "")
    last_name     = current_user.get("last_name", "")

    if not clerk_user_id:
        raise HTTPException(status_code=400, detail="Invalid token: missing user ID")

    # Check if user already exists in our database
    existing_user = db.query(User).filter(User.id == clerk_user_id).first()

    if existing_user:
        # Update their info in case they changed name/email in Clerk
        existing_user.email      = email
        existing_user.first_name = first_name
        existing_user.last_name  = last_name
        db.commit()
        db.refresh(existing_user)

        return {
            "status": "updated",
            "user_id": existing_user.id,
            "email": existing_user.email,
        }
    else:
        # First login — create a new user row
        new_user = User(
            id         = clerk_user_id,
            email      = email,
            first_name = first_name,
            last_name  = last_name,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "status": "created",
            "user_id": new_user.id,
            "email": new_user.email,
        }


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current logged-in user's info from our database.
    Useful for the frontend to fetch user details.
    """
    clerk_user_id = current_user.get("sub")

    user = db.query(User).filter(User.id == clerk_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found. Try logging out and back in.")

    return {
        "id":         user.id,
        "email":      user.email,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "created_at": user.created_at,
    }