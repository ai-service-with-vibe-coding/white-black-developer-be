"""
분석 요청/응답 스키마 (MVP)
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum


class Language(str, Enum):
    """지원 언어"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    AUTO = "auto"  # 자동 감지


class CodeAnalysisRequest(BaseModel):
    """코드 분석 요청"""
    code: str = Field(
        ...,
        min_length=10,
        max_length=100000,
        description="분석할 코드 (10자 이상)",
        json_schema_extra={"example": "def hello():\n    print('Hello, World!')"}
    )
    language: Language = Field(
        default=Language.AUTO,
        description="프로그래밍 언어 (auto: 자동 감지)"
    )
    include_persona_review: bool = Field(
        default=True,
        description="안성재 쉐프 페르소나 리뷰 포함 여부"
    )


class ScoreDetail(BaseModel):
    """점수 상세"""
    security: float = Field(..., description="보안 점수 (0-100)")
    quality: float = Field(..., description="코드 품질 점수 (0-100)")
    best_practices: float = Field(..., description="베스트 프랙티스 점수 (0-100)")
    complexity: float = Field(..., description="복잡도 점수 (0-100, 높을수록 좋음)")
    documentation: float = Field(..., description="문서화 점수 (0-100)")


class CodeAnalysisResponse(BaseModel):
    """코드 분석 응답"""
    # 레벨 및 점수
    level: int = Field(..., ge=1, le=5, description="평가 레벨 (1-5)")
    level_title: str = Field(..., description="레벨 타이틀 (예: 중급 개발자)")
    verdict: str = Field(..., description="최종 판정 (예: 생존하셨습니다)")
    overall_score: float = Field(..., description="종합 점수 (0-100)")

    # 상세 점수
    scores: ScoreDetail

    # 리뷰
    code_review: str = Field(..., description="기본 코드 리뷰")
    persona_review: Optional[str] = Field(None, description="안성재 쉐프 스타일 리뷰")

    # 취약점
    is_vulnerable: bool = Field(..., description="취약점 존재 여부")
    vulnerability_score: float = Field(..., description="안전 점수 (0-100, 높을수록 안전)")

    # 이슈
    issues: List[str] = Field(default_factory=list, description="발견된 이슈 목록")
    suggestions: List[str] = Field(default_factory=list, description="개선 제안")

    # 메타 정보
    language: str = Field(..., description="감지된 언어")
    line_count: int = Field(..., description="코드 라인 수")


class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    gpu_available: bool
    gpu_name: Optional[str] = None
    gpu_memory: Optional[Dict[str, str]] = None
    models_loaded: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
