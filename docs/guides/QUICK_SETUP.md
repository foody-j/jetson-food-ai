# ⚡ 빠른 설정 가이드

**Jetson 카메라 모니터링 시스템**

---

## 🔧 필수 설정

### 0. MAXN 성능 모드 설정 (최우선!) ⚡

**Jetson Orin Nano는 기본 25W 모드**로 부팅됩니다. **최대 성능**을 위해 MAXN 모드로 변경 필수!

#### 방법 1: 즉시 적용 (수동)
```bash
cd ~/jetson-camera-monitor
./set_maxn_mode.sh
```

#### 방법 2: 부팅 시 자동 적용 (추천!)
```bash
cd ~/jetson-camera-monitor
./install_maxn_service.sh

# 재부팅 후 자동으로 MAXN 모드
```

#### 현재 모드 확인
```bash
sudo nvpmodel -q
```

**예상 출력**:
```
NV Power Mode: MAXN
0  ← MAXN 모드 (최대 성능)
```

**성능 비교**:
| 모드 | 전력 | CPU | GPU | 성능 |
|------|------|-----|-----|------|
| 25W | 25W | 제한적 | 제한적 | 보통 |
| **MAXN** | **최대** | **최대** | **최대** | **최고** ⭐ |

---

### 1. jtop 설치 (시스템 모니터링)

**jtop**은 Jetson의 CPU/GPU/메모리 사용률을 실시간으로 모니터링하는 필수 도구입니다.

#### 설치 방법
```bash
sudo pip3 install -U jetson-stats
```

**⚠️ 주의**:
- 반드시 `sudo`와 함께 설치해야 합니다
- 설치 후 **재부팅** 필요합니다

```bash
sudo reboot
```

#### 사용 방법
```bash
sudo jtop
```

**화면 설명**:
- `1 - ALL`: 전체 시스템 상태
- `2 - CPU`: CPU 코어별 사용률
- `3 - GPU`: GPU 사용률 ⭐ (여기서 GPU 사용 확인!)
- `4 - MEM`: 메모리 사용률
- `5 - EMC`: 메모리 대역폭
- `6 - PWR`: 전력 소비
- `7 - TEMP`: 온도

**단축키**:
- `1-7`: 각 페이지로 이동
- `q`: 종료
- `h`: 도움말

---

## 📊 GPU 사용 확인 방법

### 방법 1: jtop 사용 (추천)
```bash
# 터미널 1: jtop 실행
sudo jtop

# 터미널 2: 프로그램 실행
cd ~/jetson-camera-monitor/jetson1_monitoring
python3 JETSON1_INTEGRATED.py

# jtop에서 '3' 누르면 GPU 페이지
# GPU 사용률이 30-50% 나오면 정상!
```

### 방법 2: 프로그램 출력 확인
프로그램 시작 시 다음 메시지 확인:

**✅ 정상 (GPU 사용)**:
```
[GPU] PyTorch CUDA 사용 가능! YOLO GPU 가속 활성화 (Orin)
[YOLO] 모델 로드 완료 (GPU 가속 활성화)
```

**❌ 문제 (CPU만 사용)**:
```
[GPU] PyTorch CUDA 미지원 - YOLO는 CPU 모드로 실행
[YOLO] 모델 로드 완료 (CPU 모드)
```

### 방법 3: Python 명령어로 확인
```bash
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"
```

**예상 출력**:
```
CUDA available: True
GPU: Orin
```

---

## 🎯 성능 목표

### Jetson #1
프로그램 실행 중 jtop 확인:

| 항목 | 목표 | 확인 방법 |
|------|------|----------|
| CPU 사용률 | < 50% | jtop → `2 - CPU` |
| GPU 사용률 | 30-50% | jtop → `3 - GPU` ⭐ |
| 온도 | < 75°C | jtop → `7 - TEMP` |
| 메모리 | < 6GB | jtop → `4 - MEM` |

### Jetson #2
프로그램 실행 중 jtop 확인:

| 항목 | 목표 | 확인 방법 |
|------|------|----------|
| CPU 사용률 | ~30-40% | jtop → `2 - CPU` |
| GPU 사용률 | 50-70% | jtop → `3 - GPU` ⭐ |
| 온도 | < 75°C | jtop → `7 - TEMP` |
| 메모리 | < 6GB | jtop → `4 - MEM` |

---

## 🐛 문제 해결

### jtop 설치 실패
```bash
# 에러: "command not found"
# 해결: sudo로 설치
sudo pip3 install -U jetson-stats

# 설치 후 반드시 재부팅
sudo reboot
```

### GPU가 0% 사용
**원인**: PyTorch CPU 버전 설치됨

**확인**:
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# False 나오면 문제!
```

**해결**:
```bash
pip3 uninstall -y torch torchvision
pip3 install torch torchvision --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

자세한 설명: `jetson2_frying_ai/INSTALL_GUIDE.md` 참조

### CPU 사용률이 너무 높음 (>80%)

**Jetson #1**:
- YOLO가 GPU를 사용하는지 확인
- 프로그램 출력에서 "GPU 가속 활성화" 확인

**Jetson #2**:
- `config_jetson2.json` 파라미터 조정
- Frame skip 증가: `frying_frame_skip: 20`, `observe_frame_skip: 30`

---

## 📝 유용한 명령어

### 시스템 정보 확인
```bash
# JetPack 버전
cat /etc/nv_tegra_release

# Python 버전
python3 --version

# PyTorch 버전
python3 -c "import torch; print(torch.__version__)"

# CUDA 버전
python3 -c "import torch; print(torch.version.cuda)"
```

### 프로세스 모니터링
```bash
# CPU 사용률 높은 프로세스 확인
top -u dkuyj

# 특정 프로세스 CPU 확인
ps aux | grep python3 | grep -v grep
```

### 카메라 확인
```bash
# 카메라 디바이스 확인
ls -la /dev/video*

# 카메라 정보
v4l2-ctl --device=/dev/video0 --all
```

---

## 🚀 빠른 시작

### Jetson #1
```bash
# 1. jtop 실행 (별도 터미널)
sudo jtop

# 2. 프로그램 실행
cd ~/jetson-camera-monitor/jetson1_monitoring
python3 JETSON1_INTEGRATED.py

# 3. jtop에서 GPU 확인 ('3' 누르기)
# GPU 사용률 30-50% 확인
```

### Jetson #2
```bash
# 1. jtop 실행 (별도 터미널)
sudo jtop

# 2. 프로그램 실행
cd ~/jetson-camera-monitor/jetson2_frying_ai
python3 JETSON2_INTEGRATED.py

# 3. GUI에서 "튀김 AI 시작" 또는 "바켓 감지 시작"
# 4. jtop에서 GPU 사용률 확인
```

---

## 📚 추가 문서

- **설치 가이드**: `jetson2_frying_ai/INSTALL_GUIDE.md`
- **GPU 최적화**: `GPU_OPTIMIZATION_STATUS.md`
- **데이터 수집**: `jetson2_frying_ai/DATA_COLLECTION_GUIDE.md`
- **전체 요약**: `OPTIMIZATION_SUMMARY.md`

---

## 💡 팁

### jtop을 자동 시작하기
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
alias j='sudo jtop'

# 사용:
j  # jtop 실행
```

### 성능 모드 설정
```bash
# 최대 성능 모드
sudo nvpmodel -m 0
sudo jetson_clocks

# 현재 모드 확인
sudo nvpmodel -q
```

---

**jtop 설치 후 재부팅하는 것을 잊지 마세요!** 🔄
