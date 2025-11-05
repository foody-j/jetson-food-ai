# 📊 Jetson #2 데이터 수집 모니터링 모드 제안

**날짜**: 2025-01-05

---

## 🎯 문제점

현재 Jetson #2는 AI 모델 개발을 위한 **데이터 수집 기능이 부족**합니다:

### 현재 상태
- ✅ 튀김 AI 실시간 분석 가능
- ✅ 바켓 감지 AI 실시간 분석 가능
- ❌ **데이터 저장 기능 없음** → AI 개선 불가능
- ❌ 실제 환경 데이터 확인 불가능
- ❌ 모델 성능 평가 불가능

### 필요성
1. **튀김 AI 파라미터 조정**: 실제 이미지로 HSV 범위 최적화
2. **바켓 감지 모델 개발**: 학습 데이터 200-300장 필요
3. **성능 평가**: 저장된 이미지로 정확도 분석
4. **문제 디버깅**: 오류 발생 시 원본 이미지 확인

---

## 💡 제안: 모니터링 모드 추가

Jetson #1의 **볶음 모니터링**과 유사하게, Jetson #2에도 **데이터 수집 모니터링** 기능을 추가합니다.

---

## 🔧 제안 방식 A: MQTT 기반 자동 수집 (추천!) ⭐

### 개념
조리 시작/종료 신호를 MQTT로 받아서 **자동으로 데이터 수집**

### 장점
- ✅ **완전 자동**: 사용자 조작 불필요
- ✅ **정확한 타이밍**: 실제 조리 중 데이터만 수집
- ✅ **세션별 저장**: 각 조리 세션마다 폴더 분리
- ✅ **효율적**: 필요한 데이터만 저장 (저장 공간 절약)

### 구현 방법

#### 1. MQTT 토픽 구독
```python
# 구독할 토픽
stirfry/cooking/start    # 조리 시작 신호
stirfry/cooking/end      # 조리 종료 신호
```

#### 2. 자동 수집 플로우
```
[조리 시작 MQTT 수신]
    ↓
[데이터 수집 시작]
    - 튀김 카메라 (0, 1): 5초마다 1장
    - 바켓 카메라 (2, 3): 5초마다 1장
    - AI 분석 결과도 함께 저장 (JSON)
    ↓
[조리 중...]
    - 백그라운드로 계속 저장
    - GUI에 저장 개수 실시간 표시
    ↓
[조리 종료 MQTT 수신]
    ↓
[데이터 수집 종료]
    - 총 저장 개수 표시
    - 세션 폴더 자동 생성
```

#### 3. 저장 구조
```
~/FryingData/                          # 튀김 AI 데이터
├── session_20251105_140230/           # 세션별 폴더
│   ├── camera_0/
│   │   ├── cam0_140230.jpg
│   │   ├── cam0_140235.jpg
│   │   └── ...
│   ├── camera_1/
│   │   └── ...
│   └── session_info.json              # AI 분석 결과
└── session_20251105_153045/
    └── ...

~/BucketData/                          # 바켓 감지 데이터
├── session_20251105_140230/
│   ├── camera_2/
│   ├── camera_3/
│   └── detections.json                # 바켓 감지 결과
└── ...
```

#### 4. GUI 변경사항

**기존:**
```
┌─────────────────────────────────┐
│ 튀김 AI                         │
│ [시작] [중지]                   │
└─────────────────────────────────┘
```

**제안:**
```
┌─────────────────────────────────┐
│ 튀김 AI                         │
│ [시작] [중지]                   │
│                                 │
│ 📊 데이터 수집: 대기 중          │  ← 추가
│ 저장: 0장 (세션: -)             │  ← 추가
│ [수동 수집 시작] (개발자용)      │  ← 추가 (옵션)
└─────────────────────────────────┘
```

#### 5. 코드 수정 포인트

**파일**: `jetson2_ai/JETSON2_INTEGRATED.py`

