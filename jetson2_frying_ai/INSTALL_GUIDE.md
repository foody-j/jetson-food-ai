# 🚀 Jetson #2 AI Monitoring - 완벽 설치 가이드

**대상**: Jetson Orin Nano (JetPack 6.x, L4T R36.x)

---

## ✅ 설치 체크리스트

- [ ] 1. 시스템 요구사항 확인
- [ ] 2. 카메라 드라이버 로드
- [ ] 3. Python 패키지 설치
- [ ] 4. PyTorch GPU 버전 설치
- [ ] 5. NumPy 버전 조정
- [ ] 6. AI 모델 파일 배치
- [ ] 7. 실행 테스트

---

## 📋 1. 시스템 요구사항 확인

### JetPack 버전 확인
```bash
cat /etc/nv_tegra_release
```

**예상 출력**:
```
# R36 (release), REVISION: 4.x, ...
```

→ **JetPack 6.x (L4T R36.x)** 확인됨 ✓

### Python 버전 확인
```bash
python3 --version
```

**필수**: Python 3.10 이상

---

## 📷 2. 카메라 드라이버 로드

### GMSL 카메라 드라이버 자동 로드
```bash
cd ~/jetson-camera-monitor/camera_autostart
sudo ./camera_driver_autoload.sh
```

### 카메라 확인
```bash
ls -la /dev/video*
```

**예상 출력**:
```
/dev/video0  ← 튀김 AI 왼쪽
/dev/video1  ← 튀김 AI 오른쪽
/dev/video2  ← 바켓 감지 왼쪽
/dev/video3  ← 바켓 감지 오른쪽
```

---

## 🐍 3. Python 패키지 설치

### 시스템 패키지 설치
```bash
sudo apt update
sudo apt install -y python3-pip python3-gi gstreamer1.0-tools v4l-utils
```

### 기본 Python 패키지
```bash
pip3 install --upgrade pip
pip3 install paho-mqtt Pillow psutil
```

---

## 🔥 4. PyTorch GPU 버전 설치 (중요!)

### ⚠️ 기존 PyTorch 제거
```bash
pip3 uninstall -y torch torchvision torchaudio
```

### ✅ Jetson AI Lab 저장소에서 GPU 버전 설치
```bash
pip3 install torch torchvision --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

**왜 이 방법?**
- ✅ JetPack 6.x 최적화
- ✅ CUDA 12.6 지원
- ✅ GPU 가속 보장
- ✅ 최신 PyTorch 2.8

### 설치 확인
```bash
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

**예상 출력**:
```
PyTorch: 2.8.0
CUDA: True
```

**❌ CUDA: False가 나온다면?**
→ 일반 PyTorch가 설치된 것! 위 단계 다시 실행

---

## 📊 5. NumPy 버전 조정 (필수!)

### 문제: PyTorch 2.8은 NumPy 1.x 필요

### 해결: NumPy 다운그레이드
```bash
pip3 install "numpy<2"
```

### 확인
```bash
python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')"
```

**예상 출력**: `NumPy: 1.26.x` (2.x가 아니어야 함!)

---

## 🤖 6. Ultralytics YOLO 설치

### 설치
```bash
pip3 install ultralytics
```

### 확인
```bash
python3 -c "from ultralytics import YOLO; print('YOLO OK')"
```

---

## 📁 7. AI 모델 파일 배치

### 필수 파일 확인
```bash
ls -la ~/jetson-camera-monitor/observe_add/
```

**필요한 파일**:
- `besta.pt` - 바켓 segmentation 모델
- `bestb.pt` - 바켓 classification 모델

**없다면?** 모델 파일을 해당 경로에 복사해야 함

---

## 🚀 8. 실행 테스트

### 프로그램 실행
```bash
cd ~/jetson-camera-monitor/jetson2_ai
python3 JETSON2_INTEGRATED.py
```

### 정상 출력 예시
```
==================================================
Jetson #2 - AI Monitoring System
==================================================
[모델] AI 모델 로딩 중...
[GPU] CUDA 사용 가능! GPU 가속 활성화
[모델] Frying segmenter 로드 완료
[모델] Observe_add 모델 로드 완료 (GPU)
[모델] Observe 분류 클래스: {0: 'basket'}
[카메라] 카메라 초기화 중...
[카메라] 튀김 왼쪽 (video0) 초기화 완료 ✓
[카메라] 튀김 오른쪽 (video1) 초기화 완료 ✓
[카메라] 바켓 왼쪽 (video2) 초기화 완료 ✓
[카메라] 바켓 오른쪽 (video3) 초기화 완료 ✓
[카메라] 모든 카메라 초기화 완료!
```

**✅ GPU 가속 확인!** "CUDA 사용 가능" 메시지가 나와야 함

---

## 🐛 문제 해결

### 문제 1: `CUDA: False`
**원인**: CPU 버전 PyTorch 설치됨

