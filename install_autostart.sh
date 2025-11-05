#!/bin/bash
# ROBOTCAM 자동 시작 설치 스크립트

set -e

echo "=========================================="
echo "  ROBOTCAM 자동 시작 설정"
echo "=========================================="
echo ""

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SERVICE_FILE="$SCRIPT_DIR/jetson-monitor.service"
SYSTEMD_DIR="/etc/systemd/system"

# 현재 사용자 이름 확인
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" = "root" ]; then
    echo "[오류] root로 실행하지 마세요."
    echo "[정보] 일반 사용자로 실행: ./install_autostart.sh"
    exit 1
fi

# 서비스 파일 존재 확인
if [ ! -f "$SERVICE_FILE" ]; then
    echo "[오류] 서비스 파일을 찾을 수 없습니다: $SERVICE_FILE"
    exit 1
fi

echo "[1/4] 서비스 파일 복사 중..."
sudo cp "$SERVICE_FILE" "$SYSTEMD_DIR/jetson-monitor.service"
echo "[OK] 서비스 파일 복사 완료"
echo ""

echo "[2/4] systemd 데몬 재로드 중..."
sudo systemctl daemon-reload
echo "[OK] 데몬 재로드 완료"
echo ""

echo "[3/4] 서비스 활성화 중..."
sudo systemctl enable jetson-monitor.service
echo "[OK] 서비스 활성화 완료"
echo ""

echo "[4/4] 서비스 시작 중..."
sudo systemctl start jetson-monitor.service
echo "[OK] 서비스 시작 완료"
echo ""

echo "=========================================="
echo "  자동 시작 설정 완료!"
echo "=========================================="
echo ""
echo "상태 확인:"
echo "  sudo systemctl status jetson-monitor"
echo ""
echo "로그 확인:"
echo "  sudo journalctl -u jetson-monitor -f"
echo ""
echo "중지:"
echo "  sudo systemctl stop jetson-monitor"
echo ""
echo "자동 시작 해제:"
echo "  ./uninstall_autostart.sh"
echo ""
