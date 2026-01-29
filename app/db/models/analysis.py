"""
Analysis 모델
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class AnalysisStatus(enum.Enum):
    """분석 상태"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    ANALYZING = "analyzing"
    GENERATING_REVIEW = "generating_review"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    """코드 분석 작업 모델"""

    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    status = Column(
        Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False
    )
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="analyses")
    repository = relationship("Repository", back_populates="analyses")
    result = relationship("AnalysisResult", back_populates="analysis", uselist=False)

    def __repr__(self):
        return f"<Analysis(id={self.id}, status={self.status.value})>"
