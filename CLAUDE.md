# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**흑백개발자 (White-Black Developer)** - AI 기반 개발자 실력 평가 플랫폼

이 프로젝트는 "흑백요리사"의 안성재 쉐프와 같은 살벌하고 직설적인 스타일로 개발자의 코드를 리뷰하고 레벨을 평가하는 백엔드 시스템입니다.

## Core Concept

1. 사용자가 GitHub 연동을 통해 자신있는 프로젝트를 업로드
2. Hugging Face AI 모델들로 다각도 코드 분석
3. 레벨 1-5로 평가
4. "안성재 쉐프" 페르소나로 살벌하고 재미있는 리뷰 생성

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Cache/Queue**: Redis + Celery
- **AI**: Hugging Face Transformers (GPU 로컬 추론, API 사용 안함)
- **GPU**: NVIDIA CUDA 11.8+, VRAM 12GB+ 권장
- **Auth**: GitHub OAuth 2.0 (Authlib) + JWT
- **Container**: Docker + Docker Compose (GPU 지원)

## Key Architecture Decisions

### GPU 기반 로컬 추론
FastAPI + Transformers를 사용하여 모든 AI 모델을 GPU에서 직접 실행합니다. API 비용 없이 완전 무료이며, 데이터 프라이버시가 보장됩니다. OpenAI API나 Hugging Face Inference API는 사용하지 않습니다.

### AI Model Pipeline
코드 분석은 여러 Hugging Face 모델을 GPU에서 병렬로 실행하여 다각도로 평가합니다:
- `microsoft/codereviewer`: 전반적 코드 리뷰 (~2GB VRAM)
- `mahdin70/codebert-devign-code-vulnerability-detector`: 보안 취약점 탐지 (~1GB VRAM)
- `beomi/OPEN-SOLAR-KO-10.7B`: 안성재 쉐프 페르소나 리뷰 생성 (~6GB VRAM, 4-bit 양자화)

모델은 `app/ai/huggingface_client.py`에서 로드하며, 메모리 효율을 위해 lru_cache로 싱글톤 패턴을 사용합니다. 4-bit 양자화(bitsandbytes)로 메모리 사용량을 1/4로 줄입니다.

### Async Processing with Celery
코드 분석은 시간이 오래 걸리므로 Celery 큐를 사용한 비동기 처리가 필수입니다. 분석 요청 시 Celery job을 생성하고, worker가 백그라운드에서 처리합니다. 진행 상황은 `task.update_state()`로 업데이트합니다.

### Scoring System
각 분석 결과는 가중치를 적용하여 종합 점수를 계산합니다:
- 보안 취약점: 30%
- 코드 품질: 25%
- 베스트 프랙티스: 20%
- 코드 복잡도: 15%
- 문서화: 10%

종합 점수를 기반으로 1-5 레벨로 변환합니다.

## Project Structure

```
app/
├── main.py                # FastAPI 애플리케이션 진입점
├── config.py              # Pydantic Settings 기반 설정
├── api/v1/                # API 라우터 (auth, github, analysis, reports)
├── db/models/             # SQLAlchemy 모델
├── schemas/               # Pydantic 스키마 (요청/응답 검증)
├── services/              # 비즈니스 로직
├── ai/                    # AI 모델 연동 및 분석 파이프라인
│   ├── huggingface_client.py
│   ├── models/            # 모델별 래퍼 클래스
│   ├── processors/        # 코드 전처리, 분석 오케스트레이터
│   └── prompts/           # 페르소나 프롬프트
├── tasks/                 # Celery 백그라운드 작업
├── core/                  # 핵심 기능 (security, oauth, rate_limiter)
└── utils/                 # 공통 유틸리티
```

FastAPI의 라우터는 `app/api/v1/`에 있으며, 각 라우터는 비즈니스 로직을 `app/services/`의 서비스 클래스에 위임합니다.

## Development Commands

```bash
# GPU 확인 (필수!)
nvidia-smi                  # GPU 상태 확인
python -c "import torch; print(torch.cuda.is_available())"  # PyTorch CUDA 확인

# 환경 설정
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate

# PyTorch CUDA 버전 설치 (먼저!)
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# 나머지 의존성 설치
pip install -r requirements.txt

# 데이터베이스
alembic revision --autogenerate -m "message"  # 마이그레이션 생성
alembic upgrade head        # 마이그레이션 적용
alembic downgrade -1        # 롤백

# 개발 서버
uvicorn app.main:app --reload  # Hot-reload 개발 서버 (http://localhost:8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000  # 프로덕션

# Celery (GPU 필요)
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2  # 워커
celery -A app.tasks.celery_app beat --loglevel=info    # 스케줄러
celery -A app.tasks.celery_app flower                  # 모니터링 UI

# GPU 모니터링
watch -n 1 nvidia-smi       # 실시간 GPU 사용률 확인

# 테스트
pytest                      # 전체 테스트
pytest tests/unit           # 단위 테스트
pytest --cov=app --cov-report=html  # 커버리지

# 코드 품질
black app/                  # 포맷팅 (PEP 8)
flake8 app/                 # 린팅
mypy app/                   # 타입 체크

# Docker (GPU 지원 필수)
# NVIDIA Container Toolkit 설치 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi

# 실행
docker-compose up           # 전체 환경 실행 (GPU 필요)
docker-compose up -d        # 백그라운드 실행
docker-compose down         # 종료
docker-compose logs -f api  # API 로그 확인
```

