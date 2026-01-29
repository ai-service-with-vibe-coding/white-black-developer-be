# 흑백개발자 (White-Black Developer)

AI 기반 개발자 실력 평가 플랫폼 - "흑백요리사" 쉐프의 살벌한 코드 리뷰

## 프로젝트 개요

사용자가 GitHub에서 자신있는 프로젝트를 업로드하면, 여러 AI 모델로 코드를 다각도로 분석하여 1-5 레벨로 평가하고, "쉐프" 페르소나로 살벌하고 재미있는 리뷰를 제공합니다.

## 핵심 특징

- ✅ **완전 로컬 GPU 실행**: OpenAI API나 Hugging Face Inference API 사용 안 함 (비용 0원)
- 🚀 **다중 AI 모델 병렬 실행**: 코드 리뷰, 보안 분석, 복잡도 평가
- 🇰🇷 **한국어 LLM**: SOLAR-10.7B로 자연스러운 한국어 리뷰 생성
- 🎭 **독특한 페르소나**: "흑백요리사" 쉐프 말투 재현
- 📊 **5단계 레벨 시스템**: 객관적 가중치 기반 평가

## 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Cache/Queue**: Redis + Celery
- **Container**: Docker + Docker Compose (GPU 지원)

### AI/ML (GPU 필수)
- **Transformers**: Hugging Face Transformers (로컬 실행)
- **PyTorch**: CUDA 11.8+ 지원
- **Quantization**: bitsandbytes (4-bit 양자화)
- **GPU**: NVIDIA GPU, VRAM 12GB+ 권장

### 사용 모델
1. **microsoft/codereviewer** - 전반적 코드 리뷰
2. **mahdin70/codebert-devign-code-vulnerability-detector** - 보안 취약점 탐지
3. **beomi/OPEN-SOLAR-KO-10.7B** - 쉐프 페르소나 리뷰 생성

## 시스템 요구사항

### 최소 사양 (4-bit 양자화 사용)
- **GPU**: NVIDIA GPU (CUDA 지원)
- **VRAM**: 8GB (RTX 3060 12GB, RTX 3070 등)
- **RAM**: 16GB
- **저장공간**: 30GB

### 권장 사양
- **GPU**: NVIDIA RTX 3090, RTX 4080, A4000 등
- **VRAM**: 12GB+
- **RAM**: 32GB
- **저장공간**: 50GB

### 프로덕션 사양
- **GPU**: NVIDIA RTX 4090, A5000, A100 등
- **VRAM**: 24GB+
- **RAM**: 64GB
- **저장공간**: 100GB

## 빠른 시작

### 1. 사전 요구사항 확인

```bash
# GPU 확인
nvidia-smi

# CUDA 확인
nvcc --version

# Python 확인
python --version  # 3.11+
```

### 2. CUDA 및 PyTorch 설치

```bash
# PyTorch CUDA 11.8 버전 설치
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# CUDA 사용 가능 확인
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### 3. 프로젝트 설정

```bash
# 저장소 클론
git clone https://github.com/yourusername/white-black-developer-be.git
cd white-black-developer-be

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집
```

### 4. 데이터베이스 설정

```bash
# PostgreSQL 시작 (Docker 사용 시)
docker run -d --name postgres \
  -e POSTGRES_DB=whiteblack \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# 마이그레이션
alembic upgrade head
```

### 5. Redis 시작

```bash
# Redis 시작 (Docker 사용 시)
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 6. 애플리케이션 실행

```bash
# API 서버
uvicorn app.main:app --reload

# 별도 터미널에서 Celery Worker 실행 (GPU 필요)
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
```

### 7. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker로 실행 (권장)

### 1. NVIDIA Container Toolkit 설치

```bash
# Ubuntu
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi
```

### 2. Docker Compose 실행

```bash
# 전체 환경 실행 (API, PostgreSQL, Redis, Celery)
docker-compose up -d

# 로그 확인
docker-compose logs -f api
docker-compose logs -f celery_worker

# 종료
docker-compose down
```

## 환경 변수 설정

`.env` 파일 예시:

```bash
# App
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/whiteblack

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_CALLBACK_URL=http://localhost:8000/api/v1/auth/github/callback

# AI 모델 (로컬 GPU 실행)
CODE_REVIEWER_MODEL=microsoft/codereviewer
VULNERABILITY_DETECTOR_MODEL=mahdin70/codebert-devign-code-vulnerability-detector
PERSONA_MODEL=beomi/OPEN-SOLAR-KO-10.7B

# 모델 캐시 디렉토리
HF_HOME=./model_cache
TRANSFORMERS_CACHE=./model_cache

# GPU 설정
CUDA_VISIBLE_DEVICES=0

# JWT & Encryption
JWT_SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-32-bytes
```

**주의**: OpenAI API key나 Hugging Face API key는 필요하지 않습니다!

