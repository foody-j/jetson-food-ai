# 🤖 Jetson 카메라 모니터링 시스템

NVIDIA Jetson Orin Nano 기반 실시간 GMSL 카메라 모니터링 및 AI 분석 시스템

**버전**: 2.1
**대상**: Jetson Orin Nano (JetPack 6.2)
**업데이트**: 2025-01-05

---

## 📖 시작하기 (첫 배포)

### 🎯 첫 번째로 읽을 문서

```bash
cat 배포가이드.md
```

**이 문서 하나만 읽으면 배포 완료!**

- 인터넷 사용 배포 (1시간)
- USB 오프라인 배포 (30분)
- 시스템 검증 방법
- 문제 해결

---

## 📂 시스템 구성

### Jetson #1 - 사람 감지 및 볶음 모니터링
- **위치**: `jetson1_monitoring/`
- **카메라**: 3대 (GMSL)
- **기능**: YOLO 사람 감지 (GPU 가속), 주야간 자동 전환, 볶음 모니터링, MQTT 전송
- **데이터 저장**:
  - 스냅샷: `~/Detection/`
  - 볶음 데이터: `~/StirFry_Data/left/`, `~/StirFry_Data/right/`

### Jetson #2 - 튀김 AI 및 바켓 감지
- **위치**: `jetson2_frying_ai/`
- **카메라**: 4대 (GMSL)
- **기능**: 튀김 상태 AI 분석, 바켓 감지, 데이터 수집, MQTT 통신
- **데이터 저장**:
  - 튀김 데이터: `~/AI_Data/FryingData/`
  - 바켓 데이터: `~/AI_Data/BucketData/`

---

## 🚀 빠른 실행 (이미 설치된 경우)

### Jetson #1
```bash
cd ~/jetson-camera-monitor/jetson1_monitoring
python3 JETSON1_INTEGRATED.py
```

### Jetson #2
```bash
cd ~/jetson-camera-monitor/jetson2_frying_ai
python3 JETSON2_INTEGRATED.py
```

---

## 📚 추가 문서 (필요시 참고)

### 배포 관련
| 문서 | 설명 | 읽는 시점 |
|------|------|----------|
| **배포가이드.md** | 전체 배포 과정 (필독) | 처음 배포 시 |
| **USB_DEPLOYMENT.md** | USB 배포 상세 가이드 | 오프라인 배포 시 |
| **install.sh** | 자동 설치 스크립트 | 배포 중 자동 실행 |
| **system_check.sh** | 시스템 검증 | 설치 후 확인 |

### Jetson #1 관련
| 문서 | 설명 |
|------|------|
| `jetson1_monitoring/README.md` | Jetson #1 개요 |
| `jetson1_monitoring/JETSON1_GUIDE.md` | 상세 설정 가이드 |

### Jetson #2 관련
| 문서 | 설명 |
|------|------|
| `jetson2_frying_ai/README.md` | Jetson #2 개요 |
| `jetson2_frying_ai/DATA_COLLECTION_GUIDE_UPDATED.md` | 데이터 수집 가이드 |

### 참고 문서
| 문서 | 설명 |
|------|------|
| `docs/DATA_STORAGE_MAP.md` | **데이터 저장 위치 맵 (필독!)** |
| `docs/AI_TRAINING_STRATEGY.md` | **AI 학습 전략 (필독!)** |
| `docs/CH340_USB_RS485_SETUP.md` | **CH340 드라이버 설치 (진동 센서)** |
| `docs/guides/GPU_OPTIMIZATION_STATUS.md` | GPU 최적화 상태 |
| `docs/guides/GMSL_CAMERA_MIGRATION_GUIDE.md` | GMSL 카메라 마이그레이션 |
| `docs/setup/BUILD_AND_TRANSFER.md` | 빌드 및 전송 |

---

## 🔧 핵심 스크립트

### 설치
```bash
./install.sh                    # 전체 의존성 설치
./set_maxn_mode.sh             # MAXN 성능 모드 설정
./install_maxn_service.sh      # MAXN 자동 시작 설정
```

