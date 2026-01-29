# AI 모델 가이드

이 문서는 흑백개발자 프로젝트에서 사용하는 AI 모델들의 상세 정보와 GPU 설정 가이드입니다.

## 사용 모델 목록

### 1. 코드 리뷰 모델
**microsoft/codereviewer**
- 용도: 전반적인 코드 리뷰
- 크기: ~1.5GB
- VRAM: ~2GB
- 특징: 코드 변경사항 및 리뷰 데이터로 학습

### 2. 보안 취약점 탐지
**mahdin70/codebert-devign-code-vulnerability-detector**
- 용도: 보안 취약점 자동 탐지
- 크기: ~500MB
- VRAM: ~1GB
- 특징: 이진 분류 (안전/취약)

### 3. 페르소나 생성 (한국어 LLM)
**beomi/Llama-3-Open-Ko-8B-Instruct-preview** (기본)
- 용도: 안성재 쉐프 스타일 리뷰 생성
- 크기: ~16GB (FP16)
- VRAM: ~8GB (FP16), ~3-4GB (4-bit NF4 양자화)
- 특징: Llama 3 기반, 한국어 성능 우수, `apply_chat_template()` 사용 필수

**대안 모델:**
- `beomi/OPEN-SOLAR-KO-10.7B` - VRAM 12GB+ 필요, 한국어 성능 우수
- `yanolja/EEVE-Korean-Instruct-10.8B-v1.0` - 야놀자, 최신
- `beomi/KoAlpaca-Polyglot-5.8B` - 경량 (VRAM 4GB)
- `maywell/Synatra-7B-v0.3-dpo` - 한국어 대화형

## GPU 메모리 요구사항

### 최소 사양 (4-bit NF4 양자화 사용)
- **VRAM**: 8GB (RTX 4070, RTX 3070 등)
- **RAM**: 16GB
- **저장공간**: 30GB

### 권장 사양
- **VRAM**: 12GB+ (RTX 3090, RTX 4080, A4000 등)
- **RAM**: 32GB
- **저장공간**: 50GB

### 프로덕션 사양
- **VRAM**: 24GB+ (RTX 4090, A5000, A100 등)
- **RAM**: 64GB
- **저장공간**: 100GB

### 현재 설정 기준 VRAM 사용량 (4-bit NF4)
| 모델 | VRAM 사용량 |
|------|------------|
| CodeReviewer | ~2GB |
| VulnerabilityDetector | ~1GB |
| PersonaLLM (Llama-3-8B) | ~3-4GB |
| **총합** | **~6-7GB** |

## 모델 메모리 최적화

### 1. 4-bit 양자화 (추천)
```python
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map="auto"
)
```

**효과**: 메모리 사용량 1/4로 감소 (12GB → 3GB)

### 2. 8-bit 양자화
```python
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_8bit=True,
    device_map="auto"
)
```

**효과**: 메모리 사용량 1/2로 감소 (12GB → 6GB)

### 3. FP16 (Half Precision)
```python
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)
```

**효과**: 메모리 사용량 1/2 + 추론 속도 향상

## CUDA 설치 가이드

### Windows
```bash
# CUDA Toolkit 11.8 설치
# https://developer.nvidia.com/cuda-11-8-0-download-archive

# cuDNN 설치
# https://developer.nvidia.com/cudnn

# 확인
nvidia-smi
nvcc --version
```

### Linux (Ubuntu)
```bash
# CUDA Toolkit 11.8
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run

# 환경 변수 설정
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 확인
nvidia-smi
nvcc --version
```

### PyTorch CUDA 설치
```bash
# CUDA 11.8
pip install torch==2.1.2 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 또는 CUDA 12.1
pip install torch==2.1.2 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 확인
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

## Docker GPU 설정

### NVIDIA Container Toolkit 설치

#### Ubuntu
```bash
# Repository 추가
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 설치
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Docker 재시작
sudo systemctl restart docker

# 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi
```

#### Windows (WSL2)
```bash
# WSL2에서 GPU 지원 확인
nvidia-smi

# Docker Desktop에서 GPU 설정 활성화
# Settings > Resources > WSL Integration > Enable GPU

# 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi
```

## 모델 다운로드 및 캐싱

### 자동 다운로드 (권장)
```python
# 첫 실행 시 자동으로 Hugging Face Hub에서 다운로드
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("beomi/Llama-3-Open-Ko-8B-Instruct-preview")
# ~/.cache/huggingface/hub/ 에 저장됨
```

### 수동 다운로드
```bash
# Hugging Face CLI 사용
pip install huggingface-hub

# 모델 다운로드
huggingface-cli download beomi/Llama-3-Open-Ko-8B-Instruct-preview \
  --local-dir ./model_cache/Llama-3-Ko-8B

# 환경 변수 설정
export HF_HOME=./model_cache
export TRANSFORMERS_CACHE=./model_cache
```

### 캐시 디렉토리 설정
```python
# app/config.py
class Settings(BaseSettings):
    HF_HOME: str = "./model_cache"
    TRANSFORMERS_CACHE: str = "./model_cache"