## API 사용 예시

### 1. GitHub OAuth 로그인

```bash
# 브라우저에서 접속
http://localhost:8000/api/v1/auth/github

# 콜백 후 JWT 토큰 받음
```

### 2. Repository 목록 조회

```bash
curl -X GET "http://localhost:8000/api/v1/github/repositories" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. 코드 분석 시작

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repository_id": "repo-uuid"}'

# 응답
{
  "id": "analysis-uuid",
  "status": "pending",
  "started_at": "2026-01-28T..."
}
```

### 4. 분석 진행 상황 조회

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/{analysis_id}/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 응답
{
  "status": "analyzing",
  "progress": 50,
  "started_at": "..."
}
```

### 5. 분석 결과 조회

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/{analysis_id}/result" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 응답
{
  "id": "result-uuid",
  "level": 3,
  "overall_score": 68.5,
  "security_score": 75.0,
  "quality_score": 70.0,
  "complexity_score": 65.0,
  "documentation_score": 50.0,
  "review_text": "코드의 완성도가 조금 모자라더라구요. 제가 제일 중요하게 생각하는 것은 코드의 모듈화 정도인 것 같아요...",
  "created_at": "..."
}
```

## 개발 가이드

### 프로젝트 구조

```
app/
├── main.py                  # FastAPI 진입점
├── config.py                # 설정 (Pydantic Settings)
├── api/v1/                  # API 라우터
├── db/models/               # SQLAlchemy 모델
├── schemas/                 # Pydantic 스키마
├── services/                # 비즈니스 로직
├── ai/                      # AI 모델 연동
│   ├── huggingface_client.py
│   ├── models/              # 모델 래퍼
│   │   ├── code_reviewer.py
│   │   ├── vulnerability_detector.py
│   │   └── persona_llm.py
│   ├── processors/          # 전처리, 오케스트레이터
│   └── prompts/             # 프롬프트
├── tasks/                   # Celery 작업
└── utils/                   # 유틸리티
```

### 주요 문서

- **CLAUDE.md**: Claude Code가 이 프로젝트를 작업할 때 참고하는 가이드
- **PRD.md**: 제품 요구사항 명세서
- **PROJECT_PLAN.md**: 상세 구현 계획 및 아키텍처
- **AI_MODELS.md**: AI 모델 상세 가이드 및 GPU 설정

### 테스트

```bash
# 전체 테스트
pytest

# 단위 테스트
pytest tests/unit

# 커버리지
pytest --cov=app --cov-report=html
```

### 코드 품질

```bash
# 포맷팅
black app/

# 린팅
flake8 app/

# 타입 체크
mypy app/
```

## GPU 모니터링

### 실시간 모니터링

```bash
# nvidia-smi 실시간 업데이트
watch -n 1 nvidia-smi

# Python에서 확인
python -c "import torch; print(f'VRAM: {torch.cuda.memory_allocated()/1024**3:.2f}GB')"
```

### API 엔드포인트

```bash
curl http://localhost:8000/api/v1/system/gpu/status
```

## 트러블슈팅

### CUDA Out of Memory

```python
# 해결 방법 1: GPU 캐시 클리어
import torch
torch.cuda.empty_cache()

# 해결 방법 2: Celery worker concurrency 줄이기
celery -A app.tasks.celery_app worker --concurrency=1

# 해결 방법 3: 더 작은 모델 사용
# PERSONA_MODEL=beomi/llama-2-ko-7b
```

### 모델 다운로드 실패

```bash
# 캐시 삭제 후 재시도
rm -rf ./model_cache/*
rm -rf ~/.cache/huggingface/*

# 직접 다운로드
huggingface-cli download beomi/OPEN-SOLAR-KO-10.7B
```

### Docker GPU 인식 안 됨

```bash
# NVIDIA Container Toolkit 설치 확인
dpkg -l | grep nvidia-container-toolkit

# Docker 재시작
sudo systemctl restart docker

# 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi
```

## 클라우드 배포 (GPU 인스턴스)

### AWS
- **g4dn.xlarge**: T4 GPU (16GB), ~$0.53/hour
- **g5.xlarge**: A10G GPU (24GB), ~$1.01/hour
- **p3.2xlarge**: V100 GPU (16GB), ~$3.06/hour

### GCP
- **n1-standard-4 + T4**: ~$0.60/hour
- **a2-highgpu-1g (A100 40GB)**: ~$3.67/hour

### Lambda Labs (저렴)
- **1x RTX 4090**: 24GB, $0.69/hour
- **1x A100**: 40GB, $1.10/hour

## 라이선스

MIT License

## 기여

이슈와 PR을 환영합니다!

## 문의

프로젝트 관련 문의는 이슈를 통해 부탁드립니다.

---

**Made with ❤️ and GPU 🔥**
