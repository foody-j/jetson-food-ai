#!/bin/bash
# USB 배포용 패키지 생성 스크립트

echo "=========================================="
echo "  📦 USB 배포 패키지 생성"
echo "=========================================="
echo ""

PACKAGE_NAME="jetson-camera-monitor-usb.tar.gz"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "[1/3] 프로젝트 압축 중..."
cd ~
tar -czf "$PACKAGE_NAME" \
    --exclude='jetson-camera-monitor/__pycache__' \
    --exclude='jetson-camera-monitor/.git' \
    --exclude='jetson-camera-monitor/Detection/*' \
    --exclude='jetson-camera-monitor/StirFry_Data/*' \
    --exclude='jetson-camera-monitor/AI_Data/*' \
    --exclude='jetson-camera-monitor/_archive' \
    --exclude='jetson-camera-monitor/docs/archive' \
    jetson-camera-monitor

if [ $? -eq 0 ]; then
    echo "✅ 압축 완료: ~/$PACKAGE_NAME"
else
    echo "❌ 압축 실패"
    exit 1
fi
echo ""

echo "[2/3] 파일 크기 확인..."
SIZE=$(du -h ~/$PACKAGE_NAME | cut -f1)
echo "압축 파일 크기: $SIZE"
echo ""

echo "[3/3] USB 마운트 확인..."
if ls /media/$USER/* 2>/dev/null | head -1; then
    USB_PATH=$(ls -d /media/$USER/*/ 2>/dev/null | head -1)
    echo "USB 발견: $USB_PATH"
    echo ""
    
    read -p "USB로 복사하시겠습니까? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "USB로 복사 중..."
        cp ~/$PACKAGE_NAME "$USB_PATH"
        
        if [ $? -eq 0 ]; then
            echo "✅ USB 복사 완료: ${USB_PATH}${PACKAGE_NAME}"
        else
            echo "❌ USB 복사 실패"
            exit 1
        fi
    else
        echo "복사 취소됨"
        echo "수동 복사: cp ~/$PACKAGE_NAME /media/usb경로/"
    fi
else
    echo "⚠️  USB가 마운트되지 않음"
    echo "수동으로 USB에 복사하세요:"
    echo "  cp ~/$PACKAGE_NAME /media/usb경로/"
fi
echo ""

echo "=========================================="
echo "  ✅ USB 배포 패키지 생성 완료!"
echo "=========================================="
echo ""
echo "생성된 파일: ~/$PACKAGE_NAME"
echo "파일 크기: $SIZE"
echo ""
echo "타겟 Jetson에서 압축 해제:"
echo "  cd ~"
echo "  tar -xzf jetson-camera-monitor-usb.tar.gz"
echo "  cd jetson-camera-monitor"
echo "  ./install.sh"
echo ""
