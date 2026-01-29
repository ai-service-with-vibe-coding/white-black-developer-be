# 빠른 시작 가이드

Transformers 라이브러리로 GPU에서 직접 모델을 실행하는 방법

## ✅ 사전 체크리스트

### 1. GPU 확인

```bash
nvidia-smi
```

출력 예시:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 525.78       Driver Version: 525.78       CUDA Version: 12.0     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ... Off  | 00000000:01:00.0  On |                  N/A |
| 30%   42C    P8    15W / 350W |    500MiB / 24576MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

**필요한 것:**
- VRAM: 최소 8GB, 권장 12GB+
- CUDA Version: 11.8 이상

### 2. CUDA 설치 확인

```bash
nvcc --version
```

없다면:
- **Windows**: https://developer.nvidia.com/cuda-11-8-0-download-archive
- **Linux**: `sudo apt install nvidia-cuda-toolkit`

## 📦 설치 (10분)

### Step 1: Python 환경 설정

```bash
# Python 3.11+ 확인
python --version

# 가상환경 생성
python -m venv venv

# 활성화
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### Step 2: PyTorch CUDA 먼저 설치 (중요!)

```bash
# CUDA 11.8 버전 (권장)
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# 확인
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
python -c "import torch; print('GPU:', torch.cuda.get_device_name(0))"
```

출력이 `CUDA available: True`이어야 합니다!

### Step 3: 나머지 의존성 설치

```bash
pip install -r requirements.txt
```

## 🗄️ 데이터베이스 설정 (5분)

### Option 1: Docker 사용 (추천)

```bash
# PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_DB=whiteblack \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### Option 2: 로컬 설치

```bash
# Ubuntu
sudo apt install postgresql redis-server

# macOS
brew install postgresql redis
brew services start postgresql
brew services start redis
```

### 데이터베이스 마이그레이션

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (DATABASE_URL 등)

# 마이그레이션 실행
alembic upgrade head
```

## 🔑 GitHub OAuth 설정 (3분)

1. https://github.com/settings/developers 접속
2. "New OAuth App" 클릭
3. 정보 입력:
   - Application name: `White-Black Developer (Local)`
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL: `http://localhost:8000/api/v1/auth/github/callback`
4. Client ID와 Client Secret을 `.env` 파일에 복사

```bash
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
```

## 🚀 실행 (2분)

### Terminal 1: API 서버

```bash
uvicorn app.main:app --reload
```

출력:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Celery Worker (GPU 필요!)

```bash
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
```

출력에서 GPU 감지 확인:
```
GPU detected: NVIDIA GeForce RTX 4090
Total VRAM: 24.00GB
Loading microsoft/codereviewer on cuda...
Model loaded successfully. VRAM usage: 1.85GB
Loading beomi/OPEN-SOLAR-KO-10.7B with 4-bit quantization...
Model loaded. VRAM usage: 7.92GB
```

## ✅ 테스트

### 1. API 문서 확인

브라우저에서 http://localhost:8000/docs 접속

### 2. GPU 상태 확인

```bash
curl http://localhost:8000/api/v1/system/gpu/status
```

응답 예시:
```json
{
  "device_name": "NVIDIA GeForce RTX 4090",
  "device_count": 1,
  "memory_allocated": "7.92GB",
  "memory_reserved": "8.50GB",
  "memory_total": "24.00GB"
}
```

### 3. 헬스체크

```bash
curl http://localhost:8000/health
```

## 🎯 첫 코드 분석 실행

### 1. GitHub 로그인

브라우저에서 http://localhost:8000/api/v1/auth/github 접속

### 2. 토큰 복사

로그인 후 받은 JWT 토큰을 복사

### 3. Repository 목록 조회

```bash
export TOKEN="your_jwt_token_here"

curl -X GET "http://localhost:8000/api/v1/github/repositories" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. 코드 분석 시작

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repository_id": "your-repo-id"}'
```

응답:
```json
{
  "id": "analysis-123",
  "status": "pending",
  "started_at": "2026-01-28T12:00:00"
}
```

### 5. 결과 조회 (약 3-5분 소요)

```bash
# 진행 상황
curl "http://localhost:8000/api/v1/analysis/analysis-123/status" \
  -H "Authorization: Bearer $TOKEN"

# 완료 후 결과
curl "http://localhost:8000/api/v1/analysis/analysis-123/result" \
  -H "Authorization: Bearer $TOKEN"
```

## 🐛 트러블슈팅

### CUDA Out of Memory

```bash
# GPU 캐시 클리어
python -c "import torch; torch.cuda.empty_cache()"

# Celery worker concurrency 줄이기
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1

# 더 작은 모델 사용
# .env 파일에서 PERSONA_MODEL 변경
PERSONA_MODEL=beomi/llama-2-ko-7b
```

### "CUDA not available"

```bash
# PyTorch 재설치
pip uninstall torch
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# 확인
python -c "import torch; print(torch.cuda.is_available())"
```

### 모델 다운로드 느림

첫 실행 시 모델을 Hugging Face Hub에서 다운로드합니다 (총 ~25GB).
- 빠른 인터넷 연결 필요
- 진행 상황은 터미널에 표시됨
- 캐시 위치: `./model_cache/` 또는 `~/.cache/huggingface/`

### Celery worker 시작 안 됨

```bash
# Redis 연결 확인
redis-cli ping  # 응답: PONG

# 데이터베이스 연결 확인
psql -h localhost -U postgres -d whiteblack -c "SELECT 1"

# 환경 변수 확인
echo $CELERY_BROKER_URL
```

## 📊 GPU 모니터링

### 실시간 모니터링

```bash
# Terminal에서 실시간 업데이트
watch -n 1 nvidia-smi

# 또는 간단한 스크립트
while true; do clear; nvidia-smi; sleep 1; done
```

### 로그 파일로 저장

```bash
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total \
  --format=csv -l 1 > gpu_usage.csv
```

## 🐳 Docker로 실행 (대안)

### 1. NVIDIA Container Toolkit 설치

```bash
# Ubuntu
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. Docker Compose 실행

```bash
# 환경 변수 설정
cp .env.example .env
# .env 편집

# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f api
docker-compose logs -f celery_worker
```

## 📚 다음 단계

- `PRD.md` - 전체 프로젝트 요구사항
- `PROJECT_PLAN.md` - 상세 구현 계획
- `AI_MODELS.md` - AI 모델 가이드
- `CLAUDE.md` - 개발 가이드
- API 문서: http://localhost:8000/docs

## ❓ 도움이 필요하면

1. GitHub Issues에 문의
2. 로그 파일 첨부: `docker-compose logs > logs.txt`
3. GPU 정보 첨부: `nvidia-smi > gpu_info.txt`

---

**Happy Coding! 🚀**
