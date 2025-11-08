# 🎓 AI 학습 전략 문서

**작성일**: 2025-01-05
**버전**: 1.0
**목적**: 각 AI 모델의 학습 전략 및 데이터 수집 요구사항 정리

---

## 📋 목차

1. [튀김 AI (Frying AI)](#1-튀김-ai-frying-ai)
2. [볶음 모니터링 (Stir-Fry)](#2-볶음-모니터링-stir-fry)
3. [바켓 감지 (Bucket Detection)](#3-바켓-감지-bucket-detection)
4. [진동 센서 (Vibration Sensor)](#4-진동-센서-vibration-sensor)

---

## 1. 튀김 AI (Frying AI)

### 🎯 목표
- 튀김 상태 실시간 분석 (익음 정도, 색상 변화)
- 최적 조리 시점 판단
- 과조리 방지

### 📊 데이터 수집 전략

#### 필수 데이터
✅ **원본 이미지**:
- 카메라 0 (왼쪽), 카메라 1 (오른쪽)
- 1280x720, JPEG
- 5초 간격

✅ **MQTT 메타데이터** (필수!):
```json
{
  "timestamp": "2025-01-05 14:30:30.123",
  "type": "oil_temperature",
  "position": "left",
  "value": 175.5,
  "unit": "celsius"
}
```

✅ **향후 추가 필요한 메타데이터**:
```json
{
  "timestamp": "2025-01-05 14:30:00.000",
  "type": "cooking_start",
  "food_type": "새우튀김",
  "quantity": 10,
  "target_temperature": 180.0,
  "recipe_id": "shrimp_001"
},
{
  "timestamp": "2025-01-05 14:32:30.000",
  "type": "cooking_end",
  "result": "success",
  "final_color": "golden"
}
```

### 🔬 현재 접근 방식
**비전 기반 로직 (Rule-based)**:
- HSV 색상 분석
- Brown ratio (갈색 비율) 계산
- Golden ratio (황금색 비율) 계산
- 임계값 기반 판단

### 🎓 학습 전략

#### Phase 1: 데이터 수집 (현재)
1. **다양한 튀김 종류** 수집:
   - 새우튀김
   - 치킨
   - 감자튀김
   - 야채튀김
   - 기타

2. **다양한 조리 단계** 수집:
   - 투입 직후 (생)
   - 초기 (20%)
   - 중간 (50%)
   - 완료 (80%)
   - 황금색 (100%)
   - 과조리 (120%+)

3. **메타데이터 필수 포함**:
   - 튀김유 온도 (실시간)
   - 음식 종류
   - 조리 시작/종료 시간
   - 심부 온도 (가능하면)

#### Phase 2: 라벨링
```
image_001.jpg → golden (완벽)
image_002.jpg → brown (익음)
image_003.jpg → raw (덜 익음)
image_004.jpg → burnt (과조리)
```

**메타데이터 활용**:
- 온도 175-180°C + Golden → "최적"
- 온도 190°C + Brown → "과조리 위험"
- 온도 160°C + Raw → "온도 낮음"

#### Phase 3: 모델 학습
**옵션 1: Classification (분류)**
- 입력: 튀김 이미지
- 출력: `[raw, cooking, golden, burnt]`
- 모델: EfficientNet, MobileNet 등

**옵션 2: Regression (회귀)**
- 입력: 튀김 이미지 + 온도
- 출력: 익음 정도 (0-100%)
- 모델: Custom CNN + Temperature input

**옵션 3: Multimodal (멀티모달)**
- 입력: 이미지 + 온도 + 시간
- 출력: 최적 조리 시점 예측
- 모델: Vision Transformer + 메타데이터

#### Phase 4: 배포
- 학습된 `.pt` 모델만 Jetson에 복사
- `config_jetson2.json` 업데이트
- 재시작

### 📝 데이터셋 구조 예시
```
frying_dataset/
├── shrimp/
│   ├── raw/
│   │   ├── img_001.jpg (메타: 160°C, 0초)
│   │   └── img_002.jpg (메타: 165°C, 10초)
│   ├── cooking/
│   │   └── img_003.jpg (메타: 175°C, 60초)
│   ├── golden/
│   │   └── img_004.jpg (메타: 180°C, 120초)
│   └── burnt/
│       └── img_005.jpg (메타: 190°C, 180초)
├── chicken/
│   └── ...
└── metadata.json
```

---

## 2. 볶음 모니터링 (Stir-Fry)

### 🎯 목표
- 볶음 상태 실시간 모니터링
- 조리 과정 기록
- 품질 관리

### 📊 데이터 수집 전략

#### 필수 데이터
✅ **원본 이미지**:
- Jetson #1, 카메라 1 (왼쪽), 카메라 2 (오른쪽)
- 1920x1536, JPEG
- 수동 녹화 시작/종료

✅ **MQTT 메타데이터** (필수!):
```json
{
  "timestamp": "2025-01-05 14:30:00.000",
  "type": "stirfry_start",
  "food_type": "볶음밥",
  "recipe_id": "friedrice_001",
  "target_temp": 200.0
},
{
  "timestamp": "2025-01-05 14:35:00.000",
  "type": "stirfry_end",
  "result": "success"
}
```

### 🔬 현재 접근 방식
- 수동 녹화
- 타임스탬프 기반 저장
- 사람이 직접 확인

### 🎓 학습 전략

#### Phase 1: 데이터 수집
1. **다양한 볶음 종류**:
   - 볶음밥
   - 볶음면
   - 야채볶음
   - 기타

2. **조리 단계별 수집**:
   - 투입 직후
   - 볶는 중 (초기)
   - 볶는 중 (중기)
   - 볶는 중 (후기)
   - 완료

3. **메타데이터 포함**:
   - 음식 종류
   - 조리 시작/종료
   - 조리 시간
   - 팬 온도 (가능하면)

#### Phase 2: 비전 로직 개발
**현재 방식 유지 + 개선**:
- 색상 변화 감지
- 연기 감지
- 움직임 감지 (볶는 동작)

#### Phase 3: (선택) AI 모델
- 과조리 감지
- 완료 시점 예측
- 품질 평가

---

## 3. 바켓 감지 (Bucket Detection)

### 🎯 목표
- 바켓 상태 자동 감지: `EMPTY` / `FILLED` / `NO_BASKET`
- 상태 변화 시 MQTT 알림
- 로봇 제어 연동

### 📊 데이터 수집 전략

#### 필수 데이터
✅ **원본 이미지만 필요!** (메타데이터 불필요)
- 카메라 2 (왼쪽), 카메라 3 (오른쪽)
- 1280x720, JPEG
- 5초 간격

✅ **다양한 상태 수집**:
- `EMPTY`: 빈 바켓 (100장+)
- `FILLED`: 가득 찬 바켓 (100장+)
- `PARTIALLY_FILLED`: 반 찬 바켓 (100장+)
- `NO_BASKET`: 바켓 없음 (50장+)

### 🎓 학습 전략

#### Phase 1: 데이터 수집
**시나리오별 수집** (2-3분씩):
1. 빈 바켓 설치 → 2분 촬영 (24장)
2. 바켓에 음식 담기 (반) → 2분 촬영
3. 바켓 가득 채우기 → 2분 촬영
4. 바켓 제거 → 2분 촬영

**10회 반복** → 약 240장 수집 (충분!)

#### Phase 2: 라벨링
```
camera_2/cam2_143030_123.jpg → EMPTY
camera_2/cam2_143035_456.jpg → FILLED
camera_3/cam3_143040_789.jpg → NO_BASKET
```

**YOLO Segmentation 라벨링**:
- `labelImg` 또는 `CVAT` 사용
- 바켓 영역 폴리곤으로 라벨링
- 클래스: `empty`, `filled`, `no_basket`

#### Phase 3: YOLO 모델 학습
**YOLOv8 Segmentation**:
```bash
yolo segment train data=bucket.yaml model=yolov8n-seg.pt epochs=100
```

**데이터셋 구조**:
```
bucket_dataset/
├── images/
│   ├── train/
│   │   ├── img_001.jpg
│   │   └── ...
│   └── val/
│       └── ...
├── labels/
│   ├── train/
│   │   ├── img_001.txt  # YOLO format
│   │   └── ...
│   └── val/
└── bucket.yaml
```

#### Phase 4: 배포
- `best.pt` 모델 Jetson에 복사
- `config_jetson2.json` 업데이트:
  ```json
  {
    "observe_seg_model": "bucket_best.pt"
  }
  ```

---

## 4. 진동 센서 (Vibration Sensor)

### 🎯 목표
- 기계 상태 실시간 모니터링
- 이상 진동 감지
- 고장 예측 (Predictive Maintenance)

### 📊 데이터 수집 전략

#### 필수 데이터
✅ **시계열 센서 데이터**:
- UID 50, 51, 52 (3개 센서)
- 진동 강도 (X, Y, Z 축)
- 주파수 스펙트럼
- 샘플링: 100Hz 이상

✅ **메타데이터**:
```json
{
  "timestamp": "2025-01-05 14:30:00.123",
  "sensor_id": "UID50",
  "machine_id": "fryer_01",
  "machine_state": "running",  # idle, running, error
  "load": 0.7,  # 부하 70%
  "label": "normal"  # normal, abnormal, warning
}
```

### 🔬 현재 접근 방식
**센서 데이터 수집 중**:
- CSV 파일로 저장 중
- 예: `20251105_144526_UID50_vibration.csv`

### 🎓 학습 전략

#### Phase 1: 데이터 수집
**정상 상태** (가장 중요!):
- 아무 문제 없을 때 최소 **1주일** 수집
- 다양한 부하 조건:
  - 유휴 (Idle)
  - 저부하 (20%)
  - 중부하 (50%)
  - 고부하 (80%)

**이상 상태** (레이블링 필요):
- 베어링 마모
- 불균형 (Imbalance)
- 축 정렬 불량 (Misalignment)
- 느슨한 볼트
- (발생 시 즉시 기록)

#### Phase 2: 특징 추출 (Feature Engineering)
**시간 도메인 특징**:
- RMS (Root Mean Square)
- Peak-to-Peak
- Crest Factor
- Kurtosis

**주파수 도메인 특징** (FFT):
- 주파수 스펙트럼
- 주요 주파수 성분
- 고조파 분석

#### Phase 3: 라벨링
```csv
timestamp,sensor_id,rms_x,rms_y,rms_z,freq_peak,label
2025-01-05 14:30:00,UID50,0.5,0.4,0.3,60Hz,normal
2025-01-05 14:30:01,UID50,0.52,0.41,0.31,60Hz,normal
2025-01-05 14:35:00,UID50,1.2,0.9,0.8,120Hz,abnormal
```

#### Phase 4: 모델 학습

**옵션 1: Classical ML (전통적 ML)**
- Random Forest
- SVM
- Gradient Boosting
- 입력: 특징 벡터 (RMS, Peak, FFT 등)
- 출력: `normal` / `abnormal`

**옵션 2: Deep Learning (딥러닝)**
- 1D CNN (시계열 데이터)
- LSTM (장기 의존성)
- Autoencoder (이상 감지)

**추천: 전통적 ML 먼저 시도!**
- 데이터 적어도 시작 가능
- 해석 가능성 높음
- 실시간 처리 빠름

#### Phase 5: 이상 감지 (Anomaly Detection)

**Autoencoder 방식**:
1. 정상 데이터만으로 학습
2. 재구성 오차 (Reconstruction Error) 계산
3. 임계값 초과 → 이상 감지

**장점**:
- 정상 데이터만 있으면 됨
- 새로운 이상 패턴도 감지 가능

#### Phase 6: 배포
- 모델을 Jetson에 배포
- 실시간 추론
- MQTT로 이상 알림

### 📝 데이터셋 구조
```
vibration_dataset/
├── normal/
│   ├── UID50_20250105_143000.csv
│   ├── UID51_20250105_143000.csv
│   └── UID52_20250105_143000.csv
├── abnormal/
│   ├── UID50_20250106_151000.csv (베어링 마모)
│   └── UID51_20250107_120000.csv (불균형)
├── features/
│   ├── features_train.csv
│   └── features_test.csv
└── metadata.json
```

---

## 📊 요약 비교표

| 항목 | 튀김 AI | 볶음 모니터링 | 바켓 감지 | 진동 센서 |
|------|---------|--------------|-----------|----------|
| **데이터 타입** | 이미지 + 메타데이터 | 이미지 + 메타데이터 | 이미지만 | 시계열 + 메타데이터 |
| **메타데이터 필요성** | ✅ 필수 | ✅ 필수 | ❌ 불필요 | ✅ 필수 |
| **수집 방법** | 자동 (5초 간격) | 수동 (녹화) | 자동 (5초 간격) | 자동 (100Hz) |
| **라벨링 난이도** | 중 | 중 | 하 | 고 |
| **학습 방법** | 비전 기반 → AI | 로직 기반 | YOLO Seg | Classical ML / DL |
| **배포 난이도** | 중 | 하 | 하 | 중 |

---

## 🎯 우선순위 및 로드맵

### Phase 1: 데이터 수집 (현재)
- [x] 튀김 AI: 이미지 + MQTT 메타데이터
- [x] 바켓 감지: 이미지만
- [x] 진동 센서: CSV 데이터

### Phase 2: 메타데이터 확장 (1주일)
- [ ] MQTT 프로토콜 확정 (Host PC)
- [ ] 음식 종류, 조리 시작/종료 신호 추가
- [ ] 온도 센서 추가 (심부 온도)

### Phase 3: 라벨링 및 학습 (2주일)
- [ ] 바켓 감지 학습 (가장 쉬움) → 먼저 시작!
- [ ] 튀김 AI 학습 (메타데이터 필수)
- [ ] 진동 센서 특징 추출 및 모델 학습

### Phase 4: 배포 및 검증 (1주일)
- [ ] 모델 Jetson 배포
- [ ] 실환경 테스트
- [ ] 정확도 평가

---

## 💡 핵심 포인트

### ✅ 이해한 내용
1. **튀김/볶음**: 메타데이터(음식종류, 온도, 시간) 필수!
   - 비전만으로는 부족 → 메타데이터로 라벨링 보조

2. **바켓 감지**: 이미지만 있으면 됨!
   - YOLO Segmentation 학습
   - 계속 촬영 → 라벨링 → 학습

3. **진동 센서**: 시계열 데이터 + 기계 상태 메타데이터
   - 정상 데이터 충분히 수집 (1주일+)
   - 특징 추출 → ML 학습

### 📋 다음 단계
1. **MQTT 프로토콜 확정**: Host PC와 협의
2. **바켓 감지 먼저 학습**: 메타데이터 불필요, 빠르게 성과
3. **튀김 AI**: 메타데이터 수집 후 학습
4. **진동 센서**: 정상 데이터 충분히 수집 후 시작

---

**문서 업데이트**: 2025-01-05
**다음 리뷰**: 메타데이터 프로토콜 확정 후
