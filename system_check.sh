#!/bin/bash
# sudo 권한 확인
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  이 스크립트는 sudo 권한이 필요합니다."
    echo "다시 실행: sudo ./시스템검증.sh"
    exit 1
fi

# Jetson 시스템 검증 스크립트
# 카메라, MAXN 모드, GPU 등 모든 설정 확인

echo "=========================================="
echo "  🔍 Jetson 시스템 검증"
echo "=========================================="
echo ""

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS="${GREEN}✅${NC}"
FAIL="${RED}❌${NC}"
WARNING="${YELLOW}⚠️${NC}"

PASS_COUNT=0
FAIL_COUNT=0

# 1. JetPack 버전 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  JetPack 버전"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f /etc/nv_tegra_release ]; then
    JETPACK=$(cat /etc/nv_tegra_release | head -1)
    echo -e "${SUCCESS} $JETPACK"
    if echo "$JETPACK" | grep -q "R36"; then
        echo "   → JetPack 6.x (정상)"
        ((PASS_COUNT++))
    else
        echo -e "   ${WARNING} JetPack 6.2 권장"
        ((FAIL_COUNT++))
    fi
else
    echo -e "${FAIL} JetPack 버전 확인 불가"
    ((FAIL_COUNT++))
fi
echo ""

# 2. MAXN 모드 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  MAXN 성능 모드"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
POWER_MODE=$(sudo nvpmodel -q 2>/dev/null | grep "NV Power Mode")
POWER_NUM=$(sudo nvpmodel -q 2>/dev/null | grep -E "^[0-9]" | head -1 | awk '{print $1}')

if [ -n "$POWER_MODE" ]; then
    echo "$POWER_MODE"
    if echo "$POWER_MODE" | grep -q "MAXN"; then
        echo -e "${SUCCESS} MAXN 모드 활성화됨 (모드 번호: $POWER_NUM)"
        ((PASS_COUNT++))
    else
        echo -e "${FAIL} MAXN 모드가 아닙니다 (현재: 모드 $POWER_NUM)"
        echo "   → 실행: ./set_maxn_mode.sh"
        ((FAIL_COUNT++))
    fi
else
    echo -e "${FAIL} 전원 모드 확인 실패"
    ((FAIL_COUNT++))
fi
echo ""

# 3. GMSL 드라이버 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  GMSL 카메라 드라이버"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if lsmod | grep -q "max96712"; then
    echo -e "${SUCCESS} max96712 드라이버 로드됨"
    lsmod | grep max96712
    ((PASS_COUNT++))
else
    echo -e "${FAIL} max96712 드라이버가 로드되지 않음"
    echo "   → 실행: cd camera_autostart && sudo ./camera_driver_autoload.sh"
    ((FAIL_COUNT++))
fi
echo ""

# 4. 카메라 장치 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  카메라 장치 (/dev/video*)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ls /dev/video* 1> /dev/null 2>&1; then
    VIDEO_COUNT=$(ls /dev/video* | wc -l)
    echo -e "${SUCCESS} 카메라 장치 발견: $VIDEO_COUNT 개"
    ls -l /dev/video*
    
    if [ "$VIDEO_COUNT" -ge 3 ]; then
        echo "   → Jetson #1: 3개 이상 (정상)"
        ((PASS_COUNT++))
    elif [ "$VIDEO_COUNT" -ge 4 ]; then
        echo "   → Jetson #2: 4개 이상 (정상)"
        ((PASS_COUNT++))
    else
        echo -e "   ${WARNING} 카메라가 $VIDEO_COUNT 개만 발견됨"
        ((FAIL_COUNT++))
    fi
else
    echo -e "${FAIL} 카메라 장치 없음"
    echo "   → GMSL 드라이버를 먼저 로드하세요"
    ((FAIL_COUNT++))
fi
echo ""

# 5. Python 버전 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Python 환경"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
PYTHON_VERSION=$(python3 --version 2>&1)
echo "$PYTHON_VERSION"
if echo "$PYTHON_VERSION" | grep -q "3.10"; then
    echo -e "${SUCCESS} Python 3.10.x (정상)"
    ((PASS_COUNT++))
else
    echo -e "${WARNING} Python 3.10 권장"
    ((FAIL_COUNT++))
fi
echo ""

# 6. CUDA 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  CUDA (GPU)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep release | awk '{print $5}' | sed 's/,//')
    echo -e "${SUCCESS} CUDA: $CUDA_VERSION"
    if echo "$CUDA_VERSION" | grep -q "12.6"; then
        echo "   → CUDA 12.6 (정상)"
        ((PASS_COUNT++))
    else
        echo -e "   ${WARNING} CUDA 12.6 권장"
        ((FAIL_COUNT++))
    fi
