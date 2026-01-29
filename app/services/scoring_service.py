"""
점수 계산 서비스
코드 분석 결과를 기반으로 최종 점수 및 레벨 산출
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.ai.processors.analysis_orchestrator import RepositoryAnalysisResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScoreBreakdown:
    """점수 상세 내역"""
    category: str
    score: float
    weight: float
    weighted_score: float
    description: str


@dataclass
class LevelInfo:
    """레벨 정보"""
    level: int
    title: str
    description: str
    min_score: float
    max_score: float


# 레벨 정의
LEVEL_DEFINITIONS = {
    1: LevelInfo(
        level=1,
        title="견습 개발자",
        description="기본기를 다지는 단계입니다. 코드 작성의 기초를 익혀야 합니다.",
        min_score=0,
        max_score=44.99,
    ),
    2: LevelInfo(
        level=2,
        title="초급 개발자",
        description="기본적인 코드 작성은 가능하나, 품질과 보안에 더 신경 써야 합니다.",
        min_score=45,
        max_score=59.99,
    ),
    3: LevelInfo(
        level=3,
        title="중급 개발자",
        description="안정적인 코드를 작성합니다. 아키텍처와 설계에 대한 이해가 필요합니다.",
        min_score=60,
        max_score=74.99,
    ),
    4: LevelInfo(
        level=4,
        title="고급 개발자",
        description="높은 품질의 코드를 작성합니다. 팀 리딩과 코드 리뷰 역량이 있습니다.",
        min_score=75,
        max_score=89.99,
    ),
    5: LevelInfo(
        level=5,
        title="마스터 개발자",
        description="최고 수준의 코드를 작성합니다. 아키텍처 설계와 기술 리딩이 가능합니다.",
        min_score=90,
        max_score=100,
    ),
}

# 점수 가중치
SCORE_WEIGHTS = {
    "security": 0.30,
    "quality": 0.25,
    "best_practices": 0.20,
    "complexity": 0.15,
    "documentation": 0.10,
}

# 카테고리 설명
CATEGORY_DESCRIPTIONS = {
    "security": "보안 취약점 및 안전한 코딩 관행",
    "quality": "코드 가독성, 구조, 유지보수성",
    "best_practices": "업계 표준 및 권장 패턴 준수",
    "complexity": "코드 복잡도 및 모듈화 수준",
    "documentation": "주석, 문서화, 명명 규칙",
}


class ScoringService:
    """점수 계산 서비스"""

    def calculate_overall_score(
        self,
        security: float,
        quality: float,
        best_practices: float,
        complexity: float,
        documentation: float,
    ) -> float:
        """
        종합 점수 계산

        Args:
            security: 보안 점수 (0-100)
            quality: 품질 점수 (0-100)
            best_practices: 베스트 프랙티스 점수 (0-100)
            complexity: 복잡도 점수 (0-100)
            documentation: 문서화 점수 (0-100)

        Returns:
            종합 점수 (0-100)
        """
        overall = (
            security * SCORE_WEIGHTS["security"] +
            quality * SCORE_WEIGHTS["quality"] +
            best_practices * SCORE_WEIGHTS["best_practices"] +
            complexity * SCORE_WEIGHTS["complexity"] +
            documentation * SCORE_WEIGHTS["documentation"]
        )

        return round(overall, 2)

    def get_level(self, overall_score: float) -> int:
        """
        점수에 따른 레벨 반환

        Args:
            overall_score: 종합 점수

        Returns:
            레벨 (1-5)
        """
        if overall_score >= 90:
            return 5
        elif overall_score >= 75:
            return 4
        elif overall_score >= 60:
            return 3
        elif overall_score >= 45:
            return 2
        else:
            return 1

    def get_level_info(self, level: int) -> LevelInfo:
        """
        레벨 정보 반환

        Args:
            level: 레벨 (1-5)

        Returns:
            LevelInfo 객체
        """
        return LEVEL_DEFINITIONS.get(level, LEVEL_DEFINITIONS[1])

    def get_score_breakdown(
        self,
        scores: Dict[str, float],
    ) -> List[ScoreBreakdown]:
        """
        점수 상세 내역 생성

        Args:
            scores: 카테고리별 점수

        Returns:
            ScoreBreakdown 리스트
        """
        breakdown = []

        for category, weight in SCORE_WEIGHTS.items():
            score = scores.get(category, 0)
            breakdown.append(ScoreBreakdown(
                category=category,
                score=score,
                weight=weight,
                weighted_score=score * weight,
                description=CATEGORY_DESCRIPTIONS.get(category, ""),
            ))

        # 가중 점수 기준 내림차순 정렬
        breakdown.sort(key=lambda x: x.weighted_score, reverse=True)

        return breakdown

    def get_improvement_suggestions(
        self,
        scores: Dict[str, float],
        level: int,
    ) -> List[str]:
        """
        개선 제안 생성

        Args:
            scores: 카테고리별 점수
            level: 현재 레벨

        Returns:
            개선 제안 리스트
        """
        suggestions = []

        # 가장 낮은 점수 카테고리 찾기
        sorted_scores = sorted(scores.items(), key=lambda x: x[1])

        for category, score in sorted_scores[:3]:  # 하위 3개 카테고리
            if score < 70:
                suggestion = self._get_category_suggestion(category, score)
                suggestions.append(suggestion)

        # 레벨별 추가 제안
        if level < 3:
            suggestions.append("기본기를 다지기 위해 클린 코드 원칙을 학습하세요.")
        elif level < 5:
            suggestions.append("설계 패턴과 아키텍처에 대한 이해를 높이세요.")

        return suggestions

    def _get_category_suggestion(self, category: str, score: float) -> str:
        """카테고리별 개선 제안"""
        suggestions = {
            "security": f"보안 점수가 {score:.0f}점입니다. 입력 검증, SQL 인젝션 방지 등 보안 코딩 가이드를 참고하세요.",
            "quality": f"코드 품질 점수가 {score:.0f}점입니다. 코드 리팩토링과 SOLID 원칙을 적용해보세요.",
            "best_practices": f"베스트 프랙티스 점수가 {score:.0f}점입니다. 업계 표준 코딩 컨벤션을 따르세요.",
            "complexity": f"복잡도 점수가 {score:.0f}점입니다. 함수를 작게 나누고 모듈화를 개선하세요.",
            "documentation": f"문서화 점수가 {score:.0f}점입니다. 주석과 문서화를 추가하세요.",
        }
        return suggestions.get(category, f"{category} 개선이 필요합니다.")

    def format_score_report(
        self,
        analysis_result: RepositoryAnalysisResult,
    ) -> Dict:
        """
        점수 리포트 포맷

        Args:
            analysis_result: 분석 결과

        Returns:
            리포트 딕셔너리
        """
        scores = {
            "security": analysis_result.security_score,
            "quality": analysis_result.quality_score,
            "best_practices": analysis_result.best_practices_score,
            "complexity": analysis_result.complexity_score,
            "documentation": analysis_result.documentation_score,
        }

        level = analysis_result.level
        level_info = self.get_level_info(level)
        breakdown = self.get_score_breakdown(scores)
        suggestions = self.get_improvement_suggestions(scores, level)

        return {
            "overall_score": analysis_result.overall_score,
            "level": level,
            "level_title": level_info.title,
            "level_description": level_info.description,
            "scores": scores,
            "breakdown": [
                {
                    "category": b.category,
                    "score": b.score,
                    "weight": f"{b.weight * 100:.0f}%",
                    "weighted_score": b.weighted_score,
                    "description": b.description,
                }
                for b in breakdown
            ],
            "improvements": suggestions,
            "stats": {
                "total_files": analysis_result.total_files,
                "total_lines": analysis_result.total_lines,
                "languages": analysis_result.language_stats,
            },
            "issues": {
                "critical": len(analysis_result.critical_issues),
                "warnings": len(analysis_result.warnings),
                "suggestions": len(analysis_result.suggestions),
            },
        }


# 전역 인스턴스
_scoring_service: Optional[ScoringService] = None


def get_scoring_service() -> ScoringService:
    """점수 서비스 싱글톤"""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
