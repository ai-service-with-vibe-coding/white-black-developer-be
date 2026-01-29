# NVIDIA CUDA 베이스 이미지 사용
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Python 3.11 설치
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    gcc \
    g++ \
    postgresql-client \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11을 기본으로 설정
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app

# pip 업그레이드
RUN pip install --upgrade pip

# PyTorch CUDA 버전 먼저 설치
RUN pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# 나머지 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY ./app ./app
COPY ./alembic ./alembic
COPY alembic.ini ./

# 모델 캐시 디렉토리 생성
RUN mkdir -p /app/model_cache

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
