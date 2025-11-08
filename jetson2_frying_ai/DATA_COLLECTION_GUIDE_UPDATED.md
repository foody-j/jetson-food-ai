# 📊 Jetson #2 데이터 수집 가이드 (업데이트)

**날짜**: 2025-01-05
**상태**: ✅ **수동 데이터 수집 기능 구현 완료!**

---

## ✅ 구현 완료!

Jetson #2에 **수동 데이터 수집 기능**이 추가되었습니다!

### 🎉 추가된 기능

1. **GUI 버튼**: "📊 수집 시작" / "📊 수집 중지"
2. **4개 카메라 동시 저장**:
   - ✅ 카메라 0 (튀김 왼쪽) → `~/AI_Data/FryingData/`
   - ✅ 카메라 1 (튀김 오른쪽) → `~/AI_Data/FryingData/`
   - ✅ 카메라 2 (바켓 왼쪽) → `~/AI_Data/BucketData/`
   - ✅ 카메라 3 (바켓 오른쪽) → `~/AI_Data/BucketData/`
3. **세션별 관리**: 타임스탬프 기반 세션 ID
4. **자동 저장**: 5초마다 4개 카메라 동시 저장 (설정 가능)
5. **실시간 상태 표시**: 저장 개수 실시간 업데이트

---

## 🚀 사용 방법

### 방법 1: GUI로 수집 (권장) - JETSON2_INTEGRATED.py

#### 1단계: 프로그램 실행
```bash
cd ~/jetson-camera-monitor/jetson2_frying_ai
python3 JETSON2_INTEGRATED.py
```

### 2단계: 데이터 수집 시작
1. 화면 하단 제어 패널 확인
2. **"📊 수집 시작"** 버튼 클릭
3. 세션 ID 자동 생성 (예: `session_20251105_143025`)
4. 상태 표시: "수집 중: session_20251105_143025"

### 3단계: 데이터 수집 중
- **자동 저장**: 5초마다 **4개 카메라 프레임 동시** 자동 저장
  - 카메라 0 (튀김 왼쪽)
  - 카메라 1 (튀김 오른쪽)
  - 카메라 2 (바켓 왼쪽)
  - 카메라 3 (바켓 오른쪽)
- **실시간 표시**: 10장마다 저장 개수 업데이트
- **백그라운드 동작**: AI 분석과 독립적으로 동작

**중요**: 버튼 한 번으로 튀김 AI와 바켓 감지 데이터를 동시에 수집합니다!

### 4단계: 데이터 수집 종료
1. **"📊 수집 중지"** 버튼 클릭
2. 세션 정보 자동 저장 (`session_info.json`)
3. 요약 창 표시:
   - 총 저장 개수
   - 수집 시간
   - 저장 경로

---

## 📁 저장 구조

```
~/AI_Data/                                 # 홈 디렉토리
├── FryingData/                            # 튀김 AI 데이터
│   └── session_20251105_143025/          # 세션별 폴더
│       ├── camera_0/                     # 왼쪽 카메라
│       │   ├── cam0_143030_123.jpg
│       │   ├── cam0_143035_456.jpg
│       │   └── ...
│       ├── camera_1/                     # 오른쪽 카메라
│       │   ├── cam1_143030_123.jpg
│       │   └── ...
│       └── session_info.json             # 세션 정보
└── BucketData/                            # 바켓 감지 데이터
    └── session_20251105_143025/
        ├── camera_2/                     # 바켓 A
        │   ├── cam2_143030_123.jpg
        │   └── ...
        ├── camera_3/                     # 바켓 B
        │   ├── cam3_143030_123.jpg
        │   └── ...
        └── session_info.json
```

---

## 📄 세션 정보 (session_info.json)

