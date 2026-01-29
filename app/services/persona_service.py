"""
페르소나 리뷰 생성 서비스
안성재 쉐프 스타일의 코드 리뷰 생성
"""
from typing import Dict, List, Optional
from app.ai.huggingface_client import get_hf_client
from app.ai.prompts.chef_ahn import CHEF_AHN_SYSTEM_PROMPT, build_review_prompt
from app.ai.processors.analysis_orchestrator import RepositoryAnalysisResult
from app.services.scoring_service import get_scoring_service, LEVEL_DEFINITIONS
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PersonaService:
    """페르소나 리뷰 생성 서비스"""

    def __init__(self):
        self._hf_client = None
        self._scoring_service = get_scoring_service()

    @property
    def hf_client(self):
        """HuggingFace 클라이언트 (lazy loading)"""
        if self._hf_client is None:
            self._hf_client = get_hf_client()
        return self._hf_client

    def generate_review(
        self,
        analysis_result: RepositoryAnalysisResult,
        max_new_tokens: int = 1000,
        temperature: float = 0.8,
    ) -> str:
        """
        분석 결과 기반 페르소나 리뷰 생성

        Args:
            analysis_result: 저장소 분석 결과
            max_new_tokens: 생성할 최대 토큰 수
            temperature: 생성 온도 (높을수록 창의적)

        Returns:
            안성재 쉐프 스타일 리뷰 텍스트
        """
        try:
            # 점수 딕셔너리 생성
            scores = {
                "overall": analysis_result.overall_score,
                "security": analysis_result.security_score,
                "quality": analysis_result.quality_score,
                "best_practices": analysis_result.best_practices_score,
                "complexity": analysis_result.complexity_score,
                "documentation": analysis_result.documentation_score,
            }

            # 주요 이슈 목록 (최대 5개)
            issues = (
                analysis_result.critical_issues[:2] +
                analysis_result.warnings[:2] +
                analysis_result.suggestions[:1]
            )

            # 프롬프트 생성
            user_prompt = build_review_prompt(
                level=analysis_result.level,
                scores=scores,
                issues=issues,
            )

            logger.info(f"Generating persona review for level {analysis_result.level}...")

            # LLM으로 리뷰 생성
            persona_llm = self.hf_client.get_persona_llm()
            review = persona_llm.generate_review(
                system_prompt=CHEF_AHN_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
            )

            logger.info(f"Persona review generated ({len(review)} characters)")

            return review

        except Exception as e:
            logger.error(f"Failed to generate persona review: {e}")
            return self._get_fallback_review(analysis_result)

    def generate_quick_review(
        self,
        level: int,
        overall_score: float,
        main_issue: Optional[str] = None,
    ) -> str:
        """
        간단한 퀵 리뷰 생성

        Args:
            level: 평가 레벨 (1-5)
            overall_score: 종합 점수
            main_issue: 주요 이슈 (선택)

        Returns:
            짧은 리뷰 텍스트
        """
        try:
            scores = {
                "overall": overall_score,
                "security": 70.0,
                "quality": 70.0,
                "best_practices": 70.0,
                "complexity": 70.0,
                "documentation": 70.0,
            }

            issues = [main_issue] if main_issue else []

            user_prompt = build_review_prompt(
                level=level,
                scores=scores,
                issues=issues,
            )

            persona_llm = self.hf_client.get_persona_llm()
            review = persona_llm.generate_review(
                system_prompt=CHEF_AHN_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_new_tokens=500,
                temperature=0.9,
            )

            return review

        except Exception as e:
            logger.error(f"Failed to generate quick review: {e}")
            return self._get_level_message(level)

    def _get_fallback_review(self, analysis_result: RepositoryAnalysisResult) -> str:
        """폴백 리뷰 (LLM 실패 시)"""
        level = analysis_result.level
        score = analysis_result.overall_score

        base_message = self._get_level_message(level)

        # 주요 이슈 추가
        issues_text = ""
        if analysis_result.critical_issues:
            issues_text = f"\n\n주요 문제점: {', '.join(analysis_result.critical_issues[:3])}"

        return f"{base_message}\n\n종합 점수: {score:.1f}점{issues_text}"

    def _get_level_message(self, level: int) -> str:
        """레벨별 기본 메시지"""
        messages = {
            1: "아직은 좀 force하고 있다는 느낌이 있고... 기본기가 많이 부족해요. "
               "코딩의 세계는 무궁무진해요. 생각을 여세요. 탈락입니다.",
            2: "코드의 완성도가 조금 모자라더라구요. 제 생각에는 본인이 알고 있는 지식은 "
               "조금 모자른 것 같아요. 보류하겠습니다.",
            3: "확실한 전달력이 없으면 전 애매하다고 보거덩요. 코드가 이븐하게 쪼개지지 않았어요. "
               "좀 더 연습이 필요해요. 생존하셨습니다.",
            4: "코드의 모듈화, SOLID. 굉장히 좋았던거 같아요. 코드를 되게 잘 짜시는 분 같아요. "
               "다음 거를 보고 싶고, 여기다 다른 거를 어떻게 추가할 수 있을까? 라는 기대감을 "
               "갖고, 굉장히 컴플릿 한거죠. 통과하셨습니다.",
            5: "제가 제일 중요하게 생각하는 것은 코드의 모듈화 정도인 것 같아요. "
               "그 모듈화가 굉장히 타이트해요. 와 이거 존나 잘 짰다... "
               "너무 좋습니다. 축하드립니다. 통과하셨습니다!",
        }
        return messages.get(level, messages[3])

    def get_verdict(self, level: int) -> str:
        """
        레벨에 따른 최종 판정

        Args:
            level: 평가 레벨 (1-5)

        Returns:
            판정 문구
        """
        verdicts = {
            1: "탈락입니다",
            2: "보류하겠습니다",
            3: "생존하셨습니다",
            4: "통과하셨습니다",
            5: "축하드립니다. 통과하셨습니다!",
        }
        return verdicts.get(level, "생존하셨습니다")

    def get_level_title_korean(self, level: int) -> str:
        """
        레벨의 한글 타이틀

        Args:
            level: 평가 레벨 (1-5)

        Returns:
            한글 타이틀
        """
        level_info = LEVEL_DEFINITIONS.get(level)
        if level_info:
            return level_info.title
        return "개발자"

    def format_full_review(
        self,
        analysis_result: RepositoryAnalysisResult,
        persona_review: str,
    ) -> Dict:
        """
        전체 리뷰 포맷

        Args:
            analysis_result: 분석 결과
            persona_review: 페르소나 리뷰 텍스트

        Returns:
            전체 리뷰 딕셔너리
        """
        level = analysis_result.level

        return {
            "level": level,
            "level_title": self.get_level_title_korean(level),
            "verdict": self.get_verdict(level),
            "overall_score": analysis_result.overall_score,
            "persona_review": persona_review,
            "scores": {
                "security": analysis_result.security_score,
                "quality": analysis_result.quality_score,
                "best_practices": analysis_result.best_practices_score,
                "complexity": analysis_result.complexity_score,
                "documentation": analysis_result.documentation_score,
            },
            "issues": {
                "critical": analysis_result.critical_issues,
                "warnings": analysis_result.warnings,
                "suggestions": analysis_result.suggestions,
            },
            "stats": {
                "total_files": analysis_result.total_files,
                "total_lines": analysis_result.total_lines,
                "languages": analysis_result.language_stats,
            },
        }


# 전역 인스턴스
_persona_service: Optional[PersonaService] = None


def get_persona_service() -> PersonaService:
    """페르소나 서비스 싱글톤"""
    global _persona_service
    if _persona_service is None:
        _persona_service = PersonaService()
    return _persona_service
