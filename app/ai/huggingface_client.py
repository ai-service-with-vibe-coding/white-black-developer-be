"""
Hugging Face 모델 클라이언트 (싱글톤)
모든 AI 모델을 로드하고 캐싱
"""
from functools import lru_cache
import torch
from typing import Optional
from app.ai.models.code_reviewer import CodeReviewerModel
from app.ai.models.vulnerability_detector import VulnerabilityDetector
from app.ai.models.persona_llm import PersonaLLM
from app.utils.logger import get_logger
from app.utils.gpu_utils import check_gpu_available, get_gpu_memory_info

logger = get_logger(__name__)


class HuggingFaceClient:
    """
    모델 로드 및 캐싱 관리 (GPU 싱글톤)

    모든 모델은 lazy loading으로 처음 사용 시에만 로드됩니다.
    """

    def __init__(self):
        self._models = {}
        self._check_gpu()

    def _check_gpu(self):
        """GPU 사용 가능 여부 확인"""
        if not torch.cuda.is_available():
            logger.error("=" * 80)
            logger.error("GPU is NOT available!")
            logger.error(
                "This application requires NVIDIA GPU with CUDA support."
            )
            logger.error("Please check:")
            logger.error("  1. NVIDIA GPU is installed")
            logger.error("  2. CUDA drivers are installed (nvidia-smi works)")
            logger.error("  3. PyTorch with CUDA is installed correctly")
            logger.error("=" * 80)
            raise RuntimeError("GPU is required but not available")

        logger.info("=" * 80)
        logger.info("GPU Status:")
        logger.info(f"  Device: {torch.cuda.get_device_name(0)}")
        logger.info(
            f"  Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}GB"
        )
        logger.info("=" * 80)

    @lru_cache(maxsize=1)
    def get_code_reviewer(self) -> CodeReviewerModel:
        """
        코드 리뷰 모델 가져오기 (Lazy Loading)

        Returns:
            CodeReviewerModel 인스턴스
        """
        if "code_reviewer" not in self._models:
            logger.info("Loading Code Reviewer model...")
            self._models["code_reviewer"] = CodeReviewerModel()
            self._log_memory_usage()

        return self._models["code_reviewer"]

    @lru_cache(maxsize=1)
    def get_vulnerability_detector(self) -> VulnerabilityDetector:
        """
        취약점 탐지 모델 가져오기 (Lazy Loading)

        Returns:
            VulnerabilityDetector 인스턴스
        """
        if "vulnerability_detector" not in self._models:
            logger.info("Loading Vulnerability Detector model...")
            self._models["vulnerability_detector"] = VulnerabilityDetector()
            self._log_memory_usage()

        return self._models["vulnerability_detector"]

    @lru_cache(maxsize=1)
    def get_persona_llm(self) -> PersonaLLM:
        """
        페르소나 LLM 가져오기 (Lazy Loading)

        Returns:
            PersonaLLM 인스턴스
        """
        if "persona_llm" not in self._models:
            logger.info("Loading Persona LLM (SOLAR-10.7B)...")
            logger.info("This is the largest model and may take several minutes on first run...")
            self._models["persona_llm"] = PersonaLLM()
            self._log_memory_usage()

        return self._models["persona_llm"]

    def _log_memory_usage(self):
        """GPU 메모리 사용량 로그"""
        memory_info = get_gpu_memory_info()
        if memory_info:
            logger.info(f"GPU Memory - Allocated: {memory_info['allocated']}, Free: {memory_info['free']}")

    def preload_all_models(self):
        """
        모든 모델을 미리 로드 (선택사항)

        애플리케이션 시작 시 호출하여 첫 요청의 대기 시간을 줄일 수 있습니다.
        """
        logger.info("Preloading all models...")

        try:
            self.get_code_reviewer()
            logger.info("✅ Code Reviewer loaded")

            self.get_vulnerability_detector()
            logger.info("✅ Vulnerability Detector loaded")

            self.get_persona_llm()
            logger.info("✅ Persona LLM loaded")

            logger.info("=" * 80)
            logger.info("All models loaded successfully!")
            memory_info = get_gpu_memory_info()
            if memory_info:
                logger.info(f"Total GPU Memory Usage: {memory_info['allocated']}")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Failed to preload models: {e}")
            raise

    def get_loaded_models(self) -> list:
        """
        현재 로드된 모델 목록 반환

        Returns:
            로드된 모델 이름 리스트
        """
        return list(self._models.keys())

    def clear_cache(self):
        """
        GPU 캐시 클리어 (메모리 정리)
        """
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU cache cleared")


# 싱글톤 인스턴스
_hf_client_instance: Optional[HuggingFaceClient] = None


def get_hf_client() -> HuggingFaceClient:
    """
    Hugging Face 클라이언트 싱글톤 가져오기

    Returns:
        HuggingFaceClient 인스턴스
    """
    global _hf_client_instance

    if _hf_client_instance is None:
        logger.info("Initializing Hugging Face Client...")
        _hf_client_instance = HuggingFaceClient()

    return _hf_client_instance


# 편의를 위한 전역 인스턴스
hf_client = None  # get_hf_client()는 필요할 때 호출