else
    echo -e "${FAIL} CUDA 미설치"
    ((FAIL_COUNT++))
fi
echo ""

# 7. PyTorch CUDA 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  PyTorch CUDA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python3 -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null)
    CUDA_AVAILABLE=$(python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null)
    GPU_NAME=$(python3 -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')" 2>/dev/null)
    
    echo "PyTorch: $TORCH_VERSION"
    echo "GPU: $GPU_NAME"
    
    if [ "$CUDA_AVAILABLE" = "True" ]; then
        echo -e "${SUCCESS} PyTorch CUDA 사용 가능!"
        echo "   → YOLO GPU 가속 활성화됨"
        ((PASS_COUNT++))
    else
        echo -e "${FAIL} PyTorch CUDA 미지원"
        echo "   → 실행: pip3 install torch --index-url https://pypi.jetson-ai-lab.io/jp6/cu126"
        ((FAIL_COUNT++))
    fi
else
    echo -e "${FAIL} PyTorch 미설치"
    echo "   → 실행: ./install.sh"
    ((FAIL_COUNT++))
fi
echo ""

# 8. Python 패키지 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  Python 패키지 (핵심)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_package() {
    local pkg=$1
    local expected=$2
    local installed=$(pip3 show "$pkg" 2>/dev/null | grep Version | awk '{print $2}')
    
    if [ -n "$installed" ]; then
        if [ "$installed" = "$expected" ]; then
            echo -e "${SUCCESS} $pkg: $installed"
            return 0
        else
            echo -e "${WARNING} $pkg: $installed (예상: $expected)"
            return 1
        fi
    else
        echo -e "${FAIL} $pkg: 미설치"
        return 1
    fi
}

PKG_PASS=0
PKG_FAIL=0

check_package "numpy" "1.26.4" && ((PKG_PASS++)) || ((PKG_FAIL++))
check_package "opencv-python" "4.12.0.88" && ((PKG_PASS++)) || ((PKG_FAIL++))
check_package "ultralytics" "8.3.224" && ((PKG_PASS++)) || ((PKG_FAIL++))
check_package "paho-mqtt" "2.1.0" && ((PKG_PASS++)) || ((PKG_FAIL++))

if [ $PKG_FAIL -eq 0 ]; then
    echo "   → 모든 패키지 버전 일치!"
    ((PASS_COUNT++))
else
    echo -e "   ${WARNING} $PKG_FAIL 개 패키지 버전 불일치"
    echo "   → 실행: pip3 install -r requirements.txt --force-reinstall"
    ((FAIL_COUNT++))
fi
echo ""

# 9. 자동 시작 서비스 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  자동 시작 서비스 (선택사항)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if systemctl is-enabled jetson-monitor.service 2>/dev/null | grep -q "enabled"; then
    echo -e "${SUCCESS} jetson-monitor.service 활성화됨"
    SERVICE_STATUS=$(systemctl is-active jetson-monitor.service 2>/dev/null)
    echo "   상태: $SERVICE_STATUS"
else
    echo -e "${WARNING} 자동 시작 미설정 (선택사항)"
    echo "   → 설정하려면: ./install_autostart.sh"
fi
echo ""

# 10. 디스크 공간 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔟  디스크 공간"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DISK_AVAIL=$(df -h ~ | tail -1 | awk '{print $4}')
DISK_AVAIL_GB=$(df -BG ~ | tail -1 | awk '{print $4}' | sed 's/G//')

echo "사용 가능: $DISK_AVAIL"
if [ "$DISK_AVAIL_GB" -ge 10 ]; then
    echo -e "${SUCCESS} 10GB 이상 여유 공간 (정상)"
    ((PASS_COUNT++))
else
    echo -e "${WARNING} 여유 공간 부족 (10GB 이상 권장)"
    ((FAIL_COUNT++))
fi
echo ""

# 최종 결과
echo "=========================================="
echo "  📊 검증 결과"
echo "=========================================="
echo ""
echo -e "통과: ${GREEN}${PASS_COUNT}${NC} / 실패: ${RED}${FAIL_COUNT}${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${SUCCESS} ${GREEN}모든 검증 통과! 시스템 정상입니다.${NC}"
    echo ""
    echo "다음 단계:"
    echo "  cd ~/jetson-camera-monitor/jetson1_monitoring"
    echo "  python3 JETSON1_INTEGRATED.py"
    echo ""
    exit 0
else
    echo -e "${WARNING} ${YELLOW}$FAIL_COUNT 개 항목에 문제가 있습니다.${NC}"
    echo ""
    echo "해결 방법은 위의 각 항목을 참고하세요."
    echo ""
    exit 1
fi