```

## 성능 벤치마크

### Llama-3-Open-Ko-8B (페르소나 LLM)
| 설정 | VRAM | 추론 시간 (256 토큰) |
|------|------|---------------------|
| FP16 | 8GB | ~10초 |
| 4-bit (NF4) | 3-4GB | ~15초 |

### SOLAR-10.7B (대안 모델)
| 설정 | VRAM | 추론 시간 (500 토큰) |
|------|------|---------------------|
| FP16 | 12GB | ~8초 |
| 4-bit (NF4) | 6GB | ~12초 |

### CodeReviewer
| 설정 | VRAM | 추론 시간 (512 토큰) |
|------|------|---------------------|
| FP32 | 4GB | ~2초 |
| FP16 | 2GB | ~1초 |

*벤치마크 환경: NVIDIA RTX 4070 8GB, CUDA 12.6*

## 트러블슈팅

### CUDA Out of Memory
```python
# 해결 방법 1: 양자화 사용
quantization_config = BitsAndBytesConfig(load_in_4bit=True)

# 해결 방법 2: GPU 캐시 클리어
import torch
torch.cuda.empty_cache()

# 해결 방법 3: 배치 크기 줄이기
# Celery worker concurrency 줄이기
celery -A app.tasks.celery_app worker --concurrency=1
```

### 느린 추론 속도
```python
# 해결 방법 1: FP16 사용
model = model.half()

# 해결 방법 2: Flash Attention 사용 (지원되는 모델)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    use_flash_attention_2=True
)

# 해결 방법 3: 작은 모델 사용
# Llama-3-8B → KoAlpaca-5.8B
```

### 모델 로드 실패
```bash
# 해결 방법 1: 캐시 삭제 후 재다운로드
rm -rf ~/.cache/huggingface/hub/

# 해결 방법 2: Git LFS 설치
git lfs install

# 해결 방법 3: 직접 다운로드
huggingface-cli download beomi/Llama-3-Open-Ko-8B-Instruct-preview
```

## Llama 3 Instruct 모델 사용법

### apply_chat_template 사용 (필수)
Llama 3 Instruct 모델은 반드시 `apply_chat_template()`을 사용해야 합니다:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "beomi/Llama-3-Open-Ko-8B-Instruct-preview"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")

messages = [
    {"role": "system", "content": "당신은 코드 심사위원입니다."},
    {"role": "user", "content": "이 코드를 평가해주세요."},
]

input_ids = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    return_tensors="pt"
).to(model.device)

# 종료 토큰 설정 (중요!)
terminators = [
    tokenizer.eos_token_id,
    tokenizer.convert_tokens_to_ids("<|eot_id|>")
]

outputs = model.generate(
    input_ids,
    max_new_tokens=256,
    eos_token_id=terminators,
    do_sample=True,
    temperature=0.7,
    top_p=0.9,
)

# 응답만 추출
response = tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
```

## 클라우드 GPU 옵션

### AWS
- **g4dn.xlarge**: T4 GPU (16GB), $0.526/hour
- **g5.xlarge**: A10G GPU (24GB), $1.006/hour
- **p3.2xlarge**: V100 GPU (16GB), $3.06/hour

### GCP
- **n1-standard-4 + T4**: T4 GPU (16GB), ~$0.60/hour
- **n1-standard-8 + V100**: V100 GPU (16GB), ~$2.50/hour
- **a2-highgpu-1g**: A100 GPU (40GB), ~$3.67/hour

### Lambda Labs (저렴한 대안)
- **1x RTX 4090**: 24GB, $0.69/hour
- **1x A100**: 40GB, $1.10/hour
- **1x H100**: 80GB, $1.99/hour

## 모니터링

### GPU 사용률 모니터링
```bash
# 실시간 모니터링
watch -n 1 nvidia-smi

# 로그 저장
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv -l 1 > gpu_log.csv
```

### Python 코드에서 모니터링
```python
# app/api/v1/system.py
from fastapi import APIRouter
import torch

router = APIRouter()

@router.get("/gpu/status")
async def get_gpu_status():
    if not torch.cuda.is_available():
        return {"error": "GPU not available"}

    return {
        "device_name": torch.cuda.get_device_name(0),
        "device_count": torch.cuda.device_count(),
        "memory_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.2f}GB",
        "memory_reserved": f"{torch.cuda.memory_reserved() / 1024**3:.2f}GB",
        "memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}GB",
    }
```

## 추가 참고 자료

- [Hugging Face Transformers 문서](https://huggingface.co/docs/transformers/)
- [bitsandbytes 양자화 가이드](https://huggingface.co/docs/transformers/main/en/quantization)
- [NVIDIA CUDA 설치 가이드](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/)
- [Docker GPU 지원 문서](https://docs.docker.com/config/containers/resource_constraints/#gpu)
