"""
코드 분석 서비스 (MVP - 단순화 버전)
코드 문자열을 받아 직접 분석하고 결과 반환
"""
from typing import Optional
from dataclasses import dataclass
from app.ai.huggingface_client import get_hf_client
from app.ai.prompts.chef_ahn import CHEF_AHN_SYSTEM_PROMPT, build_review_prompt
from app.services.scoring_service import get_scoring_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


# 언어 감지를 위한 간단한 휴리스틱
LANGUAGE_PATTERNS = {
    "python": ["def ", "import ", "from ", "class ", "if __name__", "print("],
    "javascript": ["function ", "const ", "let ", "var ", "=>", "require(", "console.log"],
    "typescript": ["interface ", "type ", ": string", ": number", ": boolean", "import {"],
    "java": ["public class", "private ", "public static void main", "System.out"],
    "go": ["func ", "package ", "import (", "fmt."],
    "rust": ["fn ", "let mut", "impl ", "pub fn", "println!"],
    "cpp": ["#include", "std::", "int main(", "cout <<"],
    "c": ["#include", "int main(", "printf(", "void "],
}


@dataclass
class AnalysisResult:
    """분석 결과"""
    level: int
    level_title: str
    verdict: str
    overall_score: float

    security_score: float
    quality_score: float
    best_practices_score: float
    complexity_score: float
    documentation_score: float

    code_review: str
    persona_review: str

    is_vulnerable: bool
    vulnerability_score: float

    issues: list
    suggestions: list

    language: str
    line_count: int


