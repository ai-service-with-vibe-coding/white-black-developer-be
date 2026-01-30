"""
페르소나 생성 LLM (beomi/OPEN-SOLAR-KO-10.7B)
안성재 쉐프 스타일 리뷰 생성
"""
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TextStreamer, TextIteratorStreamer
import torch
from typing import Optional, Iterator
from threading import Thread
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 오프로드 폴더 생성
OFFLOAD_FOLDER = "./offload"
os.makedirs(OFFLOAD_FOLDER, exist_ok=True)


class PersonaLLM:
    """한국어 LLM으로 안성재 쉐프 페르소나 생성"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.PERSONA_MODEL
        self.device = "cuda"

        if not torch.cuda.is_available():
            raise RuntimeError(
                "GPU is required for PersonaLLM. Please ensure CUDA is available."
            )

        # GPU VRAM 확인
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        available_memory = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1024**3
        logger.info(f"GPU Total VRAM: {gpu_memory:.2f}GB, Available: {available_memory:.2f}GB")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # pad_token 설정
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # 로딩 시도 순서: 8-bit → FP16 → FP32
        self.model = None

        # 방법 1: 4-bit 양자화 시도 (VRAM 효율 최대화)
        if self.model is None:
            self.model = self._try_load_4bit(available_memory)

        # 방법 2: FP16 시도
        if self.model is None:
            self.model = self._try_load_fp16(available_memory)

        # 방법 3: FP32 시도 (최후의 수단)
        if self.model is None:
            self.model = self._try_load_fp32()

        if self.model is None:
            raise RuntimeError("Failed to load model with any method")

        vram_usage = torch.cuda.memory_allocated() / 1024**3
        logger.info(f"Final VRAM usage: {vram_usage:.2f}GB")

    def _try_load_4bit(self, available_memory: float):
        """4-bit 양자화로 로드 시도 (VRAM 효율 최대화)"""
        logger.info(f"Trying to load {self.model_name} with 4-bit quantization...")

        try:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )

            max_memory = {
                0: f"{int(available_memory * 0.85)}GB",
                "cpu": "24GB"
            }

            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                max_memory=max_memory,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                offload_folder=OFFLOAD_FOLDER,
            )

            logger.info(f"✅ {self.model_name} loaded with 4-bit quantization")
            return model

        except Exception as e:
            logger.warning(f"4-bit loading failed: {e}")
            return None

    def _try_load_fp16(self, available_memory: float):
        """FP16으로 로드 시도"""
        logger.info(f"Trying to load {self.model_name} with FP16...")

        try:
            max_memory = {
                0: f"{int(available_memory * 0.85)}GB",
                "cpu": "24GB"
            }

            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                max_memory=max_memory,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                offload_folder=OFFLOAD_FOLDER,
            )

            logger.info(f"✅ {self.model_name} loaded with FP16")
            return model

        except Exception as e:
            logger.warning(f"FP16 loading failed: {e}")
            return None

    def _try_load_fp32(self):
        """FP32로 로드 시도 (최후의 수단)"""
        logger.info(f"Trying to load {self.model_name} with FP32 (CPU offload)...")

        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                offload_folder=OFFLOAD_FOLDER,
            )

            logger.info(f"✅ {self.model_name} loaded with FP32")
            return model

        except Exception as e:
            logger.error(f"FP32 loading failed: {e}")
            return None

    def generate_review(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = True,
    ) -> str:
        """
        리뷰 생성 (Llama 3 Instruct 공식 사용법)

        Args:
            system_prompt: 시스템 프롬프트 (페르소나 정의)
            user_prompt: 사용자 프롬프트 (평가 결과)
            max_new_tokens: 생성할 최대 토큰 수
            temperature: 생성 온도 (높을수록 창의적)

        Returns:
            생성된 리뷰 텍스트
        """
        try:
            logger.info("Generating review with persona LLM...")

            # Llama 3 Instruct 공식 메시지 형식
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # 모델 디바이스 찾기 (4-bit 양자화 모델 호환)
            device = next(self.model.parameters()).device
            logger.info(f"Model device: {device}")

            # apply_chat_template 사용 (공식 방식)
            input_ids = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt"
            )

            # 텐서로 변환 및 디바이스 이동
            if not isinstance(input_ids, torch.Tensor):
                input_ids = input_ids["input_ids"]
            input_ids = input_ids.to(device)

            input_length = input_ids.shape[1]
            logger.info(f"Input tokens: {input_length}, max_new_tokens: {max_new_tokens}")

            # 종료 토큰 설정 (중요!)
            terminators = [self.tokenizer.eos_token_id]
            eot_id = self.tokenizer.convert_tokens_to_ids("<|eot_id|>")
            if eot_id is not None and eot_id != self.tokenizer.unk_token_id:
                terminators.append(eot_id)
            logger.info(f"Terminators: {terminators}")

            # 실시간 스트리밍 출력 설정
            streamer = None
            if stream:
                streamer = TextStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
                logger.info("Starting generation (streaming enabled)...")

            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    max_new_tokens=max_new_tokens,
                    eos_token_id=terminators,
                    do_sample=True,
                    temperature=temperature,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.pad_token_id,
                    streamer=streamer,
                )

            # 응답만 추출 (입력 부분 제외)
            response_ids = outputs[0][input_length:]
            response = self.tokenizer.decode(response_ids, skip_special_tokens=True)
            response = response.strip()

            logger.info(f"Review generated ({len(response)} characters)")

            return response

        except Exception as e:
            import traceback
            logger.error(f"Error during review generation: {type(e).__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return "리뷰 생성 중 오류가 발생했습니다. 다시 시도해주세요."

    def generate_simple(self, prompt: str, max_new_tokens: int = 500) -> str:
        """
        간단한 텍스트 생성 (시스템 프롬프트 없이)

        Args:
            prompt: 프롬프트
            max_new_tokens: 생성할 최대 토큰 수

        Returns:
            생성된 텍스트
        """
        try:
            first_param_device = next(self.model.parameters()).device

            inputs = self.tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=2048
            ).to(first_param_device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=0.8,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response

        except Exception as e:
            logger.error(f"Error during text generation: {e}")
            return f"Error: {str(e)}"
