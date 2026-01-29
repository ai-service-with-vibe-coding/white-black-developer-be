"""
분석 서비스
전체 분석 파이프라인 통합
"""
import asyncio
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from app.ai.processors.analysis_orchestrator import (
    get_orchestrator,
    RepositoryAnalysisResult,
    AnalysisStage,
)
from app.services.scoring_service import get_scoring_service
from app.services.persona_service import get_persona_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FullAnalysisResult:
    """전체 분석 결과"""
    # 기본 정보
    repository_name: str
    analyzed_at: datetime

    # 분석 결과
    level: int
    level_title: str
    verdict: str
    overall_score: float

    # 상세 점수
    scores: Dict[str, float]

    # 페르소나 리뷰
    persona_review: str

    # 통계
    total_files: int
    total_lines: int
    language_stats: Dict[str, int]

    # 이슈
    critical_issues: list
    warnings: list
    suggestions: list

    # 점수 상세 내역
    score_breakdown: list

    # 개선 제안
    improvements: list


class AnalysisService:
    """분석 서비스"""

    def __init__(self):
        self._orchestrator = None
        self._scoring_service = None
        self._persona_service = None

    @property
    def orchestrator(self):
        if self._orchestrator is None:
            self._orchestrator = get_orchestrator()
        return self._orchestrator

    @property
    def scoring_service(self):
        if self._scoring_service is None:
            self._scoring_service = get_scoring_service()
        return self._scoring_service

    @property
    def persona_service(self):
        if self._persona_service is None:
            self._persona_service = get_persona_service()
        return self._persona_service

    async def analyze_repository(
        self,
        repo_path: str,
        repo_name: str,
        progress_callback: Optional[Callable] = None,
        generate_persona_review: bool = True,
    ) -> FullAnalysisResult:
        """
        저장소 전체 분석 수행

        Args:
            repo_path: 저장소 로컬 경로
            repo_name: 저장소 이름 (표시용)
            progress_callback: 진행 상황 콜백 (stage, progress)
            generate_persona_review: 페르소나 리뷰 생성 여부

        Returns:
            FullAnalysisResult
        """
        logger.info(f"Starting full analysis for: {repo_name}")
        start_time = datetime.now()

        try:
            # 1. 코드 분석 (Code Review + Vulnerability Detection)
            analysis_result = await self.orchestrator.analyze_repository(
                repo_path=repo_path,
                progress_callback=progress_callback,
            )

            # 2. 점수 리포트 생성
            score_report = self.scoring_service.format_score_report(analysis_result)

            # 3. 페르소나 리뷰 생성
            persona_review = ""
            if generate_persona_review:
                if progress_callback:
                    await progress_callback(AnalysisStage.REVIEW_GENERATION, 0)

                logger.info("Generating persona review...")
                persona_review = self.persona_service.generate_review(analysis_result)

                if progress_callback:
                    await progress_callback(AnalysisStage.REVIEW_GENERATION, 100)

            # 4. 최종 결과 조합
            result = FullAnalysisResult(
                repository_name=repo_name,
                analyzed_at=datetime.now(),
                level=analysis_result.level,
                level_title=self.persona_service.get_level_title_korean(analysis_result.level),
                verdict=self.persona_service.get_verdict(analysis_result.level),
                overall_score=analysis_result.overall_score,
                scores={
                    "security": analysis_result.security_score,
                    "quality": analysis_result.quality_score,
                    "best_practices": analysis_result.best_practices_score,
                    "complexity": analysis_result.complexity_score,
                    "documentation": analysis_result.documentation_score,
                },
                persona_review=persona_review,
                total_files=analysis_result.total_files,
                total_lines=analysis_result.total_lines,
                language_stats=analysis_result.language_stats,
                critical_issues=analysis_result.critical_issues,
                warnings=analysis_result.warnings,
                suggestions=analysis_result.suggestions,
                score_breakdown=score_report["breakdown"],
                improvements=score_report["improvements"],
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Analysis completed for {repo_name} in {elapsed:.1f}s. "
                f"Level: {result.level}, Score: {result.overall_score:.1f}"
            )

            return result

        except Exception as e:
            logger.error(f"Analysis failed for {repo_name}: {e}")
            raise

    async def quick_analyze(
        self,
        repo_path: str,
        repo_name: str,
    ) -> Dict:
        """
        빠른 분석 (페르소나 리뷰 없이)

        Args:
            repo_path: 저장소 경로
            repo_name: 저장소 이름

        Returns:
            분석 결과 딕셔너리
        """
        result = await self.analyze_repository(
            repo_path=repo_path,
            repo_name=repo_name,
            generate_persona_review=False,
        )

        return {
            "repository": repo_name,
            "level": result.level,
            "level_title": result.level_title,
            "overall_score": result.overall_score,
            "scores": result.scores,
            "stats": {
                "files": result.total_files,
                "lines": result.total_lines,
                "languages": result.language_stats,
            },
        }

    def to_dict(self, result: FullAnalysisResult) -> Dict:
        """분석 결과를 딕셔너리로 변환"""
        return {
            "repository_name": result.repository_name,
            "analyzed_at": result.analyzed_at.isoformat(),
            "level": result.level,
            "level_title": result.level_title,
            "verdict": result.verdict,
            "overall_score": result.overall_score,
            "scores": result.scores,
            "persona_review": result.persona_review,
            "stats": {
                "total_files": result.total_files,
                "total_lines": result.total_lines,
                "languages": result.language_stats,
            },
            "issues": {
                "critical": result.critical_issues,
                "warnings": result.warnings,
                "suggestions": result.suggestions,
            },
            "score_breakdown": result.score_breakdown,
            "improvements": result.improvements,
        }


# 전역 인스턴스
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    """분석 서비스 싱글톤"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
