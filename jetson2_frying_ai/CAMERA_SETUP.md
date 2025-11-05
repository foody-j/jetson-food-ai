# 📷 Jetson #2 - 카메라 설정 가이드

## ⚠️ 필수 사항: 카메라 드라이버 로드

**새 카메라를 연결하거나 시스템 재부팅 후 반드시 실행해야 합니다!**

---

## 🚀 빠른 설정 (권장)

```bash
cd ~/jetson-camera-monitor/camera_autostart
sudo ./camera_driver_autoload.sh
```

이 스크립트는:
- ✅ GMSL 드라이버 자동 로드 (4-camera 모드)
- ✅ NVCSI 클럭 설정
- ✅ 카메라 해상도 자동 설정 (1920x1536)
- ✅ video0~3 디바이스 확인

---

## 🔧 수동 설정

### 1. 기존 드라이버 제거 (선택사항)

새 카메라를 연결한 경우:

```bash
sudo rmmod sgx_yuv_gmsl2 max96712
```

### 2. 드라이버 로드

```bash
cd ~/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ko

# MAX96712 deserializer 로드
sudo insmod max96712.ko

# GMSL2 카메라 드라이버 로드 (4개 카메라, 모두 GMSL2/3G)
sudo insmod sgx-yuv-gmsl2.ko GMSLMODE_1=2,2,2,2
```

**GMSLMODE 값:**
- `0` = GMSL (구형)
- `1` = GMSL2/6G (6Gbps)
- `2` = GMSL2/3G (3Gbps) ← 기본값

### 3. 카메라 확인

```bash
# 디바이스 확인
ls -la /dev/video*

# 출력 예시:
# /dev/video0  ← Frying AI Left
# /dev/video1  ← Frying AI Right
# /dev/video2  ← Observe_add Left
# /dev/video3  ← Observe_add Right
```

### 4. GStreamer 테스트

각 카메라가 정상 작동하는지 테스트:

```bash
# video0 (Frying AI Left)
gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw,format=UYVY,width=1920,height=1536,framerate=30/1 ! autovideosink

# video1 (Frying AI Right)
gst-launch-1.0 v4l2src device=/dev/video1 ! video/x-raw,format=UYVY,width=1920,height=1536,framerate=30/1 ! autovideosink

# video2 (Observe_add Left)
gst-launch-1.0 v4l2src device=/dev/video2 ! video/x-raw,format=UYVY,width=1920,height=1536,framerate=30/1 ! autovideosink

# video3 (Observe_add Right)
gst-launch-1.0 v4l2src device=/dev/video3 ! video/x-raw,format=UYVY,width=1920,height=1536,framerate=30/1 ! autovideosink
```

**정상 작동 시**: 카메라 영상이 화면에 표시됨
**ESC 키**: 테스트 종료

---

## 🔍 문제 해결

### "Device or resource busy" 에러

다른 프로그램이 카메라를 사용 중입니다:

```bash
# 실행 중인 Python 프로세스 확인
ps aux | grep python3

# 종료 (필요시)
pkill -f JETSON2_INTEGRATED.py
```

### 드라이버가 로드되지 않음

```bash
# 드라이버 상태 확인
lsmod | grep gmsl

# 출력 예시:
# sgx_yuv_gmsl2          24576  0
# max96712               20480  1 sgx_yuv_gmsl2
```

로드되지 않았다면:
1. 드라이버 파일 존재 확인
2. 커널 버전 호환성 확인
3. `dmesg | tail -50` 로그 확인

### 카메라가 /dev/video*에 없음

```bash
# 시스템 로그 확인
dmesg | grep -i camera
dmesg | grep -i gmsl

# 드라이버 재로드
cd ~/jetson-camera-monitor/camera_autostart
sudo rmmod sgx_yuv_gmsl2 max96712
sudo ./camera_driver_autoload.sh
```

---

## 📋 카메라 할당

| Device | 용도 | 위치 |
|--------|------|------|
| /dev/video0 | 🍳 Frying AI | 왼쪽 |
| /dev/video1 | 🍳 Frying AI | 오른쪽 |
| /dev/video2 | 🥘 Observe_add | 왼쪽 |
| /dev/video3 | 🥘 Observe_add | 오른쪽 |

---

## ⚙️ 자동 시작 설정 (선택사항)

부팅 시 자동으로 드라이버를 로드하려면:

```bash
# Systemd 서비스 생성
sudo nano /etc/systemd/system/gmsl-camera.service
```

서비스 파일 내용:
```ini
[Unit]
Description=GMSL Camera Driver Auto-load
After=network.target

[Service]
Type=oneshot
ExecStart=/home/dkuyj/jetson-camera-monitor/camera_autostart/camera_driver_autoload.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

활성화:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gmsl-camera.service
sudo systemctl start gmsl-camera.service
```

---

## 📝 참고사항

1. **카메라 연결 순서**: 물리적 연결 순서와 video 번호가 일치해야 함
2. **전원**: GMSL 카메라는 충분한 전원 공급 필요
3. **케이블**: GMSL 케이블 길이/품질이 신호에 영향을 줄 수 있음
4. **해상도**: 1920x1536 (기본), 변경 시 config_jetson2.json 수정 필요

---

## ✅ 설정 완료 체크리스트

- [ ] 4개 카메라 물리적 연결 완료
- [ ] `sudo ./camera_driver_autoload.sh` 실행 완료
- [ ] `ls /dev/video*` 에서 video0~3 확인
- [ ] GStreamer로 모든 카메라 테스트 완료
- [ ] JETSON2_INTEGRATED.py 실행 시 4개 카메라 모두 표시됨

모두 체크되면 시연 준비 완료! 🎉