```json
{
  "session_id": "session_20251105_143025",
  "start_time": "2025-01-05 14:30:25",
  "end_time": "2025-01-05 14:45:30",
  "duration_sec": 905.3,
  "collection_interval": 5,
  "cameras_used": [0, 1, 2, 3],
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

**설명**:
- `session_id`: 세션 식별자
- `start_time`: 수집 시작 시간
- `end_time`: 수집 종료 시간
- `duration_sec`: 총 수집 시간 (초)
- `collection_interval`: 저장 간격 (5초)
- `cameras_used`: 사용된 카메라 번호
- `total_saved`: 총 저장 장수 (카메라당 아님, 전체 저장 횟수)
- `camera_config`: 카메라 설정 (해상도, FPS)
- `mqtt_metadata`: **MQTT로 받은 조리 정보 (튀김유 온도, 조리 상태 등)**
- `metadata_count`: MQTT 메타데이터 개수

### 🎯 학습 시 활용
- **원본 이미지**: `camera_0/`, `camera_1/`, `camera_2/`, `camera_3/`
- **메타데이터**: `session_info.json`의 `mqtt_metadata`
  - 튀김유 온도와 이미지 매칭
  - 조리 타임라인 분석
  - 온도별 튀김 상태 라벨링 보조

---

## ⚙️ 설정

### config_jetson2.json

```json
{
  "data_collection_interval": 5    // 저장 간격 (초) - 기본값
}
```

**설정 변경**:
```bash
# 저장 간격을 3초로 변경
"data_collection_interval": 3

# 저장 간격을 10초로 변경 (저장량 감소)
"data_collection_interval": 10
```

---

## 💾 저장 용량 예상

### 설정
- **해상도**: 1280x720 (config에서 조정 가능)
- **JPEG 품질**: 85%
- **수집 간격**: 5초마다 1회
- **카메라**: 4대

### 용량 계산

**1회 수집 (5초마다)**:
- 카메라 4대 × 1장 = 4장
- 1장 약 100KB (1280x720, 85% JPEG)
- **4장 = 약 400KB**

**1시간 수집**:
- 720회 × 400KB = **약 288MB**

**8시간 (영업시간)**:
- 8시간 × 288MB = **약 2.3GB/일**

**500GB SSD 기준**:
- 500GB ÷ 2.3GB/일 = **약 217일 (7개월)**
- **5일간 수집**: 5일 × 2.3GB = **약 11.5GB** (500GB의 2.3%)

→ **500GB SSD면 충분히 여유롭습니다! 5일은 물론 7개월도 가능!** ✅

---

## 🎯 사용 시나리오

### 시나리오 1: 튀김 AI 파라미터 조정

**목적**: 실제 환경에서 HSV 범위 최적화

**절차**:
1. 튀김 조리 시작
2. **"📊 수집 시작"** 클릭
3. 조리 과정 모니터링 (5-10분)
4. 조리 완료 후 **"📊 수집 중지"** 클릭
5. `~/AI_Data/FryingData/` 확인
6. 이미지 분석 → HSV 범위 조정

**예상 데이터**: 5분 × 2회 = 약 10MB

---

### 시나리오 2: 바켓 감지 모델 학습 데이터

**목적**: 바켓 감지 YOLO 모델 학습용 데이터 200-300장

**절차**:
1. 바켓 상태 다양하게 준비:
   - 빈 바켓
   - 반만 찬 바켓
   - 가득 찬 바켓
   - 바켓 없음
2. 각 상태마다 **"📊 수집 시작"**
3. 2-3분 수집 (5초 간격 → 약 24-36장)
4. **"📊 수집 중지"**
5. 다음 상태로 변경 → 반복

**예상 데이터**: 10회 세션 × 5MB = **약 50MB**

---

### 시나리오 3: 장시간 모니터링

**목적**: 하루 종일 데이터 수집 (성능 평가용)

**절차**:
1. 아침 영업 시작 시 **"📊 수집 시작"**
2. 하루 종일 자동 수집
3. 저녁 영업 종료 시 **"📊 수집 중지"**

**예상 데이터**: 8시간 × 96MB/시간 = **약 768MB**

---

## 🔍 데이터 확인 방법

### 방법 1: 직접 확인
```bash
# 세션 목록 확인
ls -lh ~/AI_Data/FryingData/
ls -lh ~/AI_Data/BucketData/

# 특정 세션 확인
cd ~/AI_Data/FryingData/session_20251105_143025/
ls -lh camera_0/
ls -lh camera_1/

