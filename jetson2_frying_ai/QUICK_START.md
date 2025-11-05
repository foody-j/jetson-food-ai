# 🚀 Jetson #2 - 빠른 시작 가이드

**내일 시연을 위한 체크리스트**

---

## ⚡ 3단계 시작

### 1️⃣ 카메라 드라이버 로드 (필수!)

```bash
cd ~/jetson-camera-monitor/camera_autostart
sudo ./camera_driver_autoload.sh
```

### 2️⃣ 카메라 확인

```bash
ls /dev/video*
# video0, video1, video2, video3 모두 있어야 함
```

### 3️⃣ 프로그램 실행

```bash
cd ~/jetson-camera-monitor/jetson2_ai
python3 JETSON2_INTEGRATED.py
```

---

## 🎮 시연 시나리오

### 화면 구성
```
┌─────────────────────────────────────────┐
│   🤖 Jetson #2 - AI 모니터링 시스템     │
├──────────────────┬──────────────────────┤
│  🍳 볶음 AI - 왼쪽 │  🍳 볶음 AI - 오른쪽  │
│  [카메라 영상]    │  [카메라 영상]       │
│  온도: -- °C     │  온도: -- °C        │
│  갈색: --% 황금: --% │  갈색: --% 황금: --% │
├──────────────────┼──────────────────────┤
│  🥘 바켓 감지 - 왼쪽 │  🥘 바켓 감지 - 오른쪽 │
│  [카메라 영상]    │  [카메라 영상]       │
│  상태: 대기 중    │  상태: 대기 중      │
└──────────────────┴──────────────────────┘
 [볶음 AI 시작] [볶음 AI 중지]
 [바켓 감지 시작] [바켓 감지 중지] [종료]
```

### 시연 순서

#### 1. 🍳 Frying AI (튀김유 색상 분석)

1. **"볶음 AI 시작"** 버튼 클릭
2. 실시간으로 표시됨:
   - 튀김유 영역에 **초록색 오버레이**
   - **Brown ratio**: 갈색 비율 (익음 정도)
   - **Golden ratio**: 황금색 비율 (완벽한 튀김)
   - **Area**: 음식 영역 비율
3. MQTT로 온도 전송 시 온도도 표시됨

**포인트**: "음식이 익을수록 갈색 비율이 증가하고, 황금색이 나타나면 최적 상태입니다"

#### 2. 🥘 Observe_add (바켓 감지)

1. **"바켓 감지 시작"** 버튼 클릭
2. 바켓에 음식을 넣거나 빼기
3. 상태 변화 확인:
   - **FILLED**: 음식 있음 (빨간색)
   - **EMPTY**: 비어있음 (회색)
   - **NO_BASKET**: 바켓 감지 안됨
4. MQTT로 상태 자동 전송

**포인트**: "7프레임 다수결 투표로 안정적인 감지, 상태 변화 시 자동으로 MQTT 전송"

#### 3. 종합 시연

- F11 눌러 **Fullscreen** 모드 전환
- 4개 카메라 모두 작동하는 모습 보여주기
- 실시간 AI 분석 결과 표시

---

## 🔧 MQTT 테스트 (선택사항)

### 온도 전송 테스트

다른 터미널에서:

```bash
# 왼쪽 튀김유 온도 전송
mosquitto_pub -h localhost -t "frying/oil_temp/left" -m "170.5"

# 오른쪽 튀김유 온도 전송
mosquitto_pub -h localhost -t "frying/oil_temp/right" -m "172.3"
```

GUI에서 온도가 업데이트됨!

### 바켓 상태 수신 테스트

```bash
# 바켓 상태 구독
mosquitto_sub -h localhost -t "observe/status"

# 바켓에 음식 넣으면:
# LEFT:FILLED
# RIGHT:EMPTY
# 등의 메시지 수신
```

---

## ⚠️ 문제 해결

### 카메라가 안 보임

```bash
# 1. 드라이버 재로드
cd ~/jetson-camera-monitor/camera_autostart
sudo rmmod sgx_yuv_gmsl2 max96712
sudo ./camera_driver_autoload.sh

# 2. 카메라 확인
ls /dev/video*

# 3. 프로그램 재실행
cd ~/jetson-camera-monitor/jetson2_ai
python3 JETSON2_INTEGRATED.py
```

### 특정 카메라만 안 나옴

```bash
# GStreamer로 개별 테스트
gst-launch-1.0 v4l2src device=/dev/video3 ! video/x-raw,format=UYVY,width=1920,height=1536,framerate=30/1 ! autovideosink
```

### "Device busy" 에러

```bash
# 실행 중인 프로세스 종료
pkill -f JETSON2_INTEGRATED.py

# 1초 대기 후 재실행
sleep 1
python3 JETSON2_INTEGRATED.py
```

### NumPy 에러

```bash
# NumPy 다운그레이드 (필요시)
pip3 install "numpy<2"
```

---

## 📋 시연 전 체크리스트

- [ ] 4개 카메라 모두 연결됨
- [ ] `sudo ./camera_driver_autoload.sh` 실행 완료
- [ ] `/dev/video0~3` 모두 존재
- [ ] GStreamer 테스트로 4개 카메라 모두 확인
- [ ] JETSON2_INTEGRATED.py 실행 → 4개 카메라 표시됨
- [ ] "볶음 AI 시작" → 색상 분석 작동 확인
- [ ] "바켓 감지 시작" → 바켓 감지 작동 확인
- [ ] F11 Fullscreen 작동 확인
- [ ] MQTT 연결 (선택사항) 확인

---

## 🎯 핵심 메시지

**Jetson #2 시스템:**
- ✅ **4-Camera 동시 모니터링**
- ✅ **실시간 AI 분석** (튀김유 색상 + 바켓 감지)
- ✅ **MQTT 통신** (온도 수신, 상태 전송)
- ✅ **직관적인 GUI** (JETSON1과 동일한 스타일)

**기술 스택:**
- GStreamer: UYVY 포맷 처리
- HSV Segmentation: 튀김유 색상 분석
- YOLO: 바켓 segmentation + classification
- MQTT: 실시간 데이터 통신

모든 준비 완료! 시연 성공을 기원합니다! 🎉
