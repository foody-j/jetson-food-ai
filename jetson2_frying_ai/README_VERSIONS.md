# Jetson #2 - 버전 관리 가이드

## 📋 파일 구조

```
jetson2_frying_ai/
├── JETSON2_INTEGRATED.py         # 🏭 현장 배포용 (Production)
├── JETSON2_INTEGRATED_LAB.py     # 🔬 실험실 테스트용 (Laboratory)
├── config_jetson2.json            # 배포용 설정
├── config_jetson2_lab.json        # 실험실용 설정
└── README_VERSIONS.md             # 이 파일
```

---

## 🏭 **배포 버전 (JETSON2_INTEGRATED.py)**

### **용도**
- 현장 실제 운영 (24시간 무인 운영)
- 로봇 PC와 MQTT 연동 필수

### **주요 특징**
- ✅ 메모리 최적화 (불필요한 UI 제거)
- ✅ MQTT로만 음식 종류 수신 (`frying/food_type`)
- ✅ 자동 완료 마킹 (탐침온도 >= 75°C)
- ❌ 수동 음식 선택 다이얼로그 없음
- ❌ 수동 완료 마킹 버튼 없음

### **실행 방법**
```bash
python3 JETSON2_INTEGRATED.py
```

### **MQTT 요구사항**
```python
# 로봇 PC에서 반드시 전송해야 함:
- frying/food_type        # 조리 시작 시: "chicken", "shrimp" 등
- frying/probe_temp/left  # 실시간 탐침 온도 (°C)
- frying/oil_temp/left    # 실시간 기름 온도 (°C)
```

### **데이터 수집 시작 조건**
1. MQTT로 `food_type` 수신 완료
2. "📊 수집 시작" 버튼 클릭
3. 탐침 온도 75°C 도달 시 자동 완료 마킹
4. "📊 수집 중지" 버튼으로 종료

---

## 🔬 **실험실 버전 (JETSON2_INTEGRATED_LAB.py)**

### **용도**
- 파일럿 테스트
- MQTT 없이 독립 테스트
- 다양한 조건 실험

### **주요 특징**
- ✅ 음식 종류 수동 선택 다이얼로그
- ✅ "✅ 완료 마킹" 버튼 (수동 마킹 가능)
- ✅ MQTT 선택적 (없어도 동작)
- ✅ 자동 완료 마킹도 지원 (MQTT 있으면)

### **실행 방법**
```bash
python3 JETSON2_INTEGRATED_LAB.py
```

### **데이터 수집 절차**
1. "📊 수집 시작" 클릭
2. 음식 종류 선택 다이얼로그 (치킨🍗, 새우🍤 등)
3. 조리 진행
4. 완료 시점에 "✅ 완료 마킹" 버튼 클릭
5. "📊 수집 중지" 버튼으로 종료

---

## 📊 **저장되는 데이터**

### **공통 폴더 구조**
```
~/AI_Data/
├── FryingData/
│   └── session_20251107_143022/
│       ├── camera_0/
│       │   ├── cam0_143025_123.jpg
│       │   └── ...
│       ├── camera_1/
│       │   └── ...
│       └── session_info.json  ⭐ 메타데이터
└── BucketData/
    └── ...
```

### **session_info.json 예시**
```json
{
  "session_id": "session_20251107_143022",
  "food_type": "chicken",
  "start_time": "2025-11-07 14:30:22",
  "end_time": "2025-11-07 14:34:10",
  "duration_sec": 228,

  "completion_marked": true,
  "completion_info": {
    "method": "auto",  // 배포: "auto", 실험실: "manual" or "auto"
    "elapsed_time_sec": 203.5,
    "frame_index": 67,
    "probe_temp_left": 75.3,
    "oil_temp_left": 172.5
  },

  "temperature_timeline": [
    {"timestamp": "14:30:25", "oil_temp_left": 175.2},
    {"timestamp": "14:30:30", "probe_temp_left": 45.3},
    ...
  ]
}
```

---

## 🔄 **버전별 사용 시나리오**

### **시나리오 1: 실험실에서 치킨 테스트**
```bash
1. JETSON2_INTEGRATED_LAB.py 실행
2. "📊 수집 시작" → "치킨🍗" 선택
3. 치킨 튀김 시작
4. 적절한 시점에 "✅ 완료 마킹" 클릭
5. 조금 더 조리 후 "📊 수집 중지"
6. ~/AI_Data/FryingData/ 확인
```

### **시나리오 2: 현장 배포 (로봇 연동)**
```bash
# 로봇 PC에서:
mosquitto_pub -t "frying/food_type" -m "chicken"

# Jetson #2에서:
1. JETSON2_INTEGRATED.py 실행 (자동 시작)
2. 로봇이 조리 시작 → 자동 데이터 수집
3. 탐침온도 75°C 도달 → 자동 완료 마킹
4. 조리 종료 → 자동 수집 중지
```

---

## ⚙️ **Config 파일 차이**

### **config_jetson2.json (배포용)**
- `mqtt_enabled`: true (필수)
- 최적화된 프레임 스킵
- 메모리 효율 우선

### **config_jetson2_lab.json (실험실용)**
- `mqtt_enabled`: false (선택)
- 더 빠른 프레임 캡처
- 실험 편의성 우선

---

## 🚨 **주의사항**

### **배포 버전**
- ⚠️ MQTT 없이 실행 시 음식 종류를 받을 수 없음
- ⚠️ 24시간 운영 고려한 메모리 관리
- ⚠️ 수동 조작 최소화

### **실험실 버전**
- ⚠️ 현장 배포 금지 (메모리 비효율적)
- ⚠️ 파일럿 테스트 전용
- ⚠️ 수동 조작이 많아 실수 가능성 높음

---

## 📞 **문제 해결**

### **배포 버전: "음식 종류가 설정되지 않았습니다"**
```bash
# 해결: 로봇 PC에서 MQTT 전송 확인
mosquitto_pub -t "frying/food_type" -m "chicken"
```

### **실험실 버전: 완료 마킹 버튼이 안 보임**
```bash
# 해결: LAB 버전 실행 확인
ps aux | grep JETSON2_INTEGRATED
# JETSON2_INTEGRATED_LAB.py 인지 확인
```

---

**작성일**: 2025-11-08
**작성자**: Claude Code
**버전**: v1.0