# 이미지 개수 확인
find ~/AI_Data/ -name "*.jpg" | wc -l

# 총 용량 확인
du -sh ~/AI_Data/
```

### 방법 2: 이미지 뷰어
```bash
# 특정 폴더 이미지 보기
cd ~/AI_Data/FryingData/session_20251105_143025/camera_0/
eog *.jpg  # 또는 다른 이미지 뷰어
```

---

## 🐛 문제 해결

### 문제 1: 버튼이 안 보임
**원인**: GUI 업데이트 필요

**해결**:
```bash
# 프로그램 재시작
# 화면 하단 제어 패널에 "📊 수집 시작" 버튼 확인
```

### 문제 2: 저장이 안 됨
**원인**: 권한 문제 또는 디스크 공간 부족

**확인**:
```bash
# 디스크 공간 확인
df -h ~

# 권한 확인
ls -ld ~/AI_Data/
```

**해결**:
```bash
# 디렉토리 재생성
rm -rf ~/AI_Data/
mkdir -p ~/AI_Data/FryingData
mkdir -p ~/AI_Data/BucketData
```

### 문제 3: 저장 개수가 0장
**원인**: 카메라 프레임이 없음

**확인**:
- AI 시작 버튼을 먼저 눌렀는지 확인
- 카메라 화면이 정상적으로 보이는지 확인

---

## 🚧 향후 추가 기능 (MQTT 자동 수집)

현재는 **수동 버튼**으로만 데이터 수집이 가능합니다.

### 향후 계획
1. MQTT 조리 시작 신호 구독
2. 조리 시작 시 자동 수집 시작
3. 조리 종료 시 자동 수집 종료
4. 수동 + 자동 하이브리드 모드

**구현 시기**: 로봇 Host PC와 MQTT 프로토콜 확정 후

---

## 📝 요약

### ✅ 현재 가능한 것
- ✅ 수동 버튼으로 데이터 수집 시작/중지
- ✅ 4개 카메라 동시 저장
- ✅ 5초 간격 자동 저장
- ✅ 세션별 폴더 관리
- ✅ 실시간 저장 개수 표시
- ✅ 세션 정보 JSON 저장

### 🚧 향후 추가 예정
- 🚧 MQTT 자동 수집 (조리 신호 기반)
- 🚧 AI 분석 결과 JSON 저장
- 🚧 데이터 자동 전송 (선택적)

---

## 💡 사용 팁

### Tip 1: 저장 간격 조정
```json
// 더 많은 데이터 수집 (3초 간격)
"data_collection_interval": 3

