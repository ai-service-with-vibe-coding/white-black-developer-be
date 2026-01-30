"""
코드 분석 API (MVP)
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.analysis import (
    CodeAnalysisRequest,
    CodeAnalysisResponse,
    ScoreDetail,
    HealthResponse,
    ErrorResponse,
)
from app.services.code_analysis_service import get_code_analysis_service
from app.ai.huggingface_client import get_hf_client
from app.ai.prompts.chef_ahn import CHEF_AHN_SYSTEM_PROMPT, build_review_prompt
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
    summary="모델 수동 로드",
    description="AI 모델을 수동으로 로드합니다. 서버 시작 시 자동 로드되지만, 실패 시 이 API로 재시도할 수 있습니다.",
)
async def preload_models():
    """모델 수동 로드 (자동 로드 실패 시 재시도용)"""
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


@router.post(
    "/analyze/stream",
    summary="코드 분석 (스트리밍)",
    description="""
    코드 분석 결과를 SSE(Server-Sent Events)로 스트리밍합니다.

    **이벤트 타입:**
    - `analysis`: 코드 분석 결과 (점수, 리뷰 등) - 즉시 전송
    - `persona_token`: 페르소나 리뷰 토큰 - 실시간 스트리밍
    - `persona_done`: 페르소나 리뷰 완료
    - `error`: 에러 발생
    - `done`: 모든 처리 완료
    """,
)
async def analyze_code_stream(request: CodeAnalysisRequest):
    """
    코드 분석 스트리밍 API

    SSE 형식으로 결과를 실시간 전송합니다.
    코드 분석 결과는 즉시 전송되고, 페르소나 리뷰는 토큰 단위로 스트리밍됩니다.
    """

    def generate_sse():
        try:
            logger.info(f"Stream analysis request. Code length: {len(request.code)}")

            # 1단계: 코드 분석 (페르소나 제외)
            service = get_code_analysis_service()
            result = service.analyze(
                code=request.code,
                language=request.language.value,
                include_persona_review=False,  # 페르소나는 별도 스트리밍
            )

            # 분석 결과 즉시 전송
            analysis_data = {
                "level": result.level,
                "level_title": result.level_title,
                "verdict": result.verdict,
                "overall_score": round(result.overall_score, 2),
                "scores": {
                    "security": round(result.security_score, 2),
                    "quality": round(result.quality_score, 2),
                    "best_practices": round(result.best_practices_score, 2),
                    "complexity": round(result.complexity_score, 2),
                    "documentation": round(result.documentation_score, 2),
                },
                "code_review": result.code_review,
                "is_vulnerable": result.is_vulnerable,
                "vulnerability_score": round(result.vulnerability_score, 2),
                "issues": result.issues,
                "suggestions": result.suggestions,
                "language": result.language,
                "line_count": result.line_count,
            }

            yield f"event: analysis\ndata: {json.dumps(analysis_data, ensure_ascii=False)}\n\n"

            # 2단계: 페르소나 리뷰 스트리밍 (요청 시에만)
            if request.include_persona_review:
                logger.info("Starting persona review streaming...")

                # 프롬프트 생성
                scores = {
                    "overall": result.overall_score,
                    "security": result.security_score,
                    "quality": result.quality_score,
                    "best_practices": result.best_practices_score,
                    "complexity": result.complexity_score,
                    "documentation": result.documentation_score,
                }
                issues = result.issues + result.suggestions[:2]
                user_prompt = build_review_prompt(
                    level=result.level,
                    scores=scores,
                    issues=issues,
                )

                # 페르소나 LLM 스트리밍
                client = get_hf_client()
                persona_llm = client.get_persona_llm()

                full_review = ""
                for token in persona_llm.generate_review_stream(
                    system_prompt=CHEF_AHN_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    max_new_tokens=256,
                    temperature=0.7,
                ):
                    full_review += token
                    yield f"event: persona_token\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

                # 페르소나 완료
                yield f"event: persona_done\ndata: {json.dumps({'full_review': full_review}, ensure_ascii=False)}\n\n"

            # 완료
            yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"

        except Exception as e:
            logger.error(f"Stream analysis failed: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        },
    )
