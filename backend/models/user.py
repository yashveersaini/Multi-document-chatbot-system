from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    # Clerk gives every user a unique ID like "user_2abc123"
    # We use that as our primary key — no need to generate our own
    id = Column(String, primary_key=True, index=True)

    email = Column(String, unique=True, nullable=False, index=True)

    # first_name / last_name come from Clerk profile
    first_name = Column(String, nullable=True)
    last_name  = Column(String, nullable=True)

    # Timestamps — func.now() lets the database set the time automatically
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships — "one user has many chats"
    # cascade="all, delete-orphan" means: if user is deleted, delete their chats too
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"