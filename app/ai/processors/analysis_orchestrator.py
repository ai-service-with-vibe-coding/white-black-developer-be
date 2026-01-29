"""
분석 오케스트레이터
여러 AI 모델을 조율하여 코드 분석 수행
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from app.ai.huggingface_client import get_hf_client
from app.ai.processors.code_preprocessor import (
    CodeFile,
    CodeChunk,
    get_preprocessor,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisStage(str, Enum):
    """분석 단계"""
    PREPROCESSING = "preprocessing"
    CODE_REVIEW = "code_review"
    VULNERABILITY_SCAN = "vulnerability_scan"
    SCORING = "scoring"
    REVIEW_GENERATION = "review_generation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FileAnalysisResult:
    """파일별 분석 결과"""
    file_path: str
    language: str
    line_count: int
    code_review: str = ""
    vulnerability: Dict = field(default_factory=dict)
    quality_score: float = 0.0
    issues: List[str] = field(default_factory=list)


@dataclass
class RepositoryAnalysisResult:
    """저장소 전체 분석 결과"""
    total_files: int = 0
    total_lines: int = 0
    language_stats: Dict[str, int] = field(default_factory=dict)
    file_results: List[FileAnalysisResult] = field(default_factory=list)

    # 종합 점수
    security_score: float = 0.0
    quality_score: float = 0.0
    best_practices_score: float = 0.0
    complexity_score: float = 0.0
    documentation_score: float = 0.0
    overall_score: float = 0.0

    # 이슈 요약
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    # 레벨
    level: int = 1


class AnalysisOrchestrator:
    """분석 오케스트레이터"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.preprocessor = get_preprocessor()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._hf_client = None

    @property
    def hf_client(self):
        """HuggingFace 클라이언트 (lazy loading)"""
        if self._hf_client is None:
            self._hf_client = get_hf_client()
        return self._hf_client

    async def analyze_repository(
        self,
        repo_path: str,
        progress_callback: Optional[callable] = None,
    ) -> RepositoryAnalysisResult:
        """
        저장소 전체 분석

        Args:
            repo_path: 저장소 경로
            progress_callback: 진행 상황 콜백 (stage, progress)

        Returns:
            RepositoryAnalysisResult
        """
        result = RepositoryAnalysisResult()

        try:
            # 1. 전처리
            if progress_callback:
                await progress_callback(AnalysisStage.PREPROCESSING, 0)

            code_files, chunks = self.preprocessor.prepare_for_analysis(repo_path)

            if not code_files:
                logger.warning("No code files found to analyze")
                return result

            result.total_files = len(code_files)
            result.total_lines = self.preprocessor.get_total_lines(code_files)
            result.language_stats = self.preprocessor.get_language_stats(code_files)

            logger.info(
                f"Analyzing {result.total_files} files, "
                f"{result.total_lines} lines, "
                f"languages: {result.language_stats}"
            )

            # 2. 코드 리뷰
            if progress_callback:
                await progress_callback(AnalysisStage.CODE_REVIEW, 0)

            file_results = await self._analyze_files(code_files, progress_callback)
            result.file_results = file_results

            # 3. 취약점 스캔
            if progress_callback:
                await progress_callback(AnalysisStage.VULNERABILITY_SCAN, 0)

            await self._scan_vulnerabilities(file_results, code_files)

            # 4. 점수 계산
            if progress_callback:
                await progress_callback(AnalysisStage.SCORING, 0)

            self._calculate_scores(result)

            # 5. 이슈 집계
            self._aggregate_issues(result)

            if progress_callback:
                await progress_callback(AnalysisStage.COMPLETED, 100)

            logger.info(
                f"Analysis completed. Level: {result.level}, "
                f"Overall score: {result.overall_score:.1f}"
            )

            return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            if progress_callback:
                await progress_callback(AnalysisStage.FAILED, 0)
            raise

    async def _analyze_files(
        self,
        code_files: List[CodeFile],
        progress_callback: Optional[callable] = None,
    ) -> List[FileAnalysisResult]:
        """파일별 코드 리뷰 분석"""
        results = []
        code_reviewer = self.hf_client.get_code_reviewer()

        total = len(code_files)
        for i, code_file in enumerate(code_files):
            try:
                # 코드 리뷰 수행
                review_result = code_reviewer.get_quality_score(code_file.content)

                file_result = FileAnalysisResult(
                    file_path=code_file.relative_path,
                    language=code_file.language,
                    line_count=code_file.line_count,
                    code_review=review_result.get("review", ""),
                    quality_score=review_result.get("quality_score", 70.0),
                )

                # 리뷰에서 이슈 추출
                file_result.issues = self._extract_issues_from_review(
                    review_result.get("review", "")
                )

                results.append(file_result)

                if progress_callback:
                    progress = int((i + 1) / total * 100)
                    await progress_callback(AnalysisStage.CODE_REVIEW, progress)

            except Exception as e:
                logger.warning(f"Error analyzing file {code_file.relative_path}: {e}")
                results.append(FileAnalysisResult(
                    file_path=code_file.relative_path,
                    language=code_file.language,
                    line_count=code_file.line_count,
                    quality_score=50.0,
                    issues=[f"Analysis error: {str(e)}"],
                ))

        return results

    async def _scan_vulnerabilities(
        self,
        file_results: List[FileAnalysisResult],
        code_files: List[CodeFile],
    ):
        """취약점 스캔"""
        detector = self.hf_client.get_vulnerability_detector()

        for file_result, code_file in zip(file_results, code_files):
            try:
                vuln_result = detector.detect(code_file.content)
                file_result.vulnerability = vuln_result

                if vuln_result.get("vulnerable", False):
                    confidence = vuln_result.get("confidence", 0)
                    file_result.issues.append(
                        f"Security vulnerability detected (confidence: {confidence:.1%})"
                    )

            except Exception as e:
                logger.warning(f"Vulnerability scan error for {file_result.file_path}: {e}")
                file_result.vulnerability = {"error": str(e)}

    def _extract_issues_from_review(self, review: str) -> List[str]:
        """리뷰 텍스트에서 이슈 추출"""
        issues = []
        review_lower = review.lower()

        # 부정적 키워드 기반 이슈 추출
        issue_keywords = {
            "error": "Potential error detected",
            "bug": "Possible bug found",
            "issue": "Code issue identified",
            "problem": "Problem in code",
            "fix": "Code needs fixing",
            "improve": "Improvement needed",
            "refactor": "Refactoring recommended",
            "duplicate": "Duplicate code detected",
            "complexity": "High complexity",
            "naming": "Naming convention issue",
        }

        for keyword, message in issue_keywords.items():
            if keyword in review_lower:
                issues.append(message)

        return issues[:5]  # 최대 5개

    def _calculate_scores(self, result: RepositoryAnalysisResult):
        """종합 점수 계산"""
        if not result.file_results:
            return

        # 보안 점수 (취약점 기반)
        security_scores = []
        for fr in result.file_results:
            vuln = fr.vulnerability
            if vuln and "score" in vuln:
                security_scores.append(vuln["score"])
            else:
                security_scores.append(70.0)  # 기본값

        result.security_score = sum(security_scores) / len(security_scores)

        # 코드 품질 점수
        quality_scores = [fr.quality_score for fr in result.file_results]
        result.quality_score = sum(quality_scores) / len(quality_scores)

        # 베스트 프랙티스 점수 (간단한 휴리스틱)
        result.best_practices_score = self._calculate_best_practices_score(result)

        # 복잡도 점수 (라인 수 기반 휴리스틱)
        result.complexity_score = self._calculate_complexity_score(result)

        # 문서화 점수 (간단한 휴리스틱)
        result.documentation_score = self._calculate_documentation_score(result)

        # 종합 점수 (가중 평균)
        # 보안 30%, 품질 25%, 베스트 프랙티스 20%, 복잡도 15%, 문서화 10%
        result.overall_score = (
            result.security_score * 0.30 +
            result.quality_score * 0.25 +
            result.best_practices_score * 0.20 +
            result.complexity_score * 0.15 +
            result.documentation_score * 0.10
        )

        # 레벨 계산
        result.level = self._calculate_level(result.overall_score)

    def _calculate_best_practices_score(self, result: RepositoryAnalysisResult) -> float:
        """베스트 프랙티스 점수"""
        score = 70.0

        # 이슈 수에 따른 감점
        total_issues = sum(len(fr.issues) for fr in result.file_results)
        issue_penalty = min(total_issues * 2, 30)
        score -= issue_penalty

        # 언어 다양성 (단일 언어 선호)
        if len(result.language_stats) == 1:
            score += 5

        return max(0, min(100, score))

    def _calculate_complexity_score(self, result: RepositoryAnalysisResult) -> float:
        """복잡도 점수 (낮은 복잡도 = 높은 점수)"""
        avg_lines_per_file = result.total_lines / max(result.total_files, 1)

        # 파일당 평균 라인 수 기준
        if avg_lines_per_file <= 100:
            return 90.0
        elif avg_lines_per_file <= 200:
            return 80.0
        elif avg_lines_per_file <= 300:
            return 70.0
        elif avg_lines_per_file <= 500:
            return 60.0
        else:
            return 50.0

    def _calculate_documentation_score(self, result: RepositoryAnalysisResult) -> float:
        """문서화 점수 (간단한 휴리스틱)"""
        # TODO: 실제 주석/문서 분석 구현
        return 65.0

    def _calculate_level(self, overall_score: float) -> int:
        """레벨 계산 (1-5)"""
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

    def _aggregate_issues(self, result: RepositoryAnalysisResult):
        """이슈 집계"""
        for fr in result.file_results:
            # 보안 이슈 (critical)
            if fr.vulnerability.get("vulnerable", False):
                confidence = fr.vulnerability.get("confidence", 0)
                if confidence > 0.8:
                    result.critical_issues.append(
                        f"{fr.file_path}: High-confidence security vulnerability"
                    )
                else:
                    result.warnings.append(
                        f"{fr.file_path}: Potential security issue"
                    )

            # 품질 이슈
            if fr.quality_score < 50:
                result.warnings.append(
                    f"{fr.file_path}: Low code quality score ({fr.quality_score:.1f})"
                )

            # 기타 이슈
            for issue in fr.issues:
                if "error" in issue.lower() or "bug" in issue.lower():
                    result.warnings.append(f"{fr.file_path}: {issue}")
                else:
                    result.suggestions.append(f"{fr.file_path}: {issue}")

        # 중복 제거 및 제한
        result.critical_issues = list(set(result.critical_issues))[:10]
        result.warnings = list(set(result.warnings))[:20]
        result.suggestions = list(set(result.suggestions))[:20]

    def get_scores_dict(self, result: RepositoryAnalysisResult) -> Dict[str, float]:
        """점수 딕셔너리 반환"""
        return {
            "overall": result.overall_score,
            "security": result.security_score,
            "quality": result.quality_score,
            "best_practices": result.best_practices_score,
            "complexity": result.complexity_score,
            "documentation": result.documentation_score,
        }

    def get_all_issues(self, result: RepositoryAnalysisResult) -> List[str]:
        """모든 이슈 목록"""
        return result.critical_issues + result.warnings + result.suggestions


# 전역 인스턴스
_orchestrator: Optional[AnalysisOrchestrator] = None


def get_orchestrator() -> AnalysisOrchestrator:
    """오케스트레이터 싱글톤"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AnalysisOrchestrator()
    return _orchestrator