**해결**:
```bash
pip3 uninstall -y torch torchvision
pip3 install torch torchvision --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

### 문제 2: NumPy 에러
**에러 메시지**: `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x`

**해결**:
```bash
pip3 install "numpy<2"
```

### 문제 3: matplotlib 에러
**에러 메시지**: `AttributeError: _ARRAY_API not found`

**원인**: NumPy 2.x 설치됨

**해결**: 위 "문제 2" 해결 방법 동일

### 문제 4: 카메라가 안 보임
**확인**:
```bash
ls /dev/video*
```

**해결**:
```bash
cd ~/jetson-camera-monitor/camera_autostart
sudo ./camera_driver_autoload.sh
```

### 문제 5: 모델 파일 없음
**에러 메시지**: `FileNotFoundError: ../observe_add/besta.pt`

**해결**: 모델 파일을 올바른 경로에 복사
```bash
# 모델 파일 위치 확인
find ~ -name "besta.pt"
find ~ -name "bestb.pt"
```

### 문제 6: 튀김 AI 시작 시 프리징
**원인**: NumPy 버전 문제 또는 matplotlib 충돌

**해결**:
1. NumPy 다운그레이드: `pip3 install "numpy<2"`
2. 프로그램 재시작

---

## 📦 완전 자동 설치 스크립트

### 한 번에 설치 (카메라 드라이버 제외)
```bash
#!/bin/bash
# install_jetson2.sh

echo "🚀 Jetson #2 AI Monitoring 설치 중..."

# 1. 시스템 패키지
echo "[1/6] 시스템 패키지 설치..."
sudo apt update
sudo apt install -y python3-pip python3-gi gstreamer1.0-tools v4l-utils

# 2. 기존 PyTorch 제거
echo "[2/6] 기존 PyTorch 제거..."
pip3 uninstall -y torch torchvision torchaudio

# 3. PyTorch GPU 버전 설치
echo "[3/6] PyTorch GPU 버전 설치..."
pip3 install torch torchvision --index-url https://pypi.jetson-ai-lab.io/jp6/cu126

# 4. NumPy 다운그레이드
echo "[4/6] NumPy 버전 조정..."
pip3 install "numpy<2"

# 5. 기타 패키지
echo "[5/6] Python 패키지 설치..."
pip3 install paho-mqtt Pillow psutil ultralytics

# 6. 확인
echo "[6/6] 설치 확인..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python3 -c "from ultralytics import YOLO; print('YOLO: OK')"

echo "✅ 설치 완료!"
echo ""
echo "다음 단계:"
echo "1. 카메라 드라이버 로드: cd ~/jetson-camera-monitor/camera_autostart && sudo ./camera_driver_autoload.sh"
echo "2. 프로그램 실행: cd ~/jetson-camera-monitor/jetson2_ai && python3 JETSON2_INTEGRATED.py"
```

### 스크립트 실행
```bash
chmod +x install_jetson2.sh
./install_jetson2.sh
```

---

## 📊 패키지 버전 요약

| 패키지 | 필수 버전 | 확인 명령 |
|--------|----------|----------|
| Python | 3.10+ | `python3 --version` |
| PyTorch | 2.8.0 (CUDA) | `python3 -c "import torch; print(torch.__version__)"` |
| NumPy | < 2.0 | `python3 -c "import numpy; print(numpy.__version__)"` |
| Ultralytics | 최신 | `pip3 show ultralytics` |
| CUDA | 12.6 | `python3 -c "import torch; print(torch.version.cuda)"` |

---

## 🎯 성능 확인

### GPU 사용률 모니터링
```bash
# 터미널 1: jtop 실행
sudo jtop

# 터미널 2: 프로그램 실행
cd ~/jetson-camera-monitor/jetson2_ai
python3 JETSON2_INTEGRATED.py
```

**정상 작동 시**:
- CPU: 15-30% (기존 100%에서 대폭 감소)
- GPU: 50-70% (YOLO 실행 중)
- 프리징: 없음

---

## 💡 바켓 감지에 대한 질문

> **Q: 바켓 감지도 PyTorch를 사용하나요?**

**A**: 네! YOLO가 PyTorch 기반입니다.

- **바켓 Segmentation**: `YOLO(besta.pt)` → PyTorch 모델
- **바켓 Classification**: `YOLO(bestb.pt)` → PyTorch 모델

둘 다 GPU에서 실행됩니다:
```python
# 코드 내부
self.observe_seg_model.predict(frame, device='cuda')  # GPU
self.observe_cls_model.predict(roi, device='cuda')    # GPU
```

---

## 📞 추가 지원

### 설치 확인 명령어
```bash
# 전체 확인
cd ~/jetson-camera-monitor/jetson2_ai
python3 -c "
import torch
import numpy
from ultralytics import YOLO
print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ CUDA: {torch.cuda.is_available()}')
print(f'✅ NumPy: {numpy.__version__}')
print(f'✅ YOLO: OK')
"
```

### 로그 확인
프로그램 실행 시 나오는 메시지를 저장:
```bash
python3 JETSON2_INTEGRATED.py 2>&1 | tee install_log.txt
```

---

## ✅ 설치 완료!

모든 단계가 성공하면:
1. GUI가 뜨고
2. 4개 카메라가 모두 보이고
3. "튀김 AI 시작" 버튼 눌러도 프리징 없음
4. GPU 사용률 상승 (jtop에서 확인)

**문제가 있다면?** 이 가이드의 "문제 해결" 섹션 참고!
