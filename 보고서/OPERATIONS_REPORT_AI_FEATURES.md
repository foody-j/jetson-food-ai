# AI 기능 운영 보고서 (야간 감시/사람 감지/바켓 감지/릴레이 ON-OFF 포함)

작성일: 2026-02-02

본 문서는 현재 운영 중인 **AI 기능 전체 흐름**을 보고서 형태로 정리한 문서이다. 야간 감시, 주간 사람 감지, 바켓(Observe_add) 감지, 릴레이 ON/OFF, MQTT 통신, 데이터 저장까지 운영 관점에서 상세히 기술한다.

---

## 1) 시스템 개요

### 1.1 Jetson #1 (사람 감지 + 볶음 모니터링)
- 메인 프로그램: `jetson1_monitoring/JETSON1_INTEGRATED.py`
- 카메라 구성: GMSL 3대
  - 사람 감지: 1대
  - 볶음 모니터링: 좌/우 2대
- 역할: **주간 사람 감지 + 야간 감시 + 릴레이 제어**

### 1.2 Jetson #2 (튀김 AI + 바켓 감지)
- 메인 프로그램: `jetson2_frying_ai/JETSON2_INTEGRATED.py`
- 카메라 구성: 4대
  - 튀김 AI: 좌/우 2대
  - Observe_add 바켓 감지: 좌/우 2대
- 역할: **튀김 상태 추론 + 바켓(Observe_add) 감지 + MQTT 상태 발행**

---

## 2) 주간 사람 감지 (Jetson #1)

### 2.1 동작 목적
- 주간에 **사람 감지** 시 로봇PC/장비 전원을 **자동 ON**
- 감지 지속 시간을 만족해야 ON 신호 발행

### 2.2 설정 (config.json)
파일: `jetson1_monitoring/config.json`

- `mode`: `auto` (주간/야간 자동 전환)
- `day_start`: `04:00`
- `day_end`: `21:00`
- `yolo_model`: `yolo12n.pt`
- `yolo_confidence`: `0.7`
- `yolo_imgsz`: `416`
- `detection_hold_sec`: `2`

### 2.3 동작 시나리오 (운영 기준)
- **주간 시간대**에 YOLO로 사람을 지속 감지
- 감지 지속 시간이 `detection_hold_sec` 이상일 경우
  - MQTT로 `ON` 메시지 전송
  - 릴레이 ON 펄스 또는 연속 출력

---

## 3) 야간 감시 (Jetson #1)

### 3.1 동작 목적
- 야간에는 사람이 없는 상태를 확인하여 **전원 OFF**
- 이후에는 모션 감지 기반으로 스냅샷을 저장해 **야간 모니터링**

### 3.2 설정 (config.json)
- `night_check_minutes`: 야간 미감지 확인 시간 (분)
- `motion_min_area`: 모션 최소 면적 (픽셀)
- `mog2_varthresh`: 배경차분 민감도
- `binary_thresh`: 이진화 임계값
- `snapshot_dir`: `~/Detection`
- `snapshot_cooldown_sec`: 15

### 3.3 동작 흐름
1. 주간 종료 시각 이후 → 야간 모드 전환
2. 야간에서 **N분 동안 사람 미감지**가 확인되면
   - MQTT `OFF` 메시지 전송
   - 릴레이 OFF 펄스 또는 LOW 출력
3. 이후 야간에는 모션 감지 시 스냅샷 저장

### 3.4 야간 스냅샷 저장 구조
```
~/Detection/
└── YYYYMMDD/
    ├── HHMMSS.jpg
    ├── HHMMSS.jpg
    └── ...
```

---

## 4) 릴레이 ON/OFF 제어 (Jetson #1)

### 4.1 역할
- 로봇PC/설비 전원을 자동 제어
- 사람 감지/야간 미감지 결과를 기반으로 ON/OFF 제어

### 4.2 설정 (config.json)
- `relay_mode`: `pulse` 또는 `continuous`
- `auto_relay_enabled`: true/false
- `periodic_off_pulse_enabled`: 야간 주기적 OFF 펄스
- `periodic_off_pulse_interval_min`: 0.05 (기본값 예시)

### 4.3 제어 방식
- **ON**: 사람 감지 지속 시간 만족 시 MQTT `ON` + GPIO HIGH
- **OFF**: 야간 미감지 조건 만족 시 MQTT `OFF` + GPIO LOW
- 필요 시 주기적 OFF 펄스로 로봇PC 상시전원 유지 시 안정화

---

## 5) 바켓 감지 (Observe_add, Jetson #2)

### 5.1 동작 목적
- 바켓 투입/상태를 **Observe_add 모델**로 인식
- 좌/우 카메라별 상태를 분리 관리

### 5.2 설정 (config_jetson2.json)
파일: `jetson2_frying_ai/config_jetson2.json`

- `observe_enabled`: true
- `observe_left_enabled`: true
- `observe_right_enabled`: true
- `observe_left_seg_model`: `observe_add/best_io.pt`
- `observe_left_cls_model`: `observe_add/best_fe.pt`

