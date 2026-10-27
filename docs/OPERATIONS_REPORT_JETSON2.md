# Jetson2 운영 시스템 보고서 (현재 운용 기준)

작성일: 2026-02-02

## 1) 개요
본 문서는 주방 튀김 공정에서 운용 중인 Jetson2 통합 AI 시스템의 **현재 동작 방식**, **모델 구성**, **MQTT 통신**, **진동 센서 감지**, **데이터 수집 흐름**을 상세히 기록한 보고서이다. 현장에서 운영되는 실제 코드 흐름을 기준으로 작성되었으며, 모델 교체(v3) 및 추론 입력 크기(800x540) 기준으로 정리했다.

---

## 2) 시스템 구성

### 2.1 하드웨어
- Jetson Orin #2 (주방 튀김 라인)
- 카메라 4대 (video0~video3)
  - 튀김 AI: video0(좌), video1(우)
  - Observe_add: video2(좌), video3(우)
- RS485 진동 센서 (USB-Serial CH340 사용 가능)
- 릴레이 제어 (Jetson.GPIO)

### 2.2 소프트웨어 구성
- 통합 실행 파일: `jetson2_frying_ai/JETSON2_INTEGRATED.py`
- 튀김 세그멘테이션 모델: `frying_seg_v3.pt` (YOLOv8-seg)
- Observe_add 모델: `observe_add/best_io.pt`, `observe_add/best_fe.pt` 등
- MQTT 통신: `src/communication/mqtt_client.py`
- 진동 분석 스크립트: `test_vibration_pymodbus3_finalrev.py`

---

## 3) AI 추론 동작 흐름

### 3.1 실행
```bash
cd /home/yjk/jetson-food-ai/jetson2_frying_ai
python3 JETSON2_INTEGRATED.py
```

### 3.2 튀김 세그멘테이션 (Frying AI)
- 모델 로딩: `frying_seg_v3.pt`
- 추론 입력 크기: **800x540**
  - 설정 위치: `jetson2_frying_ai/config_jetson2.json`
  - 키: `frying_seg_imgsz: [800, 540]`
- 추론은 **원본 프레임(1920x1536)**을 넣고, YOLO가 내부에서 letterbox로 800x540으로 변환

### 3.3 FoodSegmenter 구조
- 파일: `jetson2_frying_ai/frying_segmenter.py`
- YOLO 모델을 통해 마스크 추출 → 음식 영역 비율 및 HSV/LAB 색상 특징 계산
- 결과는 Lift Event Tracker에 전달되어 "탈탈" 이벤트 판단과 완료 상태 추적에 사용됨

---

## 4) MQTT 통신 및 DISCHARGE 로직

### 4.1 기본 MQTT 설정
- 설정 파일: `jetson2_frying_ai/config_jetson2.json`
- 주요 항목
  - `mqtt_enabled: true`
  - `mqtt_broker: 192.168.0.100` (로봇PC)
  - `mqtt_topic_status: jetson2/status`

### 4.2 상태 발행 구조
- 통합 상태는 **단일 토픽**(`jetson2/status`)으로 주기적으로 발행됨
- 발행 주기: `mqtt_publish_interval` (초)
- 전송 payload 예시 구조:
```json
{
  "device_id": "jetson2",
  "timestamp": "2026-02-02 13:10:22",
  "frying": {
    "left": "COOKING",
    "right": "DISCHARGE"
  },
  "observe": {"left": "UNKNOWN", "right": "UNKNOWN"},
  "vibration": {"status": "NORMAL"}
}
```

### 4.3 DISCHARGE 판정 로직
- 로봇PC에서 수신하는 `HR/Status` 내 **RunningTime** 과 **TargetTime**을 비교
- **`running_time >= target_time`**이면 DISCHARGE 상태로 전환
- DISCHARGE는 별도 토픽이 아니라 `jetson2/status`의 `frying.left/right` 값으로 전달됨

