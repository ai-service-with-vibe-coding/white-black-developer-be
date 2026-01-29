"""
코드 리뷰 모델 (microsoft/codereviewer)
"""
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from typing import List, Dict
from app.config import settings
from app.utils.logger import get_logger
from app.utils.gpu_utils import check_gpu_available

logger = get_logger(__name__)


class CodeReviewerModel:
    """코드 리뷰 모델"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.CODE_REVIEWER_MODEL
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if self.device == "cpu":
            logger.warning(
                "GPU not available. Model will run on CPU (very slow for large models)"
            )

        logger.info(f"Loading {self.model_name} on {self.device}...")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
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

    def analyze(self, code: str, max_length: int = 512) -> str:
        """
        코드 리뷰 수행

        Args:
            code: 리뷰할 코드
            max_length: 최대 입력 길이

        Returns:
            리뷰 텍스트
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
                    max_length=512,
                    num_beams=5,
                    early_stopping=True,
                    temperature=0.7,
                )

            review = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return review

        except Exception as e:
            logger.error(f"Error during code review: {e}")
            return f"Error: {str(e)}"

    def analyze_batch(self, codes: List[str], max_length: int = 512) -> List[str]:
        """
        배치 코드 리뷰

        Args:
            codes: 리뷰할 코드 리스트
            max_length: 최대 입력 길이

        Returns:
            리뷰 텍스트 리스트
        """
        reviews = []
        for code in codes:
            review = self.analyze(code, max_length)
            reviews.append(review)
        return reviews

    def get_quality_score(self, code: str) -> Dict[str, float]:
        """
        코드 품질 점수 (0-100)

        실제로는 모델의 출력을 분석하여 점수를 계산해야 하지만,
        여기서는 단순화된 버전을 제공합니다.
        """
        review = self.analyze(code)

        # 간단한 휴리스틱: 리뷰 길이와 긍정적 키워드 기반 점수
        score = 70.0  # 기본 점수

        positive_keywords = ["good", "well", "clean", "organized", "efficient"]
        negative_keywords = ["issue", "problem", "error", "bug", "fix", "improve"]

        review_lower = review.lower()

        for keyword in positive_keywords:
            if keyword in review_lower:
                score += 2.0

        for keyword in negative_keywords:
            if keyword in review_lower:
                score -= 3.0

        # 점수 범위 제한
        score = max(0.0, min(100.0, score))

        return {
            "quality_score": score,
            "review": review,
        }
