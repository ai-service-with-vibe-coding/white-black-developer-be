# AWS EC2 GPU 배포 가이드

이 문서는 흑백개발자 백엔드를 AWS EC2 GPU 인스턴스에 배포하는 방법을 설명합니다.

## MVP 배포 (가장 간단)

MVP는 DB/Redis 없이 API 서버만 실행합니다.

```bash
# EC2 접속 후
git clone <your-repo>
cd white-black-developer-be

# 초기 설정 (GPU 드라이버, Docker)
chmod +x scripts/aws-ec2-setup.sh
sudo ./scripts/aws-ec2-setup.sh

# 재접속 후 실행
docker compose -f docker-compose.mvp.yml up -d

# 확인
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

**MVP 구성:**
- API 서버만 (FastAPI + Uvicorn)
- GPU 모델 로딩 (4-bit 양자화)
- DB/Redis/Celery 없음
- 동기 방식 분석 (요청 시 바로 응답)

---

## 요구사항

- AWS 계정
- EC2 GPU 인스턴스 (g4dn.xlarge 권장)
- 도메인 (선택사항)

## 권장 인스턴스

| 인스턴스 | GPU | VRAM | 비용 | 용도 |
|----------|-----|------|------|------|
| **g4dn.xlarge** | T4 | 16GB | ~$0.53/hour | MVP/개발 (권장) |
| g4dn.2xlarge | T4 | 16GB | ~$0.94/hour | 동시 사용자 증가 시 |
| g5.xlarge | A10G | 24GB | ~$1.01/hour | 프로덕션 |

**월 예상 비용 (g4dn.xlarge 기준):**
- 24시간 운영: ~$380/월
- 8시간/일 운영: ~$127/월

## 빠른 시작

### 1. EC2 인스턴스 생성

**AWS Console에서:**

1. EC2 > Launch Instance
2. 설정:
   - **Name**: whiteblack-api
   - **AMI**: Ubuntu 22.04 LTS (또는 Amazon Linux 2023)
   - **Instance type**: g4dn.xlarge
   - **Key pair**: 새로 생성 또는 기존 키 선택
   - **Security Group**:
     - SSH (22): My IP
     - HTTP (80): Anywhere
     - HTTPS (443): Anywhere
     - Custom TCP (8000): Anywhere (개발용)
   - **Storage**: 50GB gp3

3. Launch Instance

### 2. 인스턴스 접속

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>

# 또는 Amazon Linux의 경우
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>
```

### 3. 초기 설정 스크립트 실행

```bash
# 프로젝트 클론
git clone https://github.com/yourusername/white-black-developer-be.git
cd white-black-developer-be

# 설정 스크립트 실행
chmod +x scripts/aws-ec2-setup.sh
sudo ./scripts/aws-ec2-setup.sh

# 로그아웃 후 재접속 (docker 그룹 적용)
exit
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 4. 환경 변수 설정

```bash
cd white-black-developer-be

# 환경 변수 파일 생성
cp .env.example .env

# 편집
nano .env
```

**필수 환경 변수:**
```bash
# Database
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_NAME=whiteblack

# Security (반드시 변경!)
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# GitHub OAuth (https://github.com/settings/developers)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_CALLBACK_URL=http://<EC2_PUBLIC_IP>:8000/api/v1/auth/github/callback
```

### 5. 애플리케이션 실행

```bash
# Docker 이미지 빌드 및 실행
docker compose -f docker-compose.prod.yml up -d

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f

# 상태 확인
docker compose -f docker-compose.prod.yml ps
```

### 6. 데이터베이스 마이그레이션

```bash
# 컨테이너 내부에서 마이그레이션 실행
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### 7. 접속 확인

```bash
# 헬스체크
curl http://localhost:8000/health

# GPU 상태 확인
curl http://localhost:8000/api/v1/system/gpu/status

# API 문서
# 브라우저에서: http://<EC2_PUBLIC_IP>:8000/docs
```

## 모델 사전 다운로드 (선택사항)

