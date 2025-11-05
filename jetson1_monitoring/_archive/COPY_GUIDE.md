# 🚀 새 Jetson에 복사할 파일/폴더 가이드

## 📦 복사해야 할 것 (필수)

새로운 Jetson Orin Nano에 복사해야 할 **최소한의 필수 파일**만 정리했습니다.

---

## 방법 1: 최소 필수 파일만 복사 (권장)

### 📁 복사할 디렉토리 구조

```
jetson-camera-monitor/
├── autostart_autodown/           ✅ 전체 복사 (메인 프로그램)
│   ├── JETSON1_INTEGRATED.py     (메인 프로그램)
│   ├── JETSON1_INTEGRATED_v2.py  (단순 테스트용)
│   ├── gst_camera.py              (GStreamer 카메라 래퍼)
│   ├── config.json                (설정 파일)
│   ├── DEPLOY_SETUP.sh            (자동 설치 스크립트)
│   ├── requirements.txt           (Python 의존성)
│   ├── DEPLOYMENT_GUIDE.md        (배포 가이드)
│   └── COPY_GUIDE.md              (이 파일)
│
├── src/                           ✅ 전체 복사 (프로그램 의존성)
│   ├── communication/
│   │   ├── __init__.py
│   │   └── mqtt_client.py
│   ├── core/
│   │   ├── config.py
│   │   ├── system_info.py
│   │   └── utils.py
│   └── monitoring/
│       └── camera/
│           ├── __init__.py
│           ├── camera_base.py
│           └── camera_factory.py
│
└── SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/  ✅ 전체 복사 (GMSL 드라이버)
    ├── ko/
    │   ├── max96712.ko
    │   └── sgx-yuv-gmsl2.ko
    └── install.sh
```

### 📝 복사 명령어

**USB/외장 드라이브 사용:**
```bash
# 현재 Jetson에서
cd /home/dkuyj
zip -r jetson-deploy.zip \
  jetson-camera-monitor/autostart_autodown \
  jetson-camera-monitor/src \
  jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3 \
  -x '*.pyc' '*__pycache__*' '*.git*'

# USB에 복사
cp jetson-deploy.zip /media/usb/

# 새 Jetson에서
cd ~
unzip /media/usb/jetson-deploy.zip
```

**네트워크 (SCP) 사용:**
```bash
# 새 Jetson의 IP가 192.168.1.100이라고 가정
cd /home/dkuyj

# 압축해서 전송
zip -r jetson-deploy.zip \
  jetson-camera-monitor/autostart_autodown \
  jetson-camera-monitor/src \
  jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3 \
  -x '*.pyc' '*__pycache__*' '*.git*'

scp jetson-deploy.zip user@192.168.1.100:~/
ssh user@192.168.1.100 "cd ~ && unzip jetson-deploy.zip"
```

---

## 방법 2: 전체 프로젝트 복사 (간단)

모든 것을 복사하고 싶다면:

```bash
# 현재 Jetson에서
cd /home/dkuyj
zip -r jetson-full.zip jetson-camera-monitor/ \
  -x '*__pycache__*' '*.pyc' '*.git*'

# USB 복사
cp jetson-full.zip /media/usb/

# 새 Jetson에서
cd ~
unzip /media/usb/jetson-full.zip
```

---

## 📋 복사 후 체크리스트

새 Jetson에서 다음을 확인하세요:

### 1. 파일 구조 확인
```bash
cd ~/jetson-camera-monitor

# 필수 파일 존재 확인
ls autostart_autodown/JETSON1_INTEGRATED.py
ls autostart_autodown/gst_camera.py
ls autostart_autodown/config.json
ls autostart_autodown/DEPLOY_SETUP.sh

# src 확인
ls src/communication/mqtt_client.py
ls src/core/system_info.py
ls src/monitoring/camera/camera_factory.py

# GMSL 드라이버 확인
ls SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ko/max96712.ko
ls SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ko/sgx-yuv-gmsl2.ko
```

### 2. 자동 설치 실행
```bash
cd ~/jetson-camera-monitor/autostart_autodown
chmod +x DEPLOY_SETUP.sh
./DEPLOY_SETUP.sh
```

### 3. config.json 수정 (필요시)
```bash
nano ~/jetson-camera-monitor/autostart_autodown/config.json
```

주요 확인 사항:
- `camera_index`: 자동 카메라 (video2)
- `stirfry_left_camera_index`: 볶음 왼쪽 (video0)
- `stirfry_right_camera_index`: 볶음 오른쪽 (video1)
- `gmsl_driver_dir`: 드라이버 경로 (사용자 이름 확인!)

### 4. 실행 테스트
```bash
cd ~/jetson-camera-monitor/autostart_autodown

# 간단한 3-카메라 테스트
python3 JETSON1_INTEGRATED_v2.py

# 전체 프로그램
python3 JETSON1_INTEGRATED.py
```

---

## ⚠️ 주의사항

### 1. 사용자 이름이 다른 경우
`config.json`에서 경로 수정 필요:

```json
{
  "gmsl_driver_dir": "/home/NEW_USERNAME/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3"
}
```

자동 수정:
```bash
cd ~/jetson-camera-monitor/autostart_autodown
sed -i "s|/home/dkuyj|/home/$USER|g" config.json
```

### 2. Python 경로 문제
`JETSON1_INTEGRATED.py` 상단의 경로가 자동으로 처리되므로 수정 불필요.

### 3. 권한 문제
```bash
# 실행 권한 추가
chmod +x ~/jetson-camera-monitor/autostart_autodown/*.sh
```

---

## 🔍 복사되지 않아도 되는 것 (불필요)

다음은 **복사하지 않아도 됨**:

- ❌ `_docker_archive/` - Docker 관련 (사용 안 함)
- ❌ `comm_protocol/` - C# MQTT 예제 (사용 안 함)
- ❌ `frying_ai/` - 옛날 버전
- ❌ `camera_monitor/` - 옛날 버전
- ❌ `tests/` - 테스트 파일
- ❌ `docs/` - 문서 (필요하면 복사)
- ❌ `.git/` - Git 히스토리
- ❌ `__pycache__/` - Python 캐시
- ❌ `*.pyc` - Python 컴파일 파일
- ❌ `.vs/`, `.claude/` - 에디터 설정
- ❌ 백업 파일 (`*_backup_*.py`)

---

## 📊 예상 크기

최소 필수 파일:
- `autostart_autodown/`: ~200KB
- `src/`: ~50KB
- `SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/`: ~5MB

**총 ~5.3MB** (매우 작음!)

전체 프로젝트: ~100MB (문서, 테스트 등 포함)

---

## 🎯 빠른 요약

### 복사할 3가지 폴더:
1. ✅ `autostart_autodown/` - 메인 프로그램
2. ✅ `src/` - 공통 라이브러리
3. ✅ `SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/` - GMSL 드라이버

### 복사 후 실행:
```bash
cd ~/jetson-camera-monitor/autostart_autodown
./DEPLOY_SETUP.sh
python3 JETSON1_INTEGRATED.py
```

끝! 🎉
