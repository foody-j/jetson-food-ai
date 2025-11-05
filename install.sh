#!/bin/bash
# Jetson Orin Nano - ROBOTCAM 통합 시스템 설치 스크립트
# JetPack 6.2 (L4T R36.4.3) 용

set -e  # 에러 시 중단

echo "=========================================="
echo "  ROBOTCAM 통합 시스템 설치"
echo "  JetPack 6.2 (L4T R36.4.3)"
echo "=========================================="
echo ""

# 현재 사용자 확인
CURRENT_USER=$(whoami)
INSTALL_DIR=$(pwd)

echo "[정보] 설치 디렉토리: $INSTALL_DIR"
echo "[정보] 사용자: $CURRENT_USER"
echo ""

# JetPack 버전 확인
echo "[1/7] JetPack 버전 확인 중..."
if [ -f /etc/nv_tegra_release ]; then
    cat /etc/nv_tegra_release
else
    echo "[경고] JetPack 버전을 확인할 수 없습니다."
fi
echo ""

# 시스템 업데이트
echo "[2/7] 시스템 패키지 업데이트 중..."
sudo apt-get update
echo ""

# 시스템 의존성 설치
echo "[3/7] 시스템 의존성 설치 중..."
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-tk \
    python3-opencv \
    fonts-nanum \
    fonts-nanum-coding \
    fonts-nanum-extra \
    v4l-utils \
    libopencv-dev \
    libopenblas-base \
    libopenmpi-dev \
    libjpeg-dev \
    zlib1g-dev \
    git \
    nano

echo "[OK] 시스템 의존성 설치 완료"
echo ""

# Python 패키지 설치
echo "[4/7] Python 패키지 설치 중 (버전 고정)..."
pip3 install --upgrade pip

# requirements.txt가 있으면 사용 (버전 고정)
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    echo "[INFO] requirements.txt 사용 (버전 고정 설치)"
    pip3 install -r "$INSTALL_DIR/requirements.txt"
else
    echo "[WARNING] requirements.txt 없음 (최신 버전 설치)"
    pip3 install \
        opencv-python \
        numpy \
        Pillow \
        ultralytics \
        paho-mqtt \
        psutil
fi

echo "[OK] Python 패키지 설치 완료"
echo ""

# 필요한 디렉토리 생성
echo "[5/7] 데이터 디렉토리 생성 중..."
mkdir -p "$HOME/Detection"
mkdir -p "$HOME/StirFry_Data/left"
mkdir -p "$HOME/StirFry_Data/right"
mkdir -p "$HOME/AI_Data/FryingData"
mkdir -p "$HOME/AI_Data/BucketData"
echo "[OK] 디렉토리 생성 완료"
echo ""

# GMSL 드라이버 확인
echo "[6/7] GMSL 드라이버 확인 중..."
if lsmod | grep -q "max96712"; then
    echo "[OK] GMSL 드라이버가 이미 로드되어 있습니다."
else
    echo "[경고] GMSL 드라이버가 로드되지 않았습니다."
    echo "[정보] camera_autostart/camera_driver_autoload.sh를 실행하세요."
fi
echo ""

# 카메라 장치 확인
echo "[7/7] 카메라 장치 확인 중..."
if ls /dev/video* 1> /dev/null 2>&1; then
    echo "[OK] 카메라 장치 발견:"
    ls -l /dev/video*
else
    echo "[경고] 카메라 장치를 찾을 수 없습니다."
    echo "[정보] GMSL 드라이버를 먼저 로드하세요."
fi
echo ""

# YOLO 모델 확인
echo "[추가] YOLO 모델 파일 확인 중..."
JETSON1_MODEL="$INSTALL_DIR/jetson1_monitoring/add_model/yolo_v8_nano.pt"
if [ -f "$JETSON1_MODEL" ]; then
    echo "[OK] Jetson #1 YOLO 모델 존재"
else
    echo "[경고] Jetson #1 YOLO 모델 파일이 없습니다"
    echo "[정보] 첫 실행 시 자동으로 다운로드됩니다."
fi
echo ""

echo "=========================================="
echo "  설치 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo ""
echo "1. MAXN 성능 모드 설정 (권장):"
echo "   ./set_maxn_mode.sh"
echo "   또는 부팅 시 자동: ./install_maxn_service.sh"
echo ""
echo "2. GMSL 드라이버 로드 (미완료 시):"
echo "   cd camera_autostart"
echo "   sudo ./camera_driver_autoload.sh"
echo ""
echo "3. Jetson #1 프로그램 실행:"
echo "   cd jetson1_monitoring"
echo "   python3 JETSON1_INTEGRATED.py"
echo ""
echo "4. Jetson #2 프로그램 실행:"
echo "   cd jetson2_frying_ai"
echo "   python3 JETSON2_INTEGRATED.py"
echo ""
echo "5. 프로그램 자동 시작 설정 (선택사항):"
echo "   ./install_autostart.sh"
echo ""
echo "자세한 내용은 README.md 또는 DEPLOYMENT_GUIDE.md를 참조하세요."
echo ""