### 자동 시작
```bash
# Jetson #1
cd ~/jetson-camera-monitor/jetson1_monitoring
./install_autostart.sh         # 자동 시작 활성화

# Jetson #2
cd ~/jetson-camera-monitor/jetson2_frying_ai
./install_autostart.sh         # 자동 시작 활성화

# 상태 확인
sudo systemctl status jetson1-monitor    # Jetson #1
sudo systemctl status jetson2-monitor    # Jetson #2
sudo systemctl status gmsl-driver-load   # GMSL 드라이버

# 실시간 로그 확인 (가장 유용!) ⭐
sudo journalctl -u jetson2-monitor -f    # Jetson #2
sudo journalctl -u jetson1-monitor -f    # Jetson #1
# 종료: Ctrl+C
```

💡 **로그 확인 및 디버깅**: 자세한 내용은 [배포가이드.md](배포가이드.md#로그-확인) 참고

### 검증
```bash
sudo ./system_check.sh         # 시스템 전체 검증 (10개 항목)
./check_versions.sh            # Python 패키지 버전 확인
```

### 배포
```bash
./prepare_usb.sh               # USB 패키지 생성
./transfer.sh <IP> <USER>      # 네트워크 전송
```

---

## ⚙️ 주요 설정 파일

| 파일 | 설명 |
|------|------|
| `requirements.txt` | Python 패키지 버전 고정 |
| `jetson1_monitoring/config.json` | Jetson #1 설정 |
| `jetson2_frying_ai/config_jetson2.json` | Jetson #2 설정 |

---

## 🔍 문제 해결

### 1. GPU 사용 안 됨
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```

### 2. 카메라 안 보임
```bash
ls -l /dev/video*

# GMSL 드라이버 로그 확인
cat /tmp/gmsl_driver_load.log

# 서비스 확인
sudo systemctl status gmsl-driver-load
sudo journalctl -u gmsl-driver-load -f

# 수동 실행 (테스트용)
cd ~/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3
sudo ./quick_bring_up.sh
```

### 2-1. 진동 센서 안 보임 (USB-RS485)
```bash
ls -l /dev/ttyUSB*

# CH340 드라이버 설치
cd ~/jetson-camera-monitor
sudo bash setup_ch340_complete.sh

# 자세한 내용: docs/CH340_USB_RS485_SETUP.md
```

### 3. 성능 느림
```bash
sudo nvpmodel -q
# NV Power Mode: MAXN_SUPER (2) ← 이게 나와야 함
./set_maxn_mode.sh
```

### 4. 버전 불일치
```bash
./check_versions.sh
pip3 install -r requirements.txt --force-reinstall
```

### 5. 전체 시스템 검증
```bash
sudo ./system_check.sh
# 통과: 10 / 실패: 0 ← 목표
```

---

## 🎯 성능 목표

### Jetson #1
- ✅ GPU 가속 활성화 (PyTorch CUDA)
- CPU 사용률: <50%
- FPS: 30 (3개 카메라)

### Jetson #2
- ✅ GPU 가속 활성화
- ✅ CPU 최적화 완료
- CPU 사용률: ~30%
- FPS: 15 (4개 카메라)

---

## 📝 버전 히스토리

### v2.1 (2025-01-05)
- ✅ 데이터 디렉토리 홈 기준 통일
- ✅ 문서 구조 개선 (배포가이드.md 중심)
- ✅ README.md 간소화

### v2.0 (2025-01-05)
- ✅ Jetson #1 GPU 가속 활성화
- ✅ Jetson #2 데이터 수집 기능 추가
- ✅ MAXN 모드 스크립트 추가
- ✅ 버전 고정 (requirements.txt)
- ✅ 폴더명 정리 (jetson1_monitoring, jetson2_frying_ai)
- ✅ USB 배포 지원
- ✅ 시스템 검증 스크립트

---

## 💡 핵심 포인트

1. ✅ **배포가이드.md** - 첫 배포 시 필독
2. ✅ **requirements.txt** - 버전 자동 고정
3. ✅ **install.sh** - 한 번 실행으로 모든 설치 완료
4. ✅ **system_check.sh** - 10개 항목 자동 검증
5. ✅ WiFi는 처음에만 필요, 이후 완전 오프라인
6. ✅ GPU 가속 자동 활성화
7. ✅ 데이터 홈 디렉토리 기준 통일

---

## 📞 문의

**문의 및 이슈 제보**: GitHub Issues

---

**배포 시작하기**: `cat 배포가이드.md` 📖
