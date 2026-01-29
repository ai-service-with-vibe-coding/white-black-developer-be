#!/bin/bash
# ===========================================
# AWS EC2 GPU 인스턴스 초기 설정 스크립트
# ===========================================
# 대상: Amazon Linux 2023 또는 Ubuntu 22.04 (g4dn.xlarge 권장)
# 사용법: chmod +x aws-ec2-setup.sh && sudo ./aws-ec2-setup.sh

set -e

echo "=========================================="
echo "흑백개발자 AWS EC2 GPU 설정 스크립트"
echo "=========================================="

# OS 감지
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
fi

echo "감지된 OS: $OS"

# ===========================================
# 1. 시스템 업데이트
# ===========================================
echo "[1/6] 시스템 업데이트 중..."

if [[ "$OS" == *"Amazon Linux"* ]]; then
    dnf update -y
elif [[ "$OS" == *"Ubuntu"* ]]; then
    apt-get update && apt-get upgrade -y
fi

# ===========================================
# 2. NVIDIA 드라이버 설치
# ===========================================
echo "[2/6] NVIDIA 드라이버 설치 중..."

if [[ "$OS" == *"Amazon Linux"* ]]; then
    # Amazon Linux 2023
    dnf install -y kernel-devel kernel-headers
    dnf install -y nvidia-driver-latest-dkms
elif [[ "$OS" == *"Ubuntu"* ]]; then
    # Ubuntu 22.04
    apt-get install -y linux-headers-$(uname -r)
    apt-get install -y nvidia-driver-535
fi

# 드라이버 로드
modprobe nvidia || true

# ===========================================
# 3. Docker 설치
# ===========================================
echo "[3/6] Docker 설치 중..."

if [[ "$OS" == *"Amazon Linux"* ]]; then
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
elif [[ "$OS" == *"Ubuntu"* ]]; then
    # Docker 공식 설치
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# ===========================================
# 4. NVIDIA Container Toolkit 설치
# ===========================================
echo "[4/6] NVIDIA Container Toolkit 설치 중..."

if [[ "$OS" == *"Amazon Linux"* ]]; then
    dnf config-manager --add-repo https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo
    dnf install -y nvidia-container-toolkit
elif [[ "$OS" == *"Ubuntu"* ]]; then
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
        gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    apt-get update
    apt-get install -y nvidia-container-toolkit
fi

# Docker 데몬 설정
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# ===========================================
# 5. 사용자 설정
# ===========================================
echo "[5/6] 사용자 설정 중..."

# ec2-user 또는 ubuntu 사용자를 docker 그룹에 추가
if id "ec2-user" &>/dev/null; then
    usermod -aG docker ec2-user
elif id "ubuntu" &>/dev/null; then
    usermod -aG docker ubuntu
fi

# ===========================================
# 6. 검증
# ===========================================
echo "[6/6] 설치 검증 중..."

echo ""
echo "NVIDIA 드라이버 확인:"
nvidia-smi

echo ""
echo "Docker GPU 지원 확인:"
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

echo ""
echo "=========================================="
echo "설치 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. 로그아웃 후 다시 로그인 (docker 그룹 적용)"
echo "2. 프로젝트 클론: git clone <your-repo>"
echo "3. 환경 변수 설정: cp .env.example .env && vim .env"
echo "4. 실행: docker compose -f docker-compose.prod.yml up -d"
echo ""
echo "GPU 인스턴스 권장: g4dn.xlarge (T4 16GB, ~\$0.53/hour)"
echo ""