// 저장량 줄이기 (10초 간격)
"data_collection_interval": 10
```

### Tip 2: 세션 이름으로 상태 파악
세션 ID가 타임스탬프이므로 언제 수집했는지 바로 알 수 있습니다:
- `session_20251105_143025` → 2025년 1월 5일 14:30:25 수집

### Tip 3: 데이터 백업
```bash
# 특정 세션 백업
tar -czf session_20251105_143025.tar.gz ~/AI_Data/*/session_20251105_143025/

# 전체 백업
tar -czf ai_data_backup_$(date +%Y%m%d).tar.gz ~/AI_Data/
```

---

---

## 🛠️ 방법 2: 커맨드라인 도구 - data_collector.py

### 개요
`data_collector.py`는 **독립적인 데이터 수집 전용 도구**입니다.

### JETSON2_INTEGRATED.py vs data_collector.py

| 항목 | JETSON2_INTEGRATED.py | data_collector.py |
|------|----------------------|-------------------|
| **목적** | AI 모니터링 + 데이터 수집 | 데이터 수집 전용 |
| **GUI** | ✅ 있음 (전체 모니터링) | ❌ 없음 (미니멀) |
| **AI 분석** | ✅ 튀김 AI + 바켓 감지 | ❌ 없음 |
| **MQTT** | ✅ 메타데이터 수집 | ❌ 없음 |
| **카메라 선택** | ❌ 4개 고정 | ✅ 자유 선택 (0,1 또는 2,3) |
| **모드** | 버튼 수동 제어 | 수동/자동 선택 |
| **용도** | 실제 운영 환경 | 빠른 데이터 수집 테스트 |

### 언제 사용하나?

#### JETSON2_INTEGRATED.py (권장)
- ✅ 실제 운영 환경
- ✅ AI 모니터링 + 데이터 수집 동시
- ✅ MQTT 메타데이터 필요
- ✅ GUI 필요

#### data_collector.py
- ✅ 빠른 데이터 수집 테스트
- ✅ 특정 카메라만 수집 (튀김만 또는 바켓만)
- ✅ 헤드리스 환경 (GUI 없이)
- ✅ AI 분석 불필요

### 사용 예시

#### 예시 1: 튀김 카메라만 수집 (수동 모드)
```bash
cd ~/jetson-camera-monitor/jetson2_frying_ai
python3 data_collector.py --cameras 0,1 --output ~/Test_FryingData --mode manual
```

**화면 표시**:
```
📸 수동 캡처 모드
키 조작:
  스페이스바: 캡처
  'a': 자동 캡처 시작/중지
  'q': 종료
```

#### 예시 2: 바켓 카메라만 수집 (수동 모드)
```bash
python3 data_collector.py --cameras 2,3 --output ~/Test_BucketData --mode manual
```

#### 예시 3: 4개 카메라 자동 수집 (헤드리스)
```bash
python3 data_collector.py --cameras 0,1,2,3 --output ~/Test_AllData --mode auto --interval 5
```

**출력**:
```
📸 자동 캡처 모드 (헤드리스)
간격: 5초
종료: Ctrl+C

[캡처] 2025-01-05 15:30:00
  ✓ 저장: ~/Test_AllData/camera_0/cam0_20250105_153000.jpg
  ✓ 저장: ~/Test_AllData/camera_1/cam1_20250105_153000.jpg
  ✓ 저장: ~/Test_AllData/camera_2/cam2_20250105_153000.jpg
  ✓ 저장: ~/Test_AllData/camera_3/cam3_20250105_153000.jpg
  → 4개 파일 저장 완료 (총 4개)
```

### 옵션 설명

| 옵션 | 설명 | 기본값 | 예시 |
|------|------|--------|------|
| `--cameras` | 카메라 인덱스 | `0,1,2,3` | `0,1` (튀김만) |
| `--output` | 저장 디렉토리 | `./data` | `~/MyData` |
| `--mode` | 모드 | `manual` | `auto` |
| `--interval` | 자동 캡처 간격 (초) | `5` | `10` |

### 저장 구조

```
output_dir/
├── camera_0/
│   ├── cam0_20250105_153000.jpg
│   ├── cam0_20250105_153005.jpg
│   └── ...
├── camera_1/
│   └── ...
├── camera_2/
│   └── ...
└── camera_3/
    └── ...
```

**주의**: `session_info.json`은 생성되지 않습니다! (메타데이터 없음)

### 장단점

#### 장점
- ✅ 빠른 시작 (AI 모델 로딩 불필요)
- ✅ 특정 카메라만 선택 가능
- ✅ 간단한 커맨드라인 인터페이스
- ✅ 헤드리스 환경 지원

#### 단점
- ❌ MQTT 메타데이터 수집 안 됨
- ❌ AI 분석 없음 (미리보기 없음)
- ❌ `session_info.json` 없음
- ❌ 세션 관리 없음

---

## 📊 비교 요약

### 실제 운영: JETSON2_INTEGRATED.py ✅
```bash
python3 JETSON2_INTEGRATED.py
# GUI에서 "📊 수집 시작" 버튼 클릭
# → 4개 카메라 + MQTT 메타데이터 + session_info.json
```

### 빠른 테스트: data_collector.py 🔧
```bash
python3 data_collector.py --cameras 0,1 --mode manual
# 스페이스바로 수동 캡처
# → 선택한 카메라만, 메타데이터 없음
```

---

**데이터 수집 준비 완료! 이제 실제 환경에서 테스트할 수 있습니다!** 🎉
