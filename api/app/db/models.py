"""
Database models for the API server.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

def generate_uuid():
    """Generate a UUID."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=generate_uuid, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("AnalysisTask", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")


class AnalysisTask(Base):
    """Analysis task model for tracking repository analysis jobs."""
    
    __tablename__ = "analysis_tasks"
    
    id = Column(UUID, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_url = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, in_progress, completed, failed
    options = Column(JSON, nullable=False, default={})  # Store analysis options like model, temperature, etc.
    progress = Column(Integer, default=0)  # 0-100 percent
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    report = relationship("Report", back_populates="task", uselist=False, cascade="all, delete-orphan")


class Report(Base):
    """Report model for storing analysis results."""
    
    __tablename__ = "reports"
    
    id = Column(UUID, primary_key=True, default=generate_uuid, index=True)
    task_id = Column(UUID, ForeignKey("analysis_tasks.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_url = Column(Text, nullable=False)
    repo_name = Column(Text, nullable=False)
    content = Column(JSON, nullable=False)  # Store full report content as JSON
    scores = Column(JSON, nullable=True)  # Store extracted scores for quick access
    ipfs_hash = Column(Text, nullable=True)  # IPFS Content ID where report is stored
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)  # When report was published to IPFS
    
    # Relationships
    user = relationship("User", back_populates="reports")
    task = relationship("AnalysisTask", back_populates="report")


class ApiKey(Base):
    """API key model for authentication."""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")