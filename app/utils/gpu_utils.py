"""
GPU 유틸리티
"""
import torch
from typing import Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


def check_gpu_available() -> bool:
    """GPU 사용 가능 여부 확인"""
    available = torch.cuda.is_available()
    if available:
        logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        logger.info(
            f"Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}GB"
        )
    else:
        logger.warning("GPU not available! Models will run on CPU (very slow)")
    return available


def get_gpu_memory_info() -> Optional[Dict[str, str]]:
    """GPU 메모리 사용량 조회"""
    if not torch.cuda.is_available():
        return None

    return {
        "allocated": f"{torch.cuda.memory_allocated() / 1024**3:.2f}GB",
        "reserved": f"{torch.cuda.memory_reserved() / 1024**3:.2f}GB",
        "total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}GB",
        "free": f"{(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1024**3:.2f}GB",
    }


def clear_gpu_cache():
    """GPU 캐시 클리어"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("GPU cache cleared")


def get_device() -> str:
    """사용할 디바이스 반환"""
    return "cuda" if torch.cuda.is_available() else "cpu"
