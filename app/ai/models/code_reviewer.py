"""
코드 품질 분석 모델 (Salesforce/codet5-base-multi-sum)
- 코드 요약 생성: CodeT5 모델 사용
- 품질 점수 계산: 정적 분석 기반
"""
from transformers import RobertaTokenizer, T5ForConditionalGeneration
import torch
import re
from typing import List, Dict
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CodeReviewerModel:
    """코드 품질 분석 모델"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.CODE_REVIEWER_MODEL
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if self.device == "cpu":
            logger.warning(
                "GPU not available. Model will run on CPU (very slow for large models)"
            )

        logger.info(f"Loading {self.model_name} on {self.device}...")

        try:
            # CodeT5는 RobertaTokenizer 사용
            self.tokenizer = RobertaTokenizer.from_pretrained(self.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
            )

            if self.device == "cpu":
                self.model = self.model.to(self.device)

            logger.info(f"✅ {self.model_name} loaded successfully")

            if self.device == "cuda":
                vram_usage = torch.cuda.memory_allocated() / 1024**3
                logger.info(f"VRAM usage: {vram_usage:.2f}GB")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def summarize(self, code: str, max_length: int = 512) -> str:
        """
        코드 요약 생성

        Args:
            code: 요약할 코드
            max_length: 최대 입력 길이

        Returns:
            코드 요약 텍스트
        """
        try:
            inputs = self.tokenizer(
                code,
                max_length=max_length,
                truncation=True,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=128,
                    num_beams=4,
                    early_stopping=True,
                )

            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return summary

        except Exception as e:
            logger.error(f"Error during code summarization: {e}")
            return f"Error: {str(e)}"

    def analyze(self, code: str, max_length: int = 512) -> str:
        """
        코드 분석 (summarize의 별칭, 하위 호환성 유지)
        """
        return self.summarize(code, max_length)

    def _calculate_static_metrics(self, code: str) -> Dict[str, float]:
        """
        정적 분석 기반 코드 메트릭 계산

        Args:
            code: 분석할 코드

        Returns:
            메트릭 딕셔너리
        """
        lines = code.split('\n')
        total_lines = len(lines)

        # 빈 줄 제외한 코드 라인
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        code_line_count = len(code_lines)

        # 주석 라인
        comment_lines = [l for l in lines if l.strip().startswith('#')]
        comment_count = len(comment_lines)

        # 함수 정의 수
        function_count = len(re.findall(r'\bdef\s+\w+\s*\(', code))

        # 클래스 정의 수
        class_count = len(re.findall(r'\bclass\s+\w+', code))

        # 평균 라인 길이
        avg_line_length = sum(len(l) for l in code_lines) / max(code_line_count, 1)

        # 최대 라인 길이
        max_line_length = max((len(l) for l in lines), default=0)

        # 중첩 깊이 (들여쓰기 기반 추정)
        indentation_levels = []
        for line in code_lines:
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                indentation_levels.append(indent // 4)  # 4칸 들여쓰기 기준
        max_nesting = max(indentation_levels, default=0)
        avg_nesting = sum(indentation_levels) / max(len(indentation_levels), 1)

        # import 문 수
        import_count = len(re.findall(r'^(?:from|import)\s+', code, re.MULTILINE))

        # try-except 블록 수
        try_except_count = len(re.findall(r'\btry\s*:', code))

        # 문서화 비율 (주석 + docstring)
        docstring_count = len(re.findall(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', code))
        documentation_ratio = (comment_count + docstring_count) / max(code_line_count, 1)

        return {
            "total_lines": total_lines,
            "code_lines": code_line_count,
            "comment_lines": comment_count,
            "function_count": function_count,
            "class_count": class_count,
            "avg_line_length": avg_line_length,
            "max_line_length": max_line_length,
            "max_nesting": max_nesting,
            "avg_nesting": avg_nesting,
            "import_count": import_count,
            "try_except_count": try_except_count,
            "documentation_ratio": documentation_ratio,
        }

    def _calculate_quality_score(self, metrics: Dict[str, float]) -> float:
        """
        메트릭 기반 품질 점수 계산 (0-100)

        Args:
            metrics: 정적 분석 메트릭

        Returns:
            품질 점수
        """
        score = 70.0  # 기본 점수

        # 1. 라인 길이 평가 (80자 이하 권장)
        if metrics["avg_line_length"] <= 80:
            score += 5.0
        elif metrics["avg_line_length"] > 120:
            score -= 10.0

        if metrics["max_line_length"] <= 120:
            score += 3.0
        elif metrics["max_line_length"] > 200:
            score -= 5.0

        # 2. 중첩 깊이 평가 (깊은 중첩은 감점)
        if metrics["max_nesting"] <= 3:
            score += 5.0
        elif metrics["max_nesting"] > 5:
            score -= 10.0

        if metrics["avg_nesting"] <= 1.5:
            score += 3.0
        elif metrics["avg_nesting"] > 3:
            score -= 5.0

        # 3. 문서화 비율 평가
        if metrics["documentation_ratio"] >= 0.1:
            score += 5.0
        elif metrics["documentation_ratio"] >= 0.05:
            score += 2.0
        elif metrics["documentation_ratio"] == 0:
            score -= 5.0

        # 4. 에러 처리 평가 (적절한 try-except 사용)
        if metrics["function_count"] > 0:
            error_handling_ratio = metrics["try_except_count"] / metrics["function_count"]
            if 0.1 <= error_handling_ratio <= 0.5:
                score += 3.0

        # 5. 코드 구조 평가 (함수/클래스 사용)
        if metrics["code_lines"] > 50:
            if metrics["function_count"] >= 2:
                score += 5.0
            elif metrics["function_count"] == 0:
                score -= 10.0

        # 점수 범위 제한
        return max(0.0, min(100.0, score))

    def get_quality_score(self, code: str) -> Dict[str, any]:
        """
        코드 품질 점수 및 요약 반환

        Args:
            code: 분석할 코드

        Returns:
            {
                "quality_score": float,
                "summary": str,
                "metrics": Dict
            }
        """
        # 코드 요약 생성
        summary = self.summarize(code)
        logger.info(f"코드 요약 결과 ::: {summary}")

        # 정적 분석 메트릭 계산
        metrics = self._calculate_static_metrics(code)
        logger.info(f"정적 분석 메트릭 ::: {metrics}")

        # 품질 점수 계산
        quality_score = self._calculate_quality_score(metrics)
        logger.info(f"품질 점수 ::: {quality_score}")

        return {
            "quality_score": quality_score,
            "summary": summary,
            "metrics": metrics,
            "review": summary,  # 하위 호환성
        }

    def analyze_batch(self, codes: List[str], max_length: int = 512) -> List[str]:
        """
        배치 코드 요약

        Args:
            codes: 요약할 코드 리스트
            max_length: 최대 입력 길이

        Returns:
            요약 텍스트 리스트
        """
        summaries = []
        for code in codes:
            summary = self.summarize(code, max_length)
            summaries.append(summary)
        return summaries
