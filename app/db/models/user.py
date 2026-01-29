"""
User 모델
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    github_id = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    access_token = Column(Text, nullable=False)  # 암호화 저장
    refresh_token = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    analyses = relationship("Analysis", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
