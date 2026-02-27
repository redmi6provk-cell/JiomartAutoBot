"""
SQLAlchemy models for storing JioMart profile data.
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Profile(Base):
    """
    Profile model - stores metadata for each browser profile.
    """
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    profile_number = Column(Integer, unique=True, nullable=False, index=True)
    profile_name = Column(Text, nullable=True)  # e.g., "Profile 1"
    extraction_time = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cookies = relationship("Cookie", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Profile(id={self.id}, number={self.profile_number}, name='{self.profile_name}')>"


class Cookie(Base):
    """
    Cookie model - stores browser cookies as JSON for each profile.
    """
    __tablename__ = "cookies"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    
    # Store entire cookie data as JSON
    cookies = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    profile = relationship("Profile", back_populates="cookies")

    def __repr__(self):
        return f"<Cookie(profile_id={self.profile_id})>"
