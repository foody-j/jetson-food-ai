#!/bin/bash
# 설치된 패키지 버전 확인 스크립트

echo "=========================================="
echo "  ROBOTCAM 설치 버전 확인"
echo "=========================================="
echo ""

echo "[시스템 정보]"
echo "JetPack: $(cat /etc/nv_tegra_release 2>/dev/null | head -1 || echo 'N/A')"
echo "Python: $(python3 --version)"
echo "CUDA: $(nvcc --version 2>/dev/null | grep release | awk '{print $5}' | sed 's/,//' || echo 'N/A')"
echo ""

echo "[Python 패키지 버전]"
echo "numpy:          $(pip3 show numpy 2>/dev/null | grep Version | awk '{print $2}')"
echo "opencv-python:  $(pip3 show opencv-python 2>/dev/null | grep Version | awk '{print $2}')"
echo "Pillow:         $(pip3 show Pillow 2>/dev/null | grep Version | awk '{print $2}')"
echo "ultralytics:    $(pip3 show ultralytics 2>/dev/null | grep Version | awk '{print $2}')"
echo "paho-mqtt:      $(pip3 show paho-mqtt 2>/dev/null | grep Version | awk '{print $2}')"
echo "psutil:         $(pip3 show psutil 2>/dev/null | grep Version | awk '{print $2}')"
echo ""

echo "[PyTorch (중요)]"
if python3 -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null)
    CUDA_AVAILABLE=$(python3 -c "import torch; print('Yes' if torch.cuda.is_available() else 'No')" 2>/dev/null)
    echo "PyTorch:        $TORCH_VERSION"
    echo "CUDA Available: $CUDA_AVAILABLE"
else
    echo "PyTorch:        미설치"
fi
echo ""

echo "[requirements.txt 비교]"
if [ -f "requirements.txt" ]; then
    echo "requirements.txt 파일 존재 ✅"
    echo ""
    echo "예상 버전 vs 설치된 버전:"
    while IFS='==' read -r package version; do
        # 주석이나 빈 줄 건너뛰기
        if [[ $package =~ ^#.*$ ]] || [[ -z "$package" ]]; then
            continue
        fi
        installed=$(pip3 show "$package" 2>/dev/null | grep Version | awk '{print $2}')
        if [ "$installed" = "$version" ]; then
            echo "  ✅ $package: $version (일치)"
        elif [ -z "$installed" ]; then
            echo "  ❌ $package: 미설치 (예상: $version)"
        else
            echo "  ⚠️  $package: $installed (예상: $version)"
        fi
    done < requirements.txt
else
    echo "requirements.txt 파일 없음 ⚠️"
    echo "버전 고정을 위해 requirements.txt 생성을 권장합니다."
fi
echo ""

echo "=========================================="
echo "  확인 완료"
echo "=========================================="