## Important Development Notes

### GitHub Token Security
GitHub access token은 반드시 `app/utils/encryption.py`의 `encrypt_token()`으로 암호화하여 DB에 저장해야 합니다. 사용 시 `decrypt_token()`으로 복호화합니다. `cryptography.fernet`을 사용합니다.

### Rate Limiting
- GitHub API: 시간당 5000 요청 제한 (인증 시)
- Hugging Face Inference API: 모델별 제한 있음
- Redis 캐싱을 적극 활용하여 API 호출을 최소화하세요.
- `app/core/rate_limiter.py`에서 클라이언트별 rate limiting 구현

### Error Handling
모든 외부 API 호출 (GitHub, Hugging Face)은 재시도 로직과 적절한 에러 처리가 필요합니다:
```python
try:
    result = await external_api_call()
except httpx.HTTPStatusError as e:
    logger.error(f"API error: {e}")
    raise HTTPException(status_code=502, detail="External service error")
```

분석 실패 시 `AnalysisStatus.FAILED`로 상태를 업데이트하고 에러 메시지를 저장하세요.

### Code Preprocessing
Repository 다운로드 후 분석 전에 반드시 전처리가 필요합니다 (`app/ai/processors/code_preprocessor.py`):
- `node_modules/`, `.git/`, `__pycache__/` 등 제외
- 대용량 파일 (1MB 이상) 필터링
- 바이너리 파일 제외 (.jpg, .png, .exe 등)
- 모델 입력 토큰 제한에 맞춰 청크 분할 (기본 2048 토큰)

### GPU Requirements
**필수 요구사항:**
- NVIDIA GPU (CUDA 지원)
- VRAM 12GB+ 권장 (최소 8GB, 4-bit 양자화 사용 시)
- CUDA 11.8 이상
- NVIDIA Driver 470.x 이상

**GPU 없이는 실행 불가**: 이 프로젝트는 GPU 기반 로컬 추론을 전제로 설계되었습니다. CPU만으로는 추론 시간이 너무 느립니다 (분 단위).

**GPU 메모리 최적화:**
- 4-bit 양자화 사용 (bitsandbytes)로 VRAM 사용량 1/4 감소
- `app/ai/models/persona_llm.py`에서 `BitsAndBytesConfig` 확인
- 메모리 부족 시 `torch.cuda.empty_cache()` 호출

### Persona Consistency
"안성재 쉐프" 페르소나는 일관성이 중요합니다:
- `app/ai/prompts/chef_ahn.py`의 `CHEF_AHN_SYSTEM_PROMPT` 사용
- 로컬 LLM (SOLAR-10.7B) temperature는 0.8로 설정 (창의적 응답)
- 레벨에 따라 톤 조절 (레벨 1-2: 엄격, 레벨 4-5: 격려)
- OpenAI API 대신 완전 로컬 실행

### Async/Await Pattern
FastAPI는 비동기를 지원하므로 I/O 바운드 작업 (DB 쿼리, API 호출)에는 `async`/`await`를 사용하세요:
```python
@router.get("/")
async def get_items(db: Session = Depends(get_db)):
    # 비동기 DB 쿼리
    items = await db.execute(select(Item))
    return items.scalars().all()
```

### Celery Task Design
Celery 작업은 상태 업데이트와 진행률 표시가 중요합니다:
```python
@celery_app.task(bind=True)
def analyze_task(self: Task, analysis_id: str):
    self.update_state(state="DOWNLOADING", meta={"progress": 10})
    # 작업 수행
    self.update_state(state="ANALYZING", meta={"progress": 50})
    # ...
```

## Testing Strategy

- **Unit Tests**: 각 service 로직 테스트, Mock으로 외부 의존성 제거
- **Integration Tests**: API 엔드포인트 테스트, `TestClient` 사용
- **E2E Tests**: 전체 플로우 테스트 (OAuth → 분석 → 결과)

