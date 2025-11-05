#!/bin/bash
# ROBOTCAM 프로젝트를 다른 Jetson Orin으로 전송하는 스크립트

set -e

echo "=========================================="
echo "  ROBOTCAM 프로젝트 전송"
echo "=========================================="
echo ""

# 사용법 확인
if [ $# -lt 1 ]; then
    echo "사용법: $0 <원격_호스트> [원격_사용자] [원격_경로]"
    echo ""
    echo "예제:"
    echo "  $0 192.168.1.100"
    echo "  $0 192.168.1.100 jetson"
    echo "  $0 192.168.1.100 jetson /home/jetson"
    echo ""
    exit 1
fi

REMOTE_HOST=$1
REMOTE_USER=${2:-$USER}  # 기본값: 현재 사용자
REMOTE_PATH=${3:-/home/$REMOTE_USER/jetson-camera-monitor}  # 기본값: 홈 디렉토리
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

echo "[정보] 원격 호스트: $REMOTE_USER@$REMOTE_HOST"
echo "[정보] 원격 경로: $REMOTE_PATH"
echo "[정보] 로컬 경로: $SCRIPT_DIR"
echo ""

# SSH 연결 확인
echo "[1/3] SSH 연결 확인 중..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "$REMOTE_USER@$REMOTE_HOST" exit 2>/dev/null; then
    echo "[경고] SSH 키 인증 실패. 비밀번호를 입력해야 합니다."
    echo "[정보] SSH 키 복사: ssh-copy-id $REMOTE_USER@$REMOTE_HOST"
fi
echo ""

# 원격 디렉토리 생성
echo "[2/3] 원격 디렉토리 생성 중..."
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_PATH"
echo "[OK] 원격 디렉토리 준비 완료"
echo ""

# 파일 전송 (rsync 사용 - Docker 파일 제외)
echo "[3/3] 파일 전송 중..."
rsync -avz --progress \
    --exclude='_docker_archive' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.vscode' \
    --exclude='*.log' \
    --exclude='Detection/*' \
    --exclude='StirFry_Data/*' \
    "$SCRIPT_DIR/" \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"

echo ""
echo "=========================================="
echo "  전송 완료!"
echo "=========================================="
echo ""
echo "다음 단계: 원격 Jetson에서 실행"
echo ""
echo "1. SSH 접속:"
echo "   ssh $REMOTE_USER@$REMOTE_HOST"
echo ""
echo "2. 디렉토리 이동:"
echo "   cd $REMOTE_PATH"
echo ""
echo "3. 의존성 설치:"
echo "   ./install.sh"
echo ""
echo "4. 프로그램 실행:"
echo "   cd autostart_autodown"
echo "   python3 JETSON1_INTEGRATED.py"
echo ""
echo "5. 자동 시작 설정 (선택사항):"
echo "   ./install_autostart.sh"
echo ""
