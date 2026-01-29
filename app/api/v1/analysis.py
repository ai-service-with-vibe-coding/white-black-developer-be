"""
코드 분석 API (MVP)
"""
from fastapi import APIRouter, HTTPException
from app.schemas.analysis import (
    CodeAnalysisRequest,
    CodeAnalysisResponse,
    ScoreDetail,
    HealthResponse,
    ErrorResponse,
)
from app.services.code_analysis_service import get_code_analysis_service
from app.ai.huggingface_client import get_hf_client
from app.utils.gpu_utils import get_gpu_memory_info
from app.utils.logger import get_logger
import torch

logger = get_logger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=CodeAnalysisResponse,
    responses={
        500: {"model": ErrorResponse, "description": "서버 에러"},
    },
    summary="코드 분석",
    description="코드를 분석하고 안성재 쉐프 스타일의 리뷰를 생성합니다.",
)
async def analyze_code(request: CodeAnalysisRequest):
    """
    코드 분석 API

    - **code**: 분석할 코드 문자열
    - **language**: 프로그래밍 언어 (auto: 자동 감지)
    - **include_persona_review**: 페르소나 리뷰 포함 여부
    """
    try:
        logger.info(f"Analysis request received. Code length: {len(request.code)}")

        service = get_code_analysis_service()

        result = service.analyze(
            code=request.code,
            language=request.language.value,
            include_persona_review=request.include_persona_review,
        )

        return CodeAnalysisResponse(
            level=result.level,
            level_title=result.level_title,
            verdict=result.verdict,
            overall_score=round(result.overall_score, 2),
            scores=ScoreDetail(
                security=round(result.security_score, 2),
                quality=round(result.quality_score, 2),
                best_practices=round(result.best_practices_score, 2),
                complexity=round(result.complexity_score, 2),
                documentation=round(result.documentation_score, 2),
            ),
            code_review=result.code_review,
            persona_review=result.persona_review if request.include_persona_review else None,
            is_vulnerable=result.is_vulnerable,
            vulnerability_score=round(result.vulnerability_score, 2),
            issues=result.issues,
            suggestions=result.suggestions,
            language=result.language,
            line_count=result.line_count,
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.post(
    "/quick",
    response_model=CodeAnalysisResponse,
    summary="빠른 분석 (페르소나 리뷰 없음)",
    description="페르소나 리뷰 없이 빠르게 코드를 분석합니다.",
)
async def quick_analyze(request: CodeAnalysisRequest):
    """빠른 분석 (페르소나 리뷰 생략)"""
    request.include_persona_review = False
    return await analyze_code(request)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="헬스 체크",
    description="서버 상태 및 GPU 정보를 확인합니다.",
)
async def health_check():
    """헬스 체크"""
    gpu_available = torch.cuda.is_available()
    gpu_name = None
    gpu_memory = None
    models_loaded = []

    if gpu_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = get_gpu_memory_info()

    try:
        client = get_hf_client()
        models_loaded = client.get_loaded_models()
    except Exception:
        pass

    return HealthResponse(
        status="ok" if gpu_available else "degraded",
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        gpu_memory=gpu_memory,
        models_loaded=models_loaded,
    )


@router.post(
    "/preload",
    summary="모델 사전 로드",
    description="모든 AI 모델을 미리 로드합니다. 첫 요청의 지연을 줄입니다.",
)
async def preload_models():
    """모델 사전 로드"""
    try:
        client = get_hf_client()
        client.preload_all_models()

        return {
            "status": "ok",
            "message": "모든 모델이 로드되었습니다",
            "models_loaded": client.get_loaded_models(),
            "gpu_memory": get_gpu_memory_info(),
        }

    except Exception as e:
        logger.error(f"Model preload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"모델 로드 실패: {str(e)}"
        )