class CodeAnalysisService:
    """코드 분석 서비스 (MVP)"""

    def __init__(self):
        self._hf_client = None
        self._scoring_service = None

    @property
    def hf_client(self):
        if self._hf_client is None:
            self._hf_client = get_hf_client()
        return self._hf_client

    @property
    def scoring_service(self):
        if self._scoring_service is None:
            self._scoring_service = get_scoring_service()
        return self._scoring_service

    def detect_language(self, code: str) -> str:
        """코드 언어 감지"""
        code_lower = code.lower()

        scores = {}
        for lang, patterns in LANGUAGE_PATTERNS.items():
            score = sum(1 for p in patterns if p.lower() in code_lower)
            if score > 0:
                scores[lang] = score

        if scores:
            return max(scores, key=scores.get)
        return "unknown"

    def analyze(
        self,
        code: str,
        language: str = "auto",
        include_persona_review: bool = True,
    ) -> AnalysisResult:
        """
        코드 분석 수행

        Args:
            code: 분석할 코드 문자열
            language: 프로그래밍 언어 (auto: 자동 감지)
            include_persona_review: 페르소나 리뷰 포함 여부

        Returns:
            AnalysisResult
        """
        logger.info("Starting code analysis...")

        # 언어 감지
        if language == "auto":
            language = self.detect_language(code)
            logger.info(f"Detected language: {language}")

        line_count = code.count("\n") + 1

        # 1. 코드 리뷰
        logger.info("Running code review...")
        code_reviewer = self.hf_client.get_code_reviewer()
        review_result = code_reviewer.get_quality_score(code)
        code_review = review_result.get("review", "")
        quality_score = review_result.get("quality_score", 70.0)

        # 2. 취약점 탐지
        logger.info("Running vulnerability detection...")
        vuln_detector = self.hf_client.get_vulnerability_detector()
        vuln_result = vuln_detector.detect(code)
        is_vulnerable = vuln_result.get("vulnerable", False)
        vulnerability_score = vuln_result.get("score", 70.0)
        security_score = vulnerability_score

        # 3. 추가 점수 계산 (휴리스틱)
        best_practices_score = self._calculate_best_practices(code, code_review)
        complexity_score = self._calculate_complexity(code, line_count)
        documentation_score = self._calculate_documentation(code)

        # 4. 종합 점수 및 레벨
        overall_score = self.scoring_service.calculate_overall_score(
            security=security_score,
            quality=quality_score,
            best_practices=best_practices_score,
            complexity=complexity_score,
            documentation=documentation_score,
        )

        level = self.scoring_service.get_level(overall_score)
        level_info = self.scoring_service.get_level_info(level)

        # 5. 이슈 및 제안
        issues = self._extract_issues(code_review, is_vulnerable)
        suggestions = self.scoring_service.get_improvement_suggestions(
            {
                "security": security_score,
                "quality": quality_score,
                "best_practices": best_practices_score,
                "complexity": complexity_score,
                "documentation": documentation_score,
            },
            level,
        )

        # 6. 페르소나 리뷰 생성
        persona_review = ""
        if include_persona_review:
            logger.info("Generating persona review...")
            persona_review = self._generate_persona_review(
                level=level,
                overall_score=overall_score,
                security_score=security_score,
                quality_score=quality_score,
                best_practices_score=best_practices_score,
                complexity_score=complexity_score,
                documentation_score=documentation_score,
                issues=issues,
            )

        # 7. 판정
        verdict = self._get_verdict(level)

        logger.info(f"Analysis complete. Level: {level}, Score: {overall_score:.1f}")

        return AnalysisResult(
            level=level,
            level_title=level_info.title,
            verdict=verdict,
            overall_score=overall_score,
            security_score=security_score,
            quality_score=quality_score,
            best_practices_score=best_practices_score,
            complexity_score=complexity_score,
            documentation_score=documentation_score,
            code_review=code_review,
            persona_review=persona_review,
            is_vulnerable=is_vulnerable,
            vulnerability_score=vulnerability_score,
            issues=issues,
            suggestions=suggestions,
            language=language,
            line_count=line_count,
        )

    def _calculate_best_practices(self, code: str, review: str) -> float:
        """베스트 프랙티스 점수"""
        score = 70.0

        # 긍정적 패턴
        if "def " in code or "function " in code:
            score += 5  # 함수 사용
        if "class " in code:
            score += 5  # 클래스 사용
        if "try:" in code or "try {" in code:
            score += 3  # 에러 처리

        # 부정적 패턴
        review_lower = review.lower()
        if "issue" in review_lower or "problem" in review_lower:
            score -= 5
        if "error" in review_lower or "bug" in review_lower:
            score -= 5

        return max(0, min(100, score))

    def _calculate_complexity(self, code: str, line_count: int) -> float:
        """복잡도 점수 (낮은 복잡도 = 높은 점수)"""
        # 라인 수 기반
        if line_count <= 50:
            base_score = 90.0
        elif line_count <= 100:
            base_score = 80.0
        elif line_count <= 200:
            base_score = 70.0
        elif line_count <= 500:
            base_score = 60.0
        else:
            base_score = 50.0

        # 중첩 깊이 패널티
        max_indent = 0
        for line in code.split("\n"):
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                spaces = indent if line[0] == " " else indent * 4
                max_indent = max(max_indent, spaces // 4)

        if max_indent > 5:
            base_score -= 10
        elif max_indent > 3:
            base_score -= 5

        return max(0, min(100, base_score))

    def _calculate_documentation(self, code: str) -> float:
        """문서화 점수"""
        score = 50.0

        lines = code.split("\n")
        total_lines = len(lines)
        comment_lines = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                comment_lines += 1
            elif stripped.startswith("/*") or stripped.startswith("\"\"\"") or stripped.startswith("'''"):
                comment_lines += 1

        # 주석 비율
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            if comment_ratio >= 0.2:
                score = 90.0
            elif comment_ratio >= 0.1:
                score = 75.0
            elif comment_ratio >= 0.05:
                score = 60.0

        # docstring 확인
        if '"""' in code or "'''" in code or "/**" in code:
            score += 10

        return min(100, score)

    def _extract_issues(self, review: str, is_vulnerable: bool) -> list:
        """이슈 추출"""
        issues = []

        if is_vulnerable:
            issues.append("보안 취약점이 감지되었습니다")

        review_lower = review.lower()

        issue_keywords = {
            "error": "잠재적 오류가 있습니다",
            "bug": "버그가 발견되었습니다",
            "issue": "코드 이슈가 있습니다",
            "problem": "문제가 감지되었습니다",
            "fix": "수정이 필요합니다",
            "improve": "개선이 필요합니다",
        }

        for keyword, message in issue_keywords.items():
            if keyword in review_lower and message not in issues:
                issues.append(message)

        return issues[:5]

    def _generate_persona_review(
        self,
        level: int,
        overall_score: float,
        security_score: float,
        quality_score: float,
        best_practices_score: float,
        complexity_score: float,
        documentation_score: float,
        issues: list,
    ) -> str:
        """페르소나 리뷰 생성"""
        try:
            scores = {
                "overall": overall_score,
                "security": security_score,
                "quality": quality_score,
                "best_practices": best_practices_score,
                "complexity": complexity_score,
                "documentation": documentation_score,
            }

            user_prompt = build_review_prompt(
                level=level,
                scores=scores,
                issues=issues,
            )

            persona_llm = self.hf_client.get_persona_llm()
            review = persona_llm.generate_review(
                system_prompt=CHEF_AHN_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_new_tokens=800,
                temperature=0.8,
            )

            return review

        except Exception as e:
            logger.error(f"Persona review generation failed: {e}")
            return self._get_fallback_review(level)

    def _get_fallback_review(self, level: int) -> str:
        """폴백 리뷰"""
        reviews = {
            1: "아직은 좀 force하고 있다는 느낌이 있고... 기본기가 많이 부족해요. 코딩의 세계는 무궁무진해요. 생각을 여세요. 탈락입니다.",
            2: "코드의 완성도가 조금 모자라더라구요. 제 생각에는 본인이 알고 있는 지식은 조금 모자른 것 같아요. 보류하겠습니다.",
            3: "확실한 전달력이 없으면 전 애매하다고 보거덩요. 코드가 이븐하게 쪼개지지 않았어요. 좀 더 연습이 필요해요. 생존하셨습니다.",
            4: "코드의 모듈화, SOLID. 굉장히 좋았던거 같아요. 코드를 되게 잘 짜시는 분 같아요. 통과하셨습니다.",
            5: "제가 제일 중요하게 생각하는 것은 코드의 모듈화 정도인 것 같아요. 그 모듈화가 굉장히 타이트해요. 너무 좋습니다. 축하드립니다!",
        }
        return reviews.get(level, reviews[3])

    def _get_verdict(self, level: int) -> str:
        """판정"""
        verdicts = {
            1: "탈락입니다",
            2: "보류하겠습니다",
            3: "생존하셨습니다",
            4: "통과하셨습니다",
            5: "축하드립니다. 통과하셨습니다!",
        }
        return verdicts.get(level, "생존하셨습니다")


# 싱글톤
_service: Optional[CodeAnalysisService] = None


def get_code_analysis_service() -> CodeAnalysisService:
    global _service
    if _service is None:
        _service = CodeAnalysisService()
    return _service
