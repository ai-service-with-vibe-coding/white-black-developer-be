"""
AnalysisResult 모델
"""
from sqlalchemy import Column, String, Integer, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class AnalysisResult(Base):
    """분석 결과 모델"""

    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(
        String, ForeignKey("analyses.id"), unique=True, nullable=False, index=True
    )
    level = Column(Integer, nullable=False)  # 1-5
    overall_score = Column(Float, nullable=False)
    security_score = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    complexity_score = Column(Float, nullable=False)
    documentation_score = Column(Float, nullable=False)
    best_practices_score = Column(Float, nullable=False)
    review_text = Column(Text, nullable=False)  # 안성재 쉐프 리뷰
    details = Column(JSON, nullable=True)  # 상세 분석 결과
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="result")

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, level={self.level})>"
