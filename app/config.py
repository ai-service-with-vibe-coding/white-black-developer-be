"""
애플리케이션 설정
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """환경 변수 기반 설정"""

    # ===== MVP 필수 설정 =====

    # App
    APP_NAME: str = "White-Black Developer"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # AI 모델 설정 (로컬 GPU 실행)
    CODE_REVIEWER_MODEL: str = "microsoft/codereviewer"
    VULNERABILITY_DETECTOR_MODEL: str = "mahdin70/codebert-devign-code-vulnerability-detector"
    # 10.7B 모델 (VRAM 12GB+ 필요)
    # PERSONA_MODEL: str = "beomi/OPEN-SOLAR-KO-10.7B"
    # 7B 모델 (VRAM 8GB로 가능)
    PERSONA_MODEL: str = "beomi/Llama-3-Open-Ko-8B-Instruct-preview"

    # 모델 캐시 디렉토리
    HF_HOME: str = "./model_cache"
    TRANSFORMERS_CACHE: str = "./model_cache"

    # GPU 설정
    CUDA_VISIBLE_DEVICES: str = "0"

    # ===== 전체 기능용 설정 (MVP에서는 선택사항) =====

    # Database (MVP에서는 사용 안함)
    DATABASE_URL: Optional[str] = None

    # Redis (MVP에서는 사용 안함)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery (MVP에서는 사용 안함)
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # GitHub OAuth (MVP에서는 사용 안함)
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_CALLBACK_URL: Optional[str] = None

    # JWT (MVP에서는 사용 안함)
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 168  # 7 days

    # Encryption (MVP에서는 사용 안함)
    ENCRYPTION_KEY: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_WINDOW_MS: int = 900000
    RATE_LIMIT_MAX_REQUESTS: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤"""
    return Settings()


settings = get_settings()