### 4.4 시간 파싱
- 지원 포맷
  - `HH:MM:SS`
  - `MM:SS`
  - `10분 15초` / `1시간 2분 3초`
  - 숫자만 있을 경우 초로 해석

---

## 5) 데이터 수집 (Data Collection)

### 5.1 기본 원칙
- 투입/조리/배출 상태 변화에 따라 수집 시작/중지
- 배출 후 `recording_delay_after_discharge` 초 만큼 추가 녹화

### 5.2 저장 주기
- 일반: `data_collection_interval_normal`
- RBMotion 발생 시: `data_collection_interval_fast`

---

## 6) 진동 센서 감지 시스템

### 6.1 실행 경로
- Jetson2 통합에서 진동 체크를 시작하면 `test_vibration_pymodbus3_finalrev.py` 실행
- 실행 시 baseline 파일을 사용해 정상/비정상 판정

### 6.2 사용 기준 (Jetson2 기준)
- 베이스라인 파일: `vibration_baseline_jetson2.json`
- 판정 기준:
  - `velocity_magnitude_p99` 초과 시 ABNORMAL
  - 현재 기준 값: **11810.6613 mm/s**

### 6.3 별도 설정 파일
- `vibration_config.json`에 하드 임계치가 있으나, **Jetson2 통합 판단 로직에는 직접 사용되지 않음**

---

## 7) 모델 교체 절차 (v3 반영 기준)

1) `fry-doneness-ai`에서 최신 모델 확인
```bash
cd /home/yjk/fry-doneness-ai
git pull
```

2) 모델 복사
```bash
cp /home/yjk/fry-doneness-ai/runs/segment/frying_seg_v3_20260202_110544/weights/best.pt \
  /home/yjk/jetson-food-ai/jetson2_frying_ai/frying_seg_v3.pt
```

3) 설정 업데이트
```json
"frying_seg_model": "frying_seg_v3.pt",
"frying_seg_imgsz": [800, 540]
```

---

## 8) 수동 검증 (프레임 단위 추론 확인)

### 8.1 키보드 기반 뷰어
```bash
cd /home/yjk/jetson-food-ai/jetson2_frying_ai
python3 manual_frame_infer.py /home/yjk/AI_Data/pot1/session_YYYYMMDD_xxxxxx
```

### 8.2 키 입력
- `n` 또는 → : 다음 프레임
- `p` 또는 ← : 이전 프레임
- `q` 또는 Esc : 종료

---

## 9) 운영 시 참고 사항

- DISCHARGE는 Jetson2 내부 AI 결과가 아니라 **Robot PC 시간 값 기반**으로 결정됨
- 추론 입력 크기가 학습과 다르면 성능 저하 가능 → 반드시 `frying_seg_imgsz`를 학습과 동일하게 유지
- 진동 임계치가 너무 민감하면 베이스라인 재측정 또는 p99/3σ 조정 필요

---

## 10) 주요 파일 목록

- `jetson2_frying_ai/JETSON2_INTEGRATED.py` : 통합 실행
- `jetson2_frying_ai/config_jetson2.json` : Jetson2 설정
- `jetson2_frying_ai/frying_seg_v3.pt` : v3 모델
- `jetson2_frying_ai/frying_segmenter.py` : 세그멘테이션 로직
- `jetson2_frying_ai/manual_frame_infer.py` : 수동 프레임 추론
- `test_vibration_pymodbus3_finalrev.py` : 진동 체크
- `vibration_baseline_jetson2.json` : Jetson2 베이스라인

---

## 11) 결론
현재 Jetson2 시스템은 v3 세그멘테이션 모델 기반으로 튀김 상태를 추론하고, 로봇PC에서 전달되는 시간 정보를 기반으로 DISCHARGE 상태를 판정하여 MQTT로 상태를 주기적으로 발행한다. 진동 센서는 별도 체크 프로세스를 통해 velocity magnitude p99 기준으로 이상을 판별하며, 운용 중 임계치 조정은 베이스라인 파일에서 관리한다.
