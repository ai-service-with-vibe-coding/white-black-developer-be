"""
코드 분석 서비스 (MVP - 단순화 버전)
코드 문자열을 받아 직접 분석하고 결과 반환
"""
import re
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

        # 보안 점수 추가 휴리스틱
        security_score = self._adjust_security_score(code, vulnerability_score, is_vulnerable)

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

    def _adjust_security_score(self, code: str, base_score: float, is_vulnerable: bool) -> float:
        """보안 점수 조정 (추가 휴리스틱)"""
        score = base_score
        code_lower = code.lower()

        # ===== 심각한 보안 이슈 (-30 ~ -50) =====
        critical_patterns = [
            ("eval(", -30),
            ("exec(", -30),
            ("os.system(", -25),
            ("subprocess.call(", -20),
            ("shell=True", -25),
            ("pickle.loads(", -20),
            ("yaml.load(", -15),  # yaml.safe_load 대신
            ("__import__", -20),
        ]
        for pattern, penalty in critical_patterns:
            if pattern in code_lower:
                score += penalty

        # ===== 하드코딩된 민감 정보 (-20 ~ -40) =====
        sensitive_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', -40),
            (r'api_key\s*=\s*["\'][^"\']+["\']', -35),
            (r'secret\s*=\s*["\'][^"\']+["\']', -35),
            (r'token\s*=\s*["\'][^"\']+["\']', -30),
            (r'private_key', -30),
        ]
        for pattern, penalty in sensitive_patterns:
            if re.search(pattern, code_lower):
                score += penalty
                break  # 하나만 적용

        # ===== SQL Injection 위험 (-25) =====
        sql_patterns = [
            'execute("', "execute('",
            'format(sql', 'f"SELECT', "f'SELECT",
            '% query', '%s" % ',
        ]
        for pattern in sql_patterns:
            if pattern in code_lower or pattern in code:
                score -= 25
                break

        # ===== XSS 위험 (-20) =====
        xss_patterns = ['innerhtml', 'document.write', 'v-html']
        for pattern in xss_patterns:
            if pattern in code_lower:
                score -= 20
                break

        # ===== 좋은 보안 패턴 (+10 ~ +20) =====
        good_patterns = [
            ("parameterized", 10),
            ("prepared_statement", 10),
            ("escape(", 10),
            ("sanitize", 10),
            ("validate", 10),
            ("bcrypt", 15),
            ("hashlib", 10),
            ("secrets.", 15),
            ("csrf", 10),
            ("https://", 5),
        ]
        for pattern, bonus in good_patterns:
            if pattern in code_lower:
                score += bonus

        # 취약점 감지 시 추가 페널티
        if is_vulnerable:
            score -= 15

        return max(10, min(95, score))

    def _calculate_best_practices(self, code: str, review: str) -> float:
        """베스트 프랙티스 점수 (엄격한 기준)"""
        score = 50.0  # 기본 점수를 낮게 시작

        lines = code.split("\n")
        code_lower = code.lower()

        # ===== 긍정적 패턴 (최대 +50) =====
        # 함수/메서드 사용 (+10)
        func_count = code.count("def ") + code.count("function ") + code.count("func ")
        if func_count >= 3:
            score += 10
        elif func_count >= 1:
            score += 5

        # 클래스 사용 (+10)
        if "class " in code:
            score += 10

        # 에러 처리 (+10)
        error_handling = code.count("try:") + code.count("try {") + code.count("catch") + code.count("except")
        if error_handling >= 2:
            score += 10
        elif error_handling >= 1:
            score += 5

        # 타입 힌트/어노테이션 (+10)
        if ": str" in code or ": int" in code or ": List" in code or "-> " in code:
            score += 10
        if "interface " in code or "type " in code:
            score += 10

        # 상수 사용 (+5)
        if "const " in code or code.count("UPPER_CASE") > 0 or "final " in code:
            score += 5

        # 모듈 import 정리 (+5)
        if "from " in code and "import " in code:
            score += 5

        # ===== 부정적 패턴 (최대 -50) =====
        # 하드코딩된 값 (-15)
        hardcoded_patterns = [
            'password', 'secret', 'api_key', 'apikey',
            '127.0.0.1', 'localhost:',
            '"http://', "'http://",
        ]
        for pattern in hardcoded_patterns:
            if pattern in code_lower:
                score -= 15
                break

        # 매직 넘버 (-10)
        import re
        magic_numbers = re.findall(r'[=<>]\s*\d{2,}[^0-9]', code)
        if len(magic_numbers) > 3:
            score -= 10
        elif len(magic_numbers) > 1:
            score -= 5

        # print/console.log 디버깅 (-10)
        debug_count = code.count("print(") + code.count("console.log") + code.count("System.out")
        if debug_count > 5:
            score -= 10
        elif debug_count > 2:
            score -= 5

        # 전역 변수 사용 (-10)
        if "global " in code:
            score -= 10

        # eval/exec 사용 (-15)
        if "eval(" in code or "exec(" in code:
            score -= 15

        # TODO/FIXME/HACK 주석 (-5)
        if "TODO" in code or "FIXME" in code or "HACK" in code:
            score -= 5

        # 빈 except/catch (-10)
        if "except:" in code or "except Exception:" in code or "catch {" in code:
            if "pass" in code or "// " not in code:
                score -= 10

        # 매우 긴 라인 (-10)
        long_lines = sum(1 for line in lines if len(line) > 120)
        if long_lines > 5:
            score -= 10
        elif long_lines > 2:
            score -= 5

        # 리뷰 결과 반영
        review_lower = review.lower()
        if "issue" in review_lower or "problem" in review_lower:
            score -= 10
        if "error" in review_lower or "bug" in review_lower:
            score -= 10
        if "good" in review_lower or "clean" in review_lower:
            score += 10

        return max(10, min(95, score))

    def _calculate_complexity(self, code: str, line_count: int) -> float:
        """복잡도 점수 (엄격한 기준: 낮은 복잡도 = 높은 점수)"""
        score = 70.0
        lines = code.split("\n")

        # ===== 함수/메서드 크기 분석 =====
        # 함수 개수
        func_count = code.count("def ") + code.count("function ") + code.count("func ")

        if func_count > 0:
            avg_lines_per_func = line_count / func_count
            if avg_lines_per_func <= 15:
                score += 15  # 작은 함수들 - 매우 좋음
            elif avg_lines_per_func <= 30:
                score += 5   # 적절한 크기
            elif avg_lines_per_func > 50:
                score -= 15  # 너무 큰 함수
            elif avg_lines_per_func > 30:
                score -= 5   # 다소 큰 함수
        else:
            # 함수 없이 스크립트 형태
            if line_count > 50:
                score -= 20  # 구조화 안됨

        # ===== 중첩 깊이 분석 (더 엄격) =====
        max_indent = 0
        deep_nesting_count = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
                indent = len(line) - len(stripped)
                indent_level = indent // 4 if "    " in line[:indent] or indent % 4 == 0 else indent // 2
                max_indent = max(max_indent, indent_level)
                if indent_level >= 4:
                    deep_nesting_count += 1

        if max_indent >= 6:
            score -= 25  # 매우 깊은 중첩
        elif max_indent >= 5:
            score -= 15
        elif max_indent >= 4:
            score -= 10
        elif max_indent <= 2:
            score += 10  # 얕은 중첩 - 좋음

        if deep_nesting_count > 10:
            score -= 10  # 깊은 중첩이 많음

        # ===== 조건문/반복문 복잡도 =====
        conditionals = code.count("if ") + code.count("elif ") + code.count("else:") + \
                       code.count("else {") + code.count("switch") + code.count("case ")
        loops = code.count("for ") + code.count("while ") + code.count(".forEach") + \
                code.count(".map(") + code.count(".filter(")

        cyclomatic = conditionals + loops
        if cyclomatic > 20:
            score -= 20  # 매우 복잡
        elif cyclomatic > 10:
            score -= 10
        elif cyclomatic <= 5:
            score += 10  # 단순

        # ===== 라인 길이 =====
        very_long_lines = sum(1 for line in lines if len(line) > 100)
        if very_long_lines > 10:
            score -= 15
        elif very_long_lines > 5:
            score -= 5

        # ===== 파일 크기 =====
        if line_count > 500:
            score -= 20  # 파일이 너무 큼
        elif line_count > 300:
            score -= 10
        elif line_count <= 100:
            score += 5  # 적절한 크기

        return max(15, min(95, score))

    def _calculate_documentation(self, code: str) -> float:
        """문서화 점수 (엄격한 기준)"""
        score = 30.0  # 문서화 없으면 낮은 점수

        lines = code.split("\n")
        total_lines = len([l for l in lines if l.strip()])  # 빈 줄 제외
        comment_lines = 0
        docstring_count = 0
        inline_comments = 0

        in_multiline = False
        for line in lines:
            stripped = line.strip()

            # 멀티라인 주석/docstring
            if '"""' in stripped or "'''" in stripped or "/*" in stripped:
                docstring_count += 1
                in_multiline = not in_multiline if stripped.count('"""') == 1 or stripped.count("'''") == 1 else False
                comment_lines += 1
            elif in_multiline:
                comment_lines += 1
            elif stripped.startswith("#") or stripped.startswith("//"):
                comment_lines += 1
            # 인라인 주석
            elif "#" in stripped or "//" in stripped:
                inline_comments += 1

        # ===== 주석 비율 점수 =====
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            if comment_ratio >= 0.25:
                score += 35  # 매우 잘 문서화됨
            elif comment_ratio >= 0.15:
                score += 25
            elif comment_ratio >= 0.10:
                score += 15
            elif comment_ratio >= 0.05:
                score += 5
            elif comment_ratio < 0.02:
                score -= 10  # 거의 주석 없음

        # ===== Docstring 점수 =====
        func_count = code.count("def ") + code.count("function ") + code.count("func ")
        class_count = code.count("class ")

        if docstring_count >= func_count + class_count and func_count > 0:
            score += 20  # 모든 함수/클래스에 docstring
        elif docstring_count >= (func_count + class_count) / 2:
            score += 10  # 절반 이상
        elif docstring_count > 0:
            score += 5
        elif func_count > 3:
            score -= 10  # 함수가 많은데 docstring 없음

        # ===== 좋은 문서화 패턴 =====
        good_patterns = [
            "Args:", "Returns:", "Raises:",  # Python docstring
            "@param", "@return", "@throws",   # JSDoc/JavaDoc
            "Parameters", "Example:",          # 일반
        ]
        for pattern in good_patterns:
            if pattern in code:
                score += 5
                break

        # ===== README나 설명 패턴 =====
        if "README" in code or "Usage:" in code or "Example:" in code:
            score += 5

        # ===== 나쁜 패턴 =====
        # 의미없는 주석
        meaningless = ["# TODO", "# FIXME", "// TODO", "// FIXME", "# test", "// test"]
        for pattern in meaningless:
            if pattern in code:
                score -= 3

        # 변수명만 있는 주석 (예: # x, # i)
        import re
        short_comments = re.findall(r'#\s*[a-z]\s*$', code, re.MULTILINE)
        if len(short_comments) > 3:
            score -= 5

        return max(10, min(95, score))

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
