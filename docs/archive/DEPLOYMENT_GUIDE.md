# ROBOTCAM 젯슨 오린 배포 가이드

새로운 Jetson Orin Nano 보드에 ROBOTCAM 통합 시스템을 배포하는 방법을 설명합니다.

## 목차
1. [사전 준비](#사전-준비)
2. [방법 1: 네트워크 전송 (추천)](#방법-1-네트워크-전송-추천)
3. [방법 2: USB/SD 카드 복사](#방법-2-usbsd-카드-복사)
4. [설치 및 실행](#설치-및-실행)
5. [자동 시작 설정](#자동-시작-설정)
6. [문제 해결](#문제-해결)

---

## 사전 준비

### 타겟 Jetson Orin Nano 보드 요구사항

- **JetPack 버전**: 6.2 (L4T R36.4.3)
- **Python 버전**: 3.10 (JetPack에 포함)
- **GMSL 카메라**: 3대 (CN4, CN5, CN6 포트)
- **모니터**: GUI 표시용 (1280x720 이상 권장)
- **저장 공간**: 최소 10GB 여유 공간

### SDK Manager로 JetPack 설치

1. **SDK Manager 다운로드**: https://developer.nvidia.com/sdk-manager
2. **타겟 보드 선택**: Jetson Orin Nano
3. **JetPack 버전**: 6.2 (r36.4.3)
4. **설치 옵션**: Full Installation
5. **완료 후**: 보드 재부팅

---

## 방법 1: 네트워크 전송 (추천)

### 1.1. 네트워크 연결 확인

타겟 보드와 개발 PC가 같은 네트워크에 연결되어 있어야 합니다.

```bash
# 타겟 보드에서 IP 확인
ip addr show

# 예: 192.168.1.100
```

### 1.2. SSH 키 복사 (선택사항 - 비밀번호 없이 접속)

```bash
# 개발 PC에서 실행
ssh-copy-id jetson@192.168.1.100
```

### 1.3. 프로젝트 전송

```bash
# 개발 PC에서 실행
cd ~/jetson-camera-monitor
./transfer.sh 192.168.1.100 jetson
```

**참고**:
- `192.168.1.100`: 타겟 보드 IP
- `jetson`: 타겟 보드 사용자 이름

전송 시간: 약 5-10분 (네트워크 속도에 따라 다름)

---

## 방법 2: USB/SD 카드 복사

### 2.1. 프로젝트 압축

```bash
# 개발 PC에서 실행
cd ~/jetson-camera-monitor
tar -czf ../jetson-camera-monitor.tar.gz \
    --exclude='_docker_archive' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='Detection/*' \
    --exclude='StirFry_Data/*' \
    .
```

### 2.2. USB/SD 카드로 복사

1. USB 드라이브/SD 카드에 `jetson-camera-monitor.tar.gz` 복사
2. 타겟 보드에 USB 연결
3. 타겟 보드에서 압축 해제:

```bash
# 타겟 보드에서 실행
cd ~
mkdir -p jetson-camera-monitor
cd jetson-camera-monitor
tar -xzf /media/usb/jetson-camera-monitor.tar.gz
```

---

## 설치 및 실행

### 3.1. 타겟 보드에 SSH 접속

```bash
ssh jetson@192.168.1.100
```

### 3.2. 프로젝트 디렉토리로 이동

```bash
cd ~/jetson-camera-monitor
```

### 3.3. 의존성 설치

```bash
./install.sh
```

**설치 항목**:
- 시스템 패키지 (Python, OpenCV, v4l-utils 등)
- Python 라이브러리 (ultralytics, opencv, paho-mqtt 등)
- 한글 폰트 (나눔고딕)
- 필요한 디렉토리 생성

설치 시간: 약 10-20분

### 3.4. GMSL 드라이버 로드

```bash
cd camera_autostart
sudo ./camera_driver_autoload.sh
```

**확인**:
```bash
# 드라이버 로드 확인
lsmod | grep max96712

# 카메라 장치 확인
ls -l /dev/video*
# /dev/video0, /dev/video1, /dev/video2가 있어야 함
```

### 3.5. 설정 파일 수정 (필요시)

```bash
cd ~/jetson-camera-monitor/jetson1_monitoring
nano config.json
```

**주요 설정**:
- `day_start`, `day_end`: 주간 모드 시간대
- `mqtt_enabled`: MQTT 사용 여부
- `mqtt_broker`: MQTT 브로커 주소
- `camera_*`: 카메라 설정

### 3.6. 수동 실행 (테스트)

```bash
cd ~/jetson-camera-monitor/jetson1_monitoring
python3 JETSON1_INTEGRATED.py
```

**확인 사항**:
- GUI 창이 정상적으로 표시되는가?
- 3개 카메라 영상이 모두 보이는가?
- YOLO 객체 검출이 작동하는가?

---

## 자동 시작 설정

부팅 시 자동으로 프로그램을 실행하려면:

### 4.1. 자동 시작 설치

```bash
cd ~/jetson-camera-monitor
./install_autostart.sh
```

### 4.2. 상태 확인

```bash
sudo systemctl status jetson-monitor
```

### 4.3. 로그 확인

```bash
# 실시간 로그
sudo journalctl -u jetson-monitor -f

# 최근 100줄
sudo journalctl -u jetson-monitor -n 100
```

### 4.4. 자동 시작 해제 (필요시)

```bash
cd ~/jetson-camera-monitor
./uninstall_autostart.sh
```

---

## 문제 해결

### GUI가 표시되지 않음

**원인**: DISPLAY 환경 변수 문제

**해결**:
```bash
export DISPLAY=:0
xhost +local:
python3 JETSON1_INTEGRATED.py
```

### 카메라 장치가 없음 (/dev/video* 없음)

**원인**: GMSL 드라이버 미로드

**해결**:
```bash
cd ~/jetson-camera-monitor/camera_autostart
sudo ./camera_driver_autoload.sh

# 확인
ls -l /dev/video*
```

### YOLO 모델 다운로드 실패

**원인**: 인터넷 연결 문제

**해결**:
```bash
# 수동으로 모델 다운로드
cd ~/jetson-camera-monitor/jetson1_monitoring
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolo12n.pt
```

### Python 패키지 import 오류

**원인**: 패키지 설치 실패

**해결**:
```bash
# 개별 설치
pip3 install --upgrade pip
pip3 install opencv-python ultralytics paho-mqtt psutil numpy Pillow

# 또는 requirements.txt 사용 (있는 경우)
pip3 install -r requirements.txt
```

### MQTT 연결 실패

**원인**: MQTT 브로커 주소 또는 네트워크 문제

**해결**:
1. `config.json`에서 `mqtt_broker` 주소 확인
2. 브로커 서버가 실행 중인지 확인
3. 네트워크 연결 확인

```bash
# MQTT 브로커 연결 테스트
mosquitto_sub -h <broker_ip> -t test -v
```

### 프로그램이 자동 시작되지 않음

**원인**: systemd 서비스 설정 문제

**해결**:
```bash
# 서비스 상태 확인
sudo systemctl status jetson-monitor

# 로그 확인
sudo journalctl -u jetson-monitor -n 50

# 서비스 재시작
sudo systemctl restart jetson-monitor
```

### 카메라 프레임 속도 느림

**원인**: GPU 사용률 높음, YOLO 추론 부하

**해결**:
```bash
# config.json 수정
nano ~/jetson-camera-monitor/jetson1_monitoring/config.json

# yolo_confidence 높이기 (0.7 → 0.8)
# camera_resolution 낮추기 (1920x1536 → 1280x720)
```

---

## 파일 구조

```
jetson-camera-monitor/
├── install.sh                      # 의존성 설치 스크립트
├── transfer.sh                     # 네트워크 전송 스크립트
├── install_autostart.sh            # 자동 시작 설치
├── uninstall_autostart.sh          # 자동 시작 제거
├── jetson-monitor.service          # systemd 서비스 파일
├── DEPLOYMENT_GUIDE.md             # 이 문서
├── jetson1_monitoring/
│   ├── JETSON1_INTEGRATED.py       # 메인 프로그램
│   ├── config.json                 # 설정 파일
│   ├── yolo12n.pt                  # YOLO 모델 (자동 다운로드)
│   ├── Detection/                  # 감지 스냅샷 저장
│   └── StirFry_Data/               # 볶음 데이터 저장
├── camera_autostart/
│   └── camera_driver_autoload.sh   # GMSL 드라이버 로드
├── src/
│   ├── core/                       # 코어 모듈
│   ├── communication/              # MQTT 통신
│   └── monitoring/                 # 카메라 모니터링
└── _docker_archive/                # 도커 파일 백업 (사용 안 함)
```

---

## 추가 정보

### 로그 파일 위치

- **systemd 로그**: `journalctl -u jetson-monitor`
- **스냅샷**: `~/jetson-camera-monitor/jetson1_monitoring/Detection/`
- **볶음 데이터**: `~/jetson-camera-monitor/jetson1_monitoring/StirFry_Data/`

### 성능 최적화

1. **YOLO 프레임 스킵 조정** (JETSON1_INTEGRATED.py:759)
2. **카메라 해상도 낮추기** (config.json)
3. **YOLO 신뢰도 임계값 높이기** (config.json: yolo_confidence)

### 백업 및 복구

```bash
# 데이터 백업
tar -czf backup_$(date +%Y%m%d).tar.gz \
    ~/jetson-camera-monitor/jetson1_monitoring/Detection \
    ~/jetson-camera-monitor/jetson1_monitoring/StirFry_Data

# 복구
tar -xzf backup_20241104.tar.gz -C ~/jetson-camera-monitor/
```

---

## 문의 및 지원

문제가 계속 발생하면:
1. 로그 파일 확인: `sudo journalctl -u jetson-monitor -n 100`
2. GitHub Issues 등록
3. 개발자에게 문의

---

**작성일**: 2024-11-04
**버전**: 1.0
**대상**: Jetson Orin Nano (JetPack 6.2)