Hugging Face 모델은 테스트에서 Mock을 사용하여 속도와 비용을 절약하세요:
```python
@pytest.fixture
def mock_hf_client(monkeypatch):
    def mock_analyze(code):
        return "Mock review result"
    monkeypatch.setattr("app.ai.models.code_reviewer.CodeReviewerModel.analyze", mock_analyze)
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/whiteblack

# Redis & Celery
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# GitHub OAuth
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_CALLBACK_URL=http://localhost:8000/api/v1/auth/github/callback

# AI 모델 설정 (로컬 GPU 실행, API 키 불필요)
CODE_REVIEWER_MODEL=microsoft/codereviewer
VULNERABILITY_DETECTOR_MODEL=mahdin70/codebert-devign-code-vulnerability-detector
PERSONA_MODEL=beomi/OPEN-SOLAR-KO-10.7B

# 모델 캐시 디렉토리
HF_HOME=./model_cache
TRANSFORMERS_CACHE=./model_cache

# GPU 설정
CUDA_VISIBLE_DEVICES=0  # 사용할 GPU ID (0, 1, 2...)

# JWT & Encryption
JWT_SECRET_KEY=...
ENCRYPTION_KEY=...  # 32 bytes for Fernet
```

`.env.example` 파일을 참고하세요. `app/config.py`에서 Pydantic Settings로 자동 로드됩니다.

**주의**: OpenAI API key나 Hugging Face API key는 필요하지 않습니다. 모든 모델을 로컬 GPU에서 직접 실행합니다.

## Key Files to Review

- `PRD.md`: 전체 프로젝트 요구사항 및 기능 명세
- `PROJECT_PLAN.md`: 상세 구현 계획 및 아키텍처
- `AI_MODELS.md`: **AI 모델 상세 가이드 및 GPU 설정** (중요!)
- `app/main.py`: FastAPI 애플리케이션 진입점
- `app/api/v1/analysis.py`: 코드 분석 API 라우터
- `app/tasks/analysis_tasks.py`: Celery 백그라운드 작업
- `app/ai/huggingface_client.py`: GPU 모델 로드 및 캐싱
- `app/ai/models/persona_llm.py`: 한국어 LLM (페르소나 생성)
- `app/ai/models/code_reviewer.py`: 코드 리뷰 모델
- `app/ai/prompts/chef_ahn.py`: 페르소나 프롬프트

## Common Patterns

### Dependency Injection
FastAPI의 `Depends()`를 사용하여 의존성 주입:
```python
from fastapi import Depends
from app.db.session import get_db

@router.get("/")
async def endpoint(db: Session = Depends(get_db)):
    # db 사용
```

### Pydantic Validation
요청/응답 검증은 Pydantic 스키마로:
```python
from pydantic import BaseModel, Field

class AnalysisCreate(BaseModel):
    repository_id: str = Field(..., min_length=1)
```

### SQLAlchemy Queries
SQLAlchemy 2.0 스타일 사용:
```python
from sqlalchemy import select
from app.db.models.user import User

result = await db.execute(select(User).where(User.github_id == github_id))
user = result.scalar_one_or_none()
```

## API Documentation

FastAPI는 자동으로 API 문서를 생성합니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Test Scripts

프로젝트 루트의 `scripts/` 디렉토리에 테스트 및 검증 스크립트가 있습니다:

```bash
# Import 검증 (모든 모듈이 정상적으로 import 되는지 확인)
python scripts/verify_imports.py

# AI 모델 테스트 (GPU 상태, 개별 모델 테스트)
python scripts/test_ai_models.py

# 전체 분석 파이프라인 데모 (현재 프로젝트를 분석)
python scripts/demo_analysis.py
```

## Current Implementation Status

**완료된 기능:**
- ✅ AI 모델 통합 (CodeReviewer, VulnerabilityDetector, PersonaLLM)
- ✅ HuggingFaceClient 싱글톤 패턴 (lazy loading)
- ✅ 코드 전처리기 (CodePreprocessor)
- ✅ 분석 오케스트레이터 (AnalysisOrchestrator)
- ✅ 점수 계산 서비스 (ScoringService)
- ✅ 페르소나 리뷰 서비스 (PersonaService)
- ✅ 통합 분석 서비스 (AnalysisService)
- ✅ 데이터베이스 모델 (User, Repository, Analysis, AnalysisResult)
- ✅ GPU 유틸리티 및 로거

**구현 예정:**
- ⬜ GitHub OAuth 인증 (Option 1)
- ⬜ GitHub 저장소 연동 (Option 3)
- ⬜ Celery 백그라운드 작업 (Option 4)
- ⬜ API 라우터 구현
- ⬜ Pydantic 스키마

## External API References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [GitHub REST API](https://docs.github.com/en/rest)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
