# 흑백개발자 MVP 빠른 시작 가이드

이 가이드는 OAuth, DB 없이 **코드 분석 API만** 빠르게 실행하는 방법을 설명합니다.

## 요구사항

- Python 3.11+
- NVIDIA GPU (CUDA 11.8+)
- VRAM 12GB+ 권장 (최소 8GB)

## 설치

### uv 사용 시 (권장)

```bash
# 1. PyTorch CUDA 버전 설치 (먼저!)
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 2. 나머지 의존성 설치 (둘 중 하나 선택)
uv pip install -r requirements-mvp.txt   # MVP 최소 의존성
# 또는
uv pip install -r requirements.txt       # 전체 의존성
```

### pip 사용 시

```bash
# 1. 가상환경 생성
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 2. PyTorch CUDA 버전 설치 (먼저!)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. 나머지 의존성 설치
pip install -r requirements.txt
```

### PyTorch 설치 확인

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

CUDA가 `True`로 나와야 합니다. `False`면 CUDA 버전이 맞지 않는 것입니다.

### 4. 환경 변수 설정

```bash
# .env 파일 생성 (MVP 최소 설정)
cp .env.example .env
```

또는 직접 생성:

```bash
# .env
APP_NAME=White-Black Developer
DEBUG=true
LOG_LEVEL=INFO
CUDA_VISIBLE_DEVICES=0
HF_HOME=./model_cache
TRANSFORMERS_CACHE=./model_cache
```

## 실행

### 서버 시작

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 사용법

### 1. 헬스 체크

```bash
curl http://localhost:8000/api/v1/analysis/health
```

### 2. 모델 사전 로드 (선택사항)

첫 분석 요청 전에 모델을 미리 로드하면 응답 시간이 단축됩니다.

```bash
curl -X POST http://localhost:8000/api/v1/analysis/preload
```

### 3. 빠른 분석 (페르소나 리뷰 없음)

```bash
curl -X POST http://localhost:8000/api/v1/analysis/quick \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello, World!\")",
    "language": "python"
  }'
```

### 4. 전체 분석 (페르소나 리뷰 포함)

```bash
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello, World!\")",
    "language": "auto",
    "include_persona_review": true
  }'
```

## 응답 예시

```json
{
  "level": 3,
  "level_title": "중급 개발자",
  "verdict": "생존하셨습니다",
  "overall_score": 68.5,
  "scores": {
    "security": 75.0,
    "quality": 70.0,
    "best_practices": 65.0,
    "complexity": 80.0,
    "documentation": 50.0
  },
  "code_review": "The code is simple and readable...",
  "persona_review": "코드의 완성도가 조금 모자라더라구요...",
  "is_vulnerable": false,
  "vulnerability_score": 75.0,
  "issues": [],
  "suggestions": ["문서화 점수가 50점입니다..."],
  "language": "python",
  "line_count": 2
}
```

## Python 테스트

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/analysis/analyze",
    json={
        "code": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
""",
        "language": "python",
        "include_persona_review": True
    }
)

result = response.json()
print(f"레벨: {result['level']} ({result['level_title']})")
print(f"판정: {result['verdict']}")
print(f"점수: {result['overall_score']}")
print(f"\n안성재 쉐프 리뷰:\n{result['persona_review']}")
```

## 테스트 스크립트

```bash
# Import 검증
python scripts/verify_imports.py

# API 테스트 (서버 실행 후)
python scripts/test_api.py

# AI 모델 테스트
python scripts/test_ai_models.py
```

## GPU 메모리 부족 시

VRAM이 부족하면 다음을 시도하세요:

1. **다른 GPU 프로세스 종료**
   ```bash
   nvidia-smi  # GPU 사용 현황 확인
   ```

2. **더 작은 페르소나 모델 사용**
   `.env`에서 모델 변경:
   ```
   PERSONA_MODEL=beomi/llama-2-ko-7b
   ```

3. **페르소나 리뷰 비활성화**
   ```json
   {"include_persona_review": false}
   ```

## 지원 언어

- Python
- JavaScript / TypeScript
- Java
- Go
- Rust
- C / C++
- C#
- Ruby
- PHP
- Swift
- Kotlin
- Scala

`language: "auto"`로 설정하면 자동 감지됩니다.