**추가할 변수**:
```python
self.data_collection_active = False
self.current_session_id = None
self.session_save_count = 0
self.collection_interval = 5  # 5초마다
```

**MQTT 핸들러 추가**:
```python
def on_mqtt_message(self, topic, payload):
    if topic == "stirfry/cooking/start":
        self.start_data_collection()
    elif topic == "stirfry/cooking/end":
        self.stop_data_collection()

def start_data_collection(self):
    """MQTT 신호로 데이터 수집 시작"""
    self.data_collection_active = True
    self.current_session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
    self.session_save_count = 0
    print(f"[데이터수집] 시작: {self.current_session_id}")

def stop_data_collection(self):
    """MQTT 신호로 데이터 수집 종료"""
    self.data_collection_active = False
    print(f"[데이터수집] 종료: {self.session_save_count}장 저장")
    self.current_session_id = None
```

**카메라 업데이트 루프에 추가**:
```python
def update_frying_cameras(self):
    # 기존 AI 분석 코드...

    # 데이터 수집 추가
    if self.data_collection_active:
        if self.frying_frame_counter % (self.collection_interval * FPS) == 0:
            self.save_frying_data(frame0, frame1, analysis_result)
```

---

## 🔧 제안 방식 B: 수동 모니터링 모드

### 개념
Jetson #1처럼 **수동으로 녹화 시작/중지** 버튼

### 장점
- ✅ **간단 구현**: Jetson #1 코드 재사용
- ✅ **직관적**: 버튼만 누르면 됨
- ✅ **즉시 사용 가능**: MQTT 설정 불필요

### 단점
- ❌ **수동 조작 필요**: 사용자가 매번 버튼 눌러야 함
- ❌ **타이밍 부정확**: 조리 시작/종료와 정확히 일치 안 할 수 있음
- ❌ **불필요한 데이터**: 조리 전후 데이터도 저장될 수 있음

### 구현 방법

**GUI에 버튼 추가**:
```
┌─────────────────────────────────┐
│ 튀김 AI                         │
│ [AI 시작] [AI 중지]             │
│                                 │
│ 📊 데이터 수집                  │
│ [수집 시작] [수집 중지]          │
│ 저장: 0장                       │
└─────────────────────────────────┘
```

**코드**: Jetson #1의 `start_stirfry_recording()` / `stop_stirfry_recording()` 복사

---

## 🔧 제안 방식 C: 하이브리드 (MQTT + 수동)

### 개념
**평소에는 MQTT 자동 수집**, 테스트 시에는 **수동 버튼**

### 장점
- ✅ **자동 + 수동 모두 지원**
- ✅ **유연성 최고**
- ✅ **개발/운영 모두 편리**

### 구현
```
┌─────────────────────────────────┐
│ 튀김 AI                         │
│ [AI 시작] [AI 중지]             │
│                                 │
│ 📊 데이터 수집                  │
│ 모드: 자동 (MQTT)  ✓            │  ← MQTT 수신 중
│ 저장: 0장 (대기 중)             │
│ [수동 수집] (개발자 테스트)      │  ← 수동 버튼 (옵션)
└─────────────────────────────────┘
```

---

## 📊 저장할 데이터 항목

### 1. 이미지 데이터
```
camera_0/      # 튀김 왼쪽
camera_1/      # 튀김 오른쪽
camera_2/      # 바켓 A
camera_3/      # 바켓 B
```

### 2. AI 분석 결과 (JSON)
```json
{
  "session_id": "session_20251105_140230",
  "start_time": "2025-01-05 14:02:30",
  "end_time": "2025-01-05 14:15:45",
  "frying_analysis": [
    {
      "timestamp": "14:02:35",
      "camera_0": {
        "brown_ratio": 0.35,
        "golden_ratio": 0.12,
        "status": "cooking"
      },
      "camera_1": { ... }
    }
  ],
  "bucket_detections": [
    {
      "timestamp": "14:02:35",
      "camera_2": {
        "basket_detected": true,
        "basket_status": "empty",
        "confidence": 0.87
      },
      "camera_3": { ... }
    }
  ],
  "total_images": 142,
  "duration_sec": 795
}
```