첫 요청 시 모델 다운로드에 시간이 걸립니다. 미리 다운로드하려면:

```bash
# 컨테이너 접속
docker compose -f docker-compose.prod.yml exec api bash

# 모델 프리로드 API 호출
curl -X POST http://localhost:8000/api/v1/analysis/preload
```

## 관리 명령어

```bash
# 서비스 시작
docker compose -f docker-compose.prod.yml up -d

# 서비스 중지
docker compose -f docker-compose.prod.yml down

# 재시작
docker compose -f docker-compose.prod.yml restart

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f celery_worker

# GPU 사용량 확인
nvidia-smi

# 실시간 GPU 모니터링
watch -n 1 nvidia-smi

# 컨테이너 리소스 확인
docker stats
```

## HTTPS 설정 (프로덕션)

### Let's Encrypt + Nginx

```bash
# Nginx 설정 디렉토리 생성
mkdir -p nginx/ssl

# nginx.conf 생성
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Certbot으로 인증서 발급
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# 인증서 복사
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown -R $(whoami):$(whoami) nginx/ssl/

# Nginx 포함하여 실행
docker compose -f docker-compose.prod.yml --profile with-nginx up -d
```

## 모니터링 설정

### CloudWatch 로그 (선택사항)

```bash
# CloudWatch Agent 설치
sudo apt install amazon-cloudwatch-agent

# 설정 파일 생성
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

### 간단한 헬스체크 스크립트

```bash
# healthcheck.sh
#!/bin/bash
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$HEALTH" != "200" ]; then
    echo "$(date): Health check failed with status $HEALTH" >> /var/log/whiteblack-health.log
    docker compose -f docker-compose.prod.yml restart api
fi

# crontab에 추가 (5분마다 체크)
# */5 * * * * /home/ubuntu/white-black-developer-be/healthcheck.sh
```

## 비용 최적화

### 1. Spot 인스턴스 사용

g4dn.xlarge Spot 인스턴스는 ~70% 저렴합니다 (~$0.16/hour).
단, 중단될 수 있으므로 상태 저장이 필요합니다.

### 2. 예약 인스턴스

1년 예약 시 ~40% 할인, 3년 예약 시 ~60% 할인

### 3. 자동 시작/중지

개발 환경에서는 업무 시간만 운영:

```bash
# AWS CLI로 인스턴스 중지/시작
aws ec2 stop-instances --instance-ids i-xxxxx
aws ec2 start-instances --instance-ids i-xxxxx

# CloudWatch Events로 자동화 가능
```

## 트러블슈팅

### Docker GPU 인식 안 됨

```bash
# NVIDIA 드라이버 확인
nvidia-smi

# Docker 데몬 재설정
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 메모리 부족

```bash
# Celery worker concurrency 줄이기
# docker-compose.prod.yml에서:
command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1

# GPU 캐시 클리어
docker compose -f docker-compose.prod.yml exec api python -c "import torch; torch.cuda.empty_cache()"
```

### 모델 다운로드 실패

```bash
# 캐시 볼륨 삭제 후 재시도
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
```

### 컨테이너 재시작 반복

```bash
# 로그 확인
docker compose -f docker-compose.prod.yml logs api

# 메모리 확인
free -h
docker stats
```

## 보안 체크리스트

- [ ] Security Group에서 불필요한 포트 차단
- [ ] JWT_SECRET_KEY 변경 (최소 32자)
- [ ] ENCRYPTION_KEY 변경
- [ ] DB_PASSWORD 강력한 비밀번호로 변경
- [ ] SSH 키 안전하게 보관
- [ ] 프로덕션에서 DEBUG=false 설정
- [ ] HTTPS 설정 (Let's Encrypt)
- [ ] 정기적인 보안 업데이트

## 백업

```bash
# PostgreSQL 백업
docker compose -f docker-compose.prod.yml exec db pg_dump -U postgres whiteblack > backup_$(date +%Y%m%d).sql

# 복원
cat backup_20260129.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U postgres whiteblack
```
