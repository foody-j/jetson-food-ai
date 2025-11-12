#!/bin/bash
# 공식 방법: 환경 변수로 Jetson 모델 지정

export JETSON_MODEL_NAME=JETSON_ORIN_NANO

echo "환경 변수 설정: JETSON_MODEL_NAME=$JETSON_MODEL_NAME"
echo ""
echo "GPIO 테스트 실행 중..."
echo ""

sudo -E python3 check_all_gpio_pins.py