### 3. 세션 정보
```json
{
  "session_id": "session_20251105_140230",
  "mqtt_start": "2025-01-05 14:02:30",
  "mqtt_end": "2025-01-05 14:15:45",
  "collection_interval": 5,
  "cameras_used": [0, 1, 2, 3],
  "total_saved": 142
}
```

---

## 📁 저장 공간 예상

### 저장 설정
- **해상도**: 640x480 (config에서 조정 가능)
- **JPEG 품질**: 70%
- **수집 간격**: 5초마다 1장

### 용량 계산
**1회 조리 세션 (15분)**:
- 카메라 4대
- 15분 ÷ 5초 = 180장/카메라
- 180장 × 4대 = 720장
- 1장 약 50KB (640x480, 70% JPEG)
- **총 용량: 약 36MB/세션**

**1일 (10회 조리)**:
- 36MB × 10회 = **약 360MB/일**

**1주일**:
- 360MB × 7일 = **약 2.5GB/주**

→ **충분히 감당 가능한 용량!**

---

## 🚀 권장 구현 순서

### Phase 1: 최소 기능 (1-2시간)
1. **수동 버튼 추가** (방식 B)
   - "수집 시작/중지" 버튼만 추가
   - Jetson #1 코드 재사용
   - **즉시 테스트 가능!**

### Phase 2: MQTT 자동 수집 (2-3시간)
2. **MQTT 구독 추가** (방식 A)
   - `stirfry/cooking/start` 구독
   - `stirfry/cooking/end` 구독
   - 자동 수집 시작/종료

### Phase 3: 분석 결과 저장 (1-2시간)
3. **JSON 메타데이터**
   - AI 분석 결과 저장
   - 세션 정보 기록
   - 성능 평가에 활용

### Phase 4: 하이브리드 모드 (30분)
4. **수동 + 자동 통합** (방식 C)
   - 평소 자동, 테스트 시 수동
   - 최고의 유연성

---

## 💡 추천 방안

### 🥇 1순위: **방식 C (하이브리드)**

**이유**:
- 평소 운영: MQTT 자동 수집 → 편리함
- 개발/테스트: 수동 버튼 → 유연함
- 구현도 간단 (Phase 1-4 순차 진행)

**타임라인**:
- Day 1: Phase 1 (수동 버튼) → 즉시 사용 가능
- Day 2: Phase 2 (MQTT 자동) → 자동화 완성
- Day 3: Phase 3-4 (메타데이터, 통합) → 완벽한 시스템

---

## 📝 다음 단계

### 즉시 시작 가능
1. ✅ Phase 1 구현: 수동 버튼 추가 (오늘 바로 시작 가능)
2. ✅ 실제 환경 테스트: 데이터 수집 시작
3. ✅ Phase 2-4 순차 진행

### 필요 시 지원
- [ ] Phase 1 코드 작성 (수동 버튼)
- [ ] Phase 2 코드 작성 (MQTT 자동)
- [ ] Phase 3 코드 작성 (JSON 메타데이터)
- [ ] GUI 디자인 개선

---

## 🤔 의견 주세요!

**선택해주세요**:
- A. **방식 A (MQTT 자동만)** - 완전 자동, 수동 버튼 없음
- B. **방식 B (수동만)** - 버튼으로만 제어, MQTT 없음
- C. **방식 C (하이브리드)** ⭐ - 자동 + 수동 모두 (추천!)

**또는 다른 아이디어 있으시면 말씀해주세요!**

---

**결론**: Jetson #2에 데이터 수집 모니터링 모드를 추가하면 AI 모델 개발과 개선이 가능해집니다!
