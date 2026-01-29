#!/bin/bash
# 프로젝트 초기 설정 스크립트

set -e

echo "🚀 흑백개발자 백엔드 설정 시작..."

# 1. GPU 확인
echo ""
echo "📊 GPU 확인 중..."
nvidia-smi || echo "⚠️  GPU를 찾을 수 없습니다. CPU 모드로 실행됩니다 (느림)."

# 2. Python 버전 확인
echo ""
echo "🐍 Python 버전 확인..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# 3. 가상환경 생성
echo ""
echo "📦 가상환경 생성 중..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "ℹ️  가상환경이 이미 존재합니다."
fi

# 4. 가상환경 활성화
echo ""
echo "🔄 가상환경 활성화..."
source venv/bin/activate

# 5. pip 업그레이드
echo ""
echo "⬆️  pip 업그레이드..."
pip install --upgrade pip

# 6. PyTorch CUDA 설치
echo ""
echo "🔥 PyTorch CUDA 설치 중..."
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# 7. CUDA 확인
echo ""
echo "✅ CUDA 사용 가능 여부 확인..."
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
python -c "import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

# 8. 의존성 설치
echo ""
echo "📚 의존성 설치 중..."
pip install -r requirements.txt

# 9. .env 파일 생성
echo ""
if [ ! -f ".env" ]; then
    echo "📝 .env 파일 생성 중..."
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다. 설정을 수정해주세요."
    echo ""
    echo "⚠️  필수 설정 항목:"
    echo "   - DATABASE_URL"
    echo "   - GITHUB_CLIENT_ID"
    echo "   - GITHUB_CLIENT_SECRET"
    echo "   - JWT_SECRET_KEY"
    echo "   - ENCRYPTION_KEY"
else
    echo "ℹ️  .env 파일이 이미 존재합니다."
fi

# 10. 모델 캐시 디렉토리 생성
echo ""
echo "📁 모델 캐시 디렉토리 생성..."
mkdir -p model_cache
echo "✅ 모델 캐시 디렉토리 생성 완료"

echo ""
echo "✨ 설정 완료!"
echo ""
echo "다음 단계:"
echo "1. .env 파일을 수정하세요"
echo "2. PostgreSQL과 Redis를 시작하세요:"
echo "   docker run -d --name postgres -e POSTGRES_DB=whiteblack -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15"
echo "   docker run -d --name redis -p 6379:6379 redis:7-alpine"
echo "3. 데이터베이스 마이그레이션을 실행하세요:"
echo "   alembic upgrade head"
echo "4. 서버를 시작하세요:"
echo "   uvicorn app.main:app --reload"
echo ""
