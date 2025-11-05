#!/bin/bash
# ROBOTCAM 자동 시작 제거 스크립트

set -e

echo "=========================================="
echo "  ROBOTCAM 자동 시작 제거"
echo "=========================================="
echo ""

SERVICE_NAME="jetson-monitor.service"

echo "[1/4] 서비스 중지 중..."
sudo systemctl stop "$SERVICE_NAME" || true
echo "[OK] 서비스 중지 완료"
echo ""

echo "[2/4] 서비스 비활성화 중..."
sudo systemctl disable "$SERVICE_NAME" || true
echo "[OK] 서비스 비활성화 완료"
echo ""

echo "[3/4] 서비스 파일 삭제 중..."
sudo rm -f "/etc/systemd/system/$SERVICE_NAME"
echo "[OK] 서비스 파일 삭제 완료"
echo ""

echo "[4/4] systemd 데몬 재로드 중..."
sudo systemctl daemon-reload
echo "[OK] 데몬 재로드 완료"
echo ""

echo "=========================================="
echo "  자동 시작 제거 완료!"
echo "=========================================="
echo ""
echo "수동 실행:"
echo "  cd autostart_autodown"
echo "  python3 JETSON1_INTEGRATED.py"
echo ""