### 5.3 동작 흐름
- 카메라 프레임 입력 → YOLO 세그/분류 → 상태 추론
- 결과는 MQTT 상태 payload 내 `observe.left/right`에 반영

---

## 6) 튀김 AI (Jetson #2)

### 6.1 모델 및 입력
- 모델: `frying_seg_v3.pt` (YOLOv8-seg)
- 입력 크기: `frying_seg_imgsz = [800, 540]`
- 원본 프레임(1920x1536)을 YOLO가 내부 letterbox 처리

### 6.2 동작 흐름
- 음식 영역 마스크 추출 → 색상 특징 계산 → Lift Tracker 기반 완료 판단
- 결과는 로봇PC 상태와 결합하여 **DISCHARGE 판정 로직**에 활용

---

## 7) 진동 센서 감지 (운영 기준)

### 7.1 현재 운영 방식 (룰/통계 기반)
- Jetson2 통합에서 진동 측정을 요청하면 별도 프로세스가 실행됨\n+- 베이스라인 파일(`vibration_baseline_jetson2.json`)을 기준으로 **velocity magnitude p99** 초과 여부로 정상/비정상 판정\n+- 장점: 경량, 설명 가능, 운영 안정성 높음\n+- 한계: 환경 변화(설치/부하/바닥 상태)에 민감 → 주기적 베이스라인 재측정 필요\n+
### 7.2 향후 고도화 방향 (CNN/FFT 이미지 기반, 연구/로드맵)
- 개념: 진동 FFT 스펙트럼을 이미지로 변환 → CNN으로 정상/이상 분류\n+- 기대효과: 패턴 기반 분류로 복합 이상 감지 가능\n+- 운영 현실 조건:\n+  - 충분한 라벨 데이터 필요(정상/이상 각각 수십~수백 이상)\n+  - 환경 변화 시 재학습 필요\n+  - 모델 배포/검증/관리 비용 증가\n+- 결론: **현재는 룰 기반 운영 유지**, CNN은 **향후 데이터 확보 후 단계적 도입 검토**\n+
---

## 8) MQTT 통신 구조

### 8.1 Jetson #1 → 로봇PC
- 사람 감지 결과에 따라 `robot/control` 토픽으로 ON/OFF 전송
- 릴레이 상태를 `jetson1/relay/status`로 전송

### 8.2 Jetson #2 → 로봇PC
- `jetson2/status` 토픽으로 통합 상태 발행
- payload 내 항목:
  - `frying.left/right` (COOKING/DISCHARGE)
  - `observe.left/right`
  - `vibration.status`

---

## 9) 야간 감지 리뷰 기능 (Jetson #1)

### 9.1 목적
- 야간에 저장된 스냅샷을 **아침 시간에 자동 리뷰**

### 9.2 설정 (config.json)
- `night_review_enabled`: true
- `night_review_time`: `08:00`
- `night_review_duration_min`: 10
- `night_review_auto_archive`: true

---

## 10) 사람 감지 데이터 수집 (Jetson #1)

### 10.1 목적
- 로봇 회사 요청에 따른 주간 사람 감지 데이터 수집

### 10.2 설정
- `person_data_collection_enabled`: true
- `person_collection_start_time`: `08:30`
- `person_collection_end_time`: `12:00`
- `person_collection_interval_sec`: 5
- `person_collection_save_dir`: `AI_Data/PersonData`

---

## 11) 운영 참고 사항

- 사람 감지 ON/OFF는 **시간대 기준(주간/야간)**과 **지속 감지 조건**을 동시에 만족해야 함
- 야간에는 **미감지 누적 시간**이 OFF를 결정하며, 이후 모션 감지로 스냅샷 저장
- 릴레이 모드는 `pulse/continuous`로 운영 환경에 맞춰 선택
- 바켓 감지(Observe_add)는 좌/우 분리 모델로 운영되어 상태가 독립적으로 출력됨

---

## 12) 주요 파일 요약

- `jetson1_monitoring/JETSON1_INTEGRATED.py` : 사람 감지 + 릴레이 ON/OFF 통합
- `jetson1_monitoring/config.json` : 사람 감지/야간 감시/릴레이 설정
- `jetson2_frying_ai/JETSON2_INTEGRATED.py` : 튀김 AI + Observe_add
- `jetson2_frying_ai/config_jetson2.json` : 튀김/바켓 모델 설정
- `jetson1_monitoring/JETSON1_GUIDE.md` : Jetson1 상세 운영 가이드

---

## 13) 결론

현재 운영 중인 AI 기능은 **주간 사람 감지 기반 자동 ON**, **야간 미감지 기반 OFF 및 모션 스냅샷**, **바켓 감지(Observe_add)**, **튀김 상태 추론**, **릴레이 제어**, **MQTT 상태 발행**의 형태로 유기적으로 연결되어 있다. 현장 운용 시 각 기능은 설정 파일을 통해 민감도와 시간대, 저장 정책을 조정할 수 있으며, 야간 감시부터 주간 전원 자동 제어까지 전 공정을 자동화하는 구조로 설계되어 있다.
