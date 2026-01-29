"""
로깅 유틸리티
"""
import logging
from app.config import settings

# 로거 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    """로거 가져오기"""
    return logging.getLogger(name)
