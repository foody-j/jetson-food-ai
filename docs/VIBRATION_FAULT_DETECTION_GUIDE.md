# 진동센서 고장 감지 가이드

## 개요
진동센서 프로그램에서 고장을 자동으로 감지하고 알림을 제공하는 기능입니다.

## 설정 파일: `vibration_config.json`

### 기본 설정

```json
{
  "window_sec": 5.0,
  "y_axis_limits": {
    "acc": {"min": -20, "max": 20},
    "vel": {"min": -100, "max": 100},
    "disp": {"min": 0, "max": 100000},
    "fft": {"min": 0, "max": 1000}
  },
  "auto_scale": false,
  "fault_detection": {
    "enabled": true,
    "methods": {...},
    "alert": {...}
  }
}
```

### 축 범위 설정

- **`window_sec`**: X축 시간 범위 (초)
  - 기본값: 5.0 (최근 5초간 데이터 표시)
  - 더 긴 시간을 보려면: 10.0, 20.0 등

- **`y_axis_limits`**: Y축 범위 고정
  - `acc`: 가속도 범위 (g)
  - `vel`: 속도 범위 (mm/s)
  - `disp`: 변위 범위 (um)
  - `fft`: FFT 스펙트럼 범위

- **`auto_scale`**:
  - `false` - Y축 고정 (진동 변화 비교 용이)
  - `true` - Y축 자동 조정

## 고장 감지 방법

### 1. 임계값 기반 감지 (Threshold)

가장 간단한 방법. 절대값이 임계값을 초과하면 고장으로 판정.

```json
"threshold": {
  "enabled": true,
  "disp_max": 5000,    // 변위 최대값 (um)
  "vel_max": 500,      // 속도 최대값 (mm/s)
  "acc_max": 10        // 가속도 최대값 (g)
}
```

**예시:**
- 변위가 5000 um를 초과하면 → 고장 감지
- 속도가 500 mm/s를 초과하면 → 고장 감지
- 가속도가 10 g를 초과하면 → 고장 감지

**장점**: 간단하고 즉시 반응
**단점**: 정상 범위를 수동으로 설정해야 함

---

### 2. 베이스라인 기반 감지 (Baseline)

정상 상태의 데이터를 수집하고, 통계적으로 이상을 감지.

```json
"baseline": {
  "enabled": true,
  "sigma_multiplier": 3.0  // 평균 + 3σ
}
```

**사용 방법:**
1. 정상 작동 중일 때 프로그램 실행
2. 키보드 **'b'** 키 누름
3. 10분간 정상 데이터 수집
4. 자동으로 통계 계산 및 저장 (`baseline_stats.json`)
5. 이후부터 자동 감지

**예시:**
- 정상 변위 평균 = 100 um, 표준편차 = 20 um
- 임계값 = 100 + 3×20 = 160 um
- 변위가 160 um 초과 → 이상 감지

**장점**: 정상 범위를 자동으로 학습
**단점**: 초기 베이스라인 수집 필요

---

### 3. 주파수 범위 기반 감지 (Frequency)

특정 주파수 범위에서 진동이 발생하면 고장으로 판정.

```json
"frequency": {
  "enabled": false,
  "abnormal_ranges": [
    {"min": 50, "max": 70},     // 50~70 Hz
    {"min": 120, "max": 150}    // 120~150 Hz
  ]
}
```

**예시:**
- 모터 공진 주파수: 60 Hz
- FFT에서 60 Hz 피크가 감지되면 → 고장 감지

**장점**: 특정 고장 패턴 감지
**단점**: 고장 주파수를 미리 알아야 함

---

## 알림 설정

```json
"alert": {
  "console_print": true,
  "save_event_log": true,
  "event_log_path": "~/data/vibration_data/fault_events.log"
}
```

### 콘솔 출력
```
============================================================
[고장 감지] UID 0x50 - 2024-11-05 20:15:30
  - 변위 초과: 6234.5 um > 5000 um
  - 베이스라인 대비 이상 진동 감지
  현재값: ACC=(1.23, 2.45, 3.67) g
         VEL=(234.5, 456.7, 678.9) mm/s
         DISP=(6234.5, 1234.5, 2345.6) um
         FFT=(45.2, 67.8, 89.1) Hz
============================================================
```

### 파일 로그
고장 이벤트가 `fault_events.log` 파일에 저장됩니다.

---

## 추천 설정

### 일반 기계 모니터링
```json
"fault_detection": {
  "enabled": true,
  "methods": {
    "threshold": {
      "enabled": true,
      "disp_max": 5000,
      "vel_max": 500,
      "acc_max": 10
    },
    "baseline": {
      "enabled": true,
      "sigma_multiplier": 3.0
    }
  }
}
```

### 고장 이력 분석 필요 시
```json
"alert": {
  "console_print": true,
  "save_event_log": true,
  "event_log_path": "~/data/vibration_data/fault_events.log"
}
```

### 테스트/디버그 시
```json
"fault_detection": {
  "enabled": false
}
```

---

## 사용 흐름도

```
1. 진동센서 프로그램 실행
   ↓
2. [선택] 'b' 키로 베이스라인 수집 (10분)
   ↓
3. 실시간 모니터링 시작
   ↓
4. 고장 감지 시:
   - 콘솔 출력 (빨간색 경고)
   - 로그 파일 저장 (설정 시)
   - 그래프 타이틀에 [⚠ 이상 감지] 표시
```

---

## 문제 해결

### Q: 고장 감지가 너무 민감해요
**A**: `sigma_multiplier`를 3.0 → 4.0 이상으로 증가

### Q: 정상인데 계속 고장으로 나와요
**A**:
1. 베이스라인 재수집 (정상 상태에서 'b' 키)
2. 임계값 증가 (`disp_max`, `vel_max` 등)

### Q: 고장을 놓치는 것 같아요
**A**:
1. `sigma_multiplier`를 2.5로 감소
2. 임계값 감소
3. 여러 방법 동시 활성화

### Q: 베이스라인 파일이 사라졌어요
**A**: `~/data/vibration_data/baseline_stats.json` 삭제 후 재수집

---

## 고급 활용

### MQTT 연동 (향후 추가 예정)
고장 감지 시 MQTT로 알림을 전송하여:
- Jetson #1, #2에서 알림 표시
- 원격 모니터링
- 자동 장비 정지

### 머신러닝 모델 (향후 추가 예정)
정상/고장 패턴을 학습하여 더 정확한 감지

---

## 참고

- 센서 사양서: WitMotion WT-VB02-485
- 측정 단위:
  - 가속도: g (중력가속도)
  - 속도: mm/s
  - 변위: um (마이크로미터)
  - 주파수: Hz
