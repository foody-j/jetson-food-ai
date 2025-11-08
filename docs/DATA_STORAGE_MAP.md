# 📁 데이터 저장 위치 맵

**작성일**: 2025-01-05
**목적**: Jetson #1, #2의 모든 데이터 저장 위치 정리

---

## 📋 목차

1. [Jetson #1 - 사람 감지 및 볶음 모니터링](#jetson-1---사람-감지-및-볶음-모니터링)
2. [Jetson #2 - 튀김 AI 및 바켓 감지](#jetson-2---튀김-ai-및-바켓-감지)
3. [진동 센서 데이터](#진동-센서-데이터)
4. [용량 및 관리](#용량-및-관리)

---

## Jetson #1 - 사람 감지 및 볶음 모니터링

### 📷 카메라 구성
- **카메라 0** (GMSL #2): 사람 감지
- **카메라 1** (GMSL #0): 볶음 왼쪽
- **카메라 2** (GMSL #1): 볶음 오른쪽

### 📂 데이터 저장 위치

#### 1. 사람 감지 스냅샷
**경로**: `~/Detection/`

**구조**:
```
/home/dkuyj/Detection/
└── YYYYMMDD/                    # 날짜별 폴더
    ├── HHMMSS.jpg               # 타임스탬프 파일명
    ├── HHMMSS.jpg
    └── ...
```

**예시**:
```
/home/dkuyj/Detection/
└── 20250105/
    ├── 143025.jpg               # 14:30:25 사람 감지
    ├── 143127.jpg               # 14:31:27 사람 감지
    └── 150322.jpg
```

**설정 파일**: `jetson1_monitoring/config.json`
```json
{
  "snapshot_dir": "~/Detection"
}
```

**용도**:
- 사람 감지 시 자동 스냅샷
- YOLO 학습 데이터 수집 (사람 감지)
- 출입 기록 확인

---

#### 2. 볶음 모니터링 데이터
**경로**: `~/StirFry_Data/`

**구조**:
```
/home/dkuyj/StirFry_Data/
├── left/                        # 왼쪽 카메라 (카메라 1)
│   └── YYYYMMDD_HHMMSS/        # 녹화 세션별
│       ├── 001.jpg
│       ├── 002.jpg
│       ├── 003.jpg
│       └── ...
└── right/                       # 오른쪽 카메라 (카메라 2)
    └── YYYYMMDD_HHMMSS/
        ├── 001.jpg
        ├── 002.jpg
        └── ...
```

**예시**:
```
/home/dkuyj/StirFry_Data/
├── left/
│   ├── 20250105_143025/
│   │   ├── 001.jpg
│   │   ├── 002.jpg
│   │   └── ...
│   └── 20250105_150532/
│       └── ...
└── right/
    ├── 20250105_143025/
    │   ├── 001.jpg
    │   └── ...
    └── 20250105_150532/
        └── ...
```

**설정 파일**: `jetson1_monitoring/config.json`
```json
{
  "stirfry_save_dir": "~/StirFry_Data"
}
```

**메타데이터**: 없음 (수동 녹화)
- 녹화 시작/종료 시간은 폴더명으로 기록
- 프레임 번호는 파일명으로 기록

**용도**:
- 볶음 과정 모니터링
- 품질 관리
- 조리 타임라인 분석

---

### 📊 Jetson #1 용량 예상

| 항목 | 용량 | 비고 |
|------|------|------|
| **사람 감지 스냅샷** | ~10MB/일 | 하루 50-100장 가정 |
| **볶음 녹화 (1회)** | ~200MB | 5분 녹화 기준 |
| **볶음 녹화 (10회/일)** | ~2GB/일 | - |
| **합계** | **~2GB/일** | - |

**500GB SSD 기준**: 약 250일 (8개월)

---

## Jetson #2 - 튀김 AI 및 바켓 감지

### 📷 카메라 구성
- **카메라 0** (GMSL #0): 튀김 왼쪽
- **카메라 1** (GMSL #1): 튀김 오른쪽
- **카메라 2** (GMSL #2): 바켓 왼쪽
- **카메라 3** (GMSL #3): 바켓 오른쪽

### 📂 데이터 저장 위치

#### 1. 튀김 AI 데이터
**경로**: `~/AI_Data/FryingData/`

**구조**:
```
/home/dkuyj/AI_Data/FryingData/
└── session_YYYYMMDD_HHMMSS/    # 세션별 폴더
    ├── camera_0/               # 카메라 0 (왼쪽)
    │   ├── cam0_HHMMSS_mmm.jpg
    │   ├── cam0_HHMMSS_mmm.jpg
    │   └── ...
    ├── camera_1/               # 카메라 1 (오른쪽)
    │   ├── cam1_HHMMSS_mmm.jpg
    │   └── ...
    └── session_info.json       # 세션 정보 + MQTT 메타데이터
```

**예시**:
```
/home/dkuyj/AI_Data/FryingData/
├── session_20250105_143025/
│   ├── camera_0/
│   │   ├── cam0_143030_123.jpg
│   │   ├── cam0_143035_456.jpg
│   │   └── cam0_143040_789.jpg
│   ├── camera_1/
│   │   ├── cam1_143030_123.jpg
│   │   └── ...
│   └── session_info.json
└── session_20250105_150530/
    └── ...
```

**session_info.json 구조**:
```json
{
  "session_id": "session_20250105_143025",
  "start_time": "2025-01-05 14:30:25",
  "end_time": "2025-01-05 14:45:30",
  "duration_sec": 905.3,
  "collection_interval": 5,
  "cameras_used": [0, 1],
  "total_saved": 181,
  "camera_config": {
    "resolution": {
      "width": 1280,
      "height": 720
    },
    "fps": 30
  },
  "mqtt_metadata": [
    {
      "timestamp": "2025-01-05 14:30:30.123",
      "type": "oil_temperature",
      "position": "left",
      "value": 175.5,
      "unit": "celsius"
    },
    {
      "timestamp": "2025-01-05 14:30:35.456",
      "type": "oil_temperature",
      "position": "right",
      "value": 178.2,
      "unit": "celsius"
    }
  ],
  "metadata_count": 243
}
```

**설정 파일**: `jetson2_frying_ai/config_jetson2.json`
```json
{
  "data_collection_interval": 5
}
```

**용도**:
- 튀김 상태 AI 학습 데이터
- 온도와 색상 관계 분석
- 조리 품질 관리

---

#### 2. 바켓 감지 데이터
**경로**: `~/AI_Data/BucketData/`

**구조**:
```
/home/dkuyj/AI_Data/BucketData/
└── session_YYYYMMDD_HHMMSS/    # 세션별 폴더
    ├── camera_2/               # 카메라 2 (왼쪽)
    │   ├── cam2_HHMMSS_mmm.jpg
    │   └── ...
    ├── camera_3/               # 카메라 3 (오른쪽)
    │   ├── cam3_HHMMSS_mmm.jpg
    │   └── ...
    └── session_info.json       # 세션 정보
```

**예시**:
```
/home/dkuyj/AI_Data/BucketData/
├── session_20250105_143025/
│   ├── camera_2/
│   │   ├── cam2_143030_123.jpg    # EMPTY
│   │   ├── cam2_143035_456.jpg    # EMPTY
│   │   ├── cam2_143040_789.jpg    # FILLED
│   │   └── ...
│   ├── camera_3/
│   │   ├── cam3_143030_123.jpg
│   │   └── ...
│   └── session_info.json
└── session_20250105_150530/
    └── ...
```

**session_info.json**: FryingData와 동일 구조

**용도**:
- 바켓 상태 감지 YOLO 학습 데이터
- EMPTY / FILLED / NO_BASKET 분류

---

### 📊 Jetson #2 용량 예상

| 항목 | 용량 | 비고 |
|------|------|------|
| **1회 수집 (5초)** | 400KB | 4장 × 100KB |
| **1시간** | 288MB | 720회 |
| **8시간 (영업시간)** | 2.3GB | - |
| **5일** | 11.5GB | 500GB의 2.3% |
| **500GB 풀 사용** | **217일 (7개월)** | - |

---

## 진동 센서 데이터

### 📂 데이터 저장 위치
**경로**: 프로젝트 루트 (현재 위치)

**파일명 형식**:
```
YYYYMMDD_HHMMSS_UIDxx_vibration.csv
```

**예시**:
```
/home/dkuyj/jetson-camera-monitor/
├── 20251105_144526_UID50_vibration.csv
├── 20251105_144526_UID51_vibration.csv
└── 20251105_144526_UID52_vibration.csv
```

**데이터 구조** (CSV):
```csv
timestamp,sensor_id,x,y,z,rms,frequency
2025-01-05 14:45:26.123,UID50,0.5,0.4,0.3,0.52,60
2025-01-05 14:45:26.133,UID50,0.51,0.41,0.31,0.53,60
...
```

**설정 파일**: `vibration_config.json`
```json
{
  "sensors": [
    {"uid": 50, "machine_id": "fryer_01"},
    {"uid": 51, "machine_id": "fryer_02"},
    {"uid": 52, "machine_id": "stirfry_01"}
  ],
  "sampling_rate": 100,
  "save_interval": 60
}
```

**용도**:
- 기계 상태 모니터링
- 이상 진동 감지
- 예지 보전 (Predictive Maintenance)

**권장 저장 위치**: `~/VibrationData/`로 이동 필요
```bash
mkdir -p ~/VibrationData
mv *.csv ~/VibrationData/
```

---

## 📊 전체 용량 요약

### 500GB SSD 기준

| Jetson | 항목 | 용량/일 | 예상 보관 기간 |
|--------|------|---------|---------------|
| **#1** | 사람 감지 | 10MB | - |
| **#1** | 볶음 녹화 | 2GB | 250일 (8개월) |
| **#2** | 튀김 AI | 2.3GB | 217일 (7개월) |
| **#2** | 바켓 감지 | (포함) | - |
| **진동** | CSV | 50MB | - |
| **합계** | - | **~4.3GB/일** | **116일 (약 4개월)** |

**5일간 수집**:
- Jetson #1: 10GB
- Jetson #2: 11.5GB
- 진동: 250MB
- **합계: 약 21.75GB** (500GB의 4.3%)

### ✅ 결론: 5일은 여유롭게 버팁니다!

---

## 🗂️ 데이터 관리 가이드

### 1. 정기 백업
```bash
# Jetson #1
tar -czf jetson1_backup_$(date +%Y%m%d).tar.gz ~/Detection ~/StirFry_Data

# Jetson #2
tar -czf jetson2_backup_$(date +%Y%m%d).tar.gz ~/AI_Data

# 진동 센서
tar -czf vibration_backup_$(date +%Y%m%d).tar.gz ~/VibrationData
```

### 2. 데이터 정리 (보관 기간 초과 시)
```bash
# 30일 이전 데이터 삭제
find ~/Detection -type f -mtime +30 -delete
find ~/StirFry_Data -type d -mtime +30 -exec rm -rf {} +
find ~/AI_Data -type d -mtime +30 -exec rm -rf {} +
```

### 3. 용량 확인
```bash
# 전체 용량
du -sh ~/Detection ~/StirFry_Data ~/AI_Data ~/VibrationData

# 디스크 여유 공간
df -h ~
```

### 4. 학습용 데이터 복사 (PC/서버로)
```bash
# Jetson → PC
rsync -avz ~/AI_Data/ user@pc:/path/to/training_data/

# 특정 세션만
rsync -avz ~/AI_Data/FryingData/session_20250105_143025/ user@pc:/path/
```

---

## 📝 파일명 규칙

### Jetson #1
- **사람 감지**: `HHMMSS.jpg` (타임스탬프)
- **볶음 녹화**: `001.jpg`, `002.jpg`, ... (순번)

### Jetson #2
- **튀김 AI**: `cam0_HHMMSS_mmm.jpg` (카메라번호_시분초_밀리초)
- **바켓 감지**: `cam2_HHMMSS_mmm.jpg`

### 진동 센서
- **CSV**: `YYYYMMDD_HHMMSS_UIDxx_vibration.csv`

---

## 🎯 데이터 수집 체크리스트

### 데이터 수집 전
- [ ] 디스크 여유 공간 확인 (`df -h`)
- [ ] 이전 데이터 백업 완료
- [ ] 날짜/시간 동기화 확인

### 데이터 수집 중
- [ ] 실시간 용량 모니터링
- [ ] MQTT 연결 상태 확인
- [ ] 카메라 동작 확인

### 데이터 수집 후
- [ ] session_info.json 생성 확인
- [ ] 이미지 파일 개수 확인
- [ ] 메타데이터 누락 여부 확인
- [ ] 백업 실행

---

## 📞 문의

데이터 저장 관련 문의: GitHub Issues

---

**문서 업데이트**: 2025-01-05
**다음 리뷰**: 데이터 수집 시작 후
