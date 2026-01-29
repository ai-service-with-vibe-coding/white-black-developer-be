"""
FastAPI 메인 애플리케이션
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import logging

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 애플리케이션 라이프사이클 관리
    - 시작: GPU 확인 및 AI 모델 프리로딩
    - 종료: GPU 메모리 해제
    """
    # ========== 시작 (Startup) ==========
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # GPU 확인
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"GPU detected: {gpu_name}")
            logger.info(f"Total VRAM: {total_vram:.2f}GB")

            # AI 모델 프리로딩
            logger.info("=" * 60)
            logger.info("Preloading AI models...")
            try:
                from app.ai.huggingface_client import get_hf_client

                hf_client = get_hf_client()

                # 모델 순차 로딩 (VRAM 효율)
                logger.info("[1/3] Loading Code Reviewer...")
                hf_client.get_code_reviewer()

                logger.info("[2/3] Loading Vulnerability Detector...")
                hf_client.get_vulnerability_detector()

                logger.info("[3/3] Loading Persona LLM...")
                hf_client.get_persona_llm()

                # 최종 메모리 사용량
                vram_used = torch.cuda.memory_allocated() / 1024**3
                vram_reserved = torch.cuda.memory_reserved() / 1024**3
                logger.info("=" * 60)
                logger.info(f"All models loaded successfully!")
                logger.info(f"VRAM allocated: {vram_used:.2f}GB")
                logger.info(f"VRAM reserved: {vram_reserved:.2f}GB")
                logger.info("=" * 60)

            except Exception as e:
                logger.error(f"Failed to preload models: {e}")
                logger.warning("Models will be loaded on first request (slower)")

        else:
            logger.warning("GPU not available! Models will run on CPU (very slow)")

    except ImportError:
        logger.warning("PyTorch not installed")

    logger.info(f"{settings.APP_NAME} is ready!")
    logger.info("=" * 60)

    # ========== 애플리케이션 실행 ==========
    yield

    # ========== 종료 (Shutdown) ==========
    logger.info("=" * 60)
    logger.info(f"Shutting down {settings.APP_NAME}...")

    # GPU 메모리 해제
    try:
        import torch

        if torch.cuda.is_available():
            # 모델 참조 해제
            from app.ai.huggingface_client import _hf_client_instance
            if _hf_client_instance is not None:
                _hf_client_instance._models.clear()
                _hf_client_instance.clear_cache()

            # GPU 캐시 클리어
            torch.cuda.empty_cache()
            logger.info("GPU memory cleared")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

    logger.info("Shutdown complete")
    logger.info("=" * 60)


# FastAPI 앱 생성 (lifespan 사용)
app = FastAPI(
    title=settings.APP_NAME,
    description="AI 기반 개발자 실력 평가 플랫폼",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],  # 프로덕션에서는 특정 도메인만
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "흑백개발자 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "ok"}


@app.get("/gpu/status")
async def gpu_status():
    """GPU 상태 확인"""
    try:
        import torch

        if not torch.cuda.is_available():
            return {"error": "GPU not available"}

        return {
            "device_name": torch.cuda.get_device_name(0),
            "device_count": torch.cuda.device_count(),
            "memory_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.2f}GB",
            "memory_reserved": f"{torch.cuda.memory_reserved() / 1024**3:.2f}GB",
            "memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}GB",
        }
    except Exception as e:
        return {"error": str(e)}


# API 라우터 등록
from app.api.v1 import analysis
app.include_router(analysis.router, prefix="/api/v1")
