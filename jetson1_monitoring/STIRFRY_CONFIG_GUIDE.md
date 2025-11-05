# 📸 볶음 모니터링 캡처 설정 가이드

**config.json 파일에서 이미지 저장 설정을 동적으로 조절할 수 있습니다**

---

## ⚙️ 설정 옵션

### config.json 파일 위치
```
~/jetson-camera-monitor/autostart_autodown/config.json
```

### 볶음 모니터링 관련 설정

```json
{
  "stirfry_save_dir": "StirFry_Data",
  "stirfry_save_resolution": {
    "width": 960,
    "height": 768
  },
  "stirfry_jpeg_quality": 70,
  "stirfry_frame_skip": 6
}
```

---

## 📋 설정 상세 설명

### 1. `stirfry_save_resolution`
**이미지 저장 해상도**

원본: 1920x1536 (GMSL 카메라)

**옵션:**

| 해상도 | width | height | 파일 크기 (예상) | 용도 |
|--------|-------|--------|------------------|------|
| **원본** | 1920 | 1536 | ~493 KB | 최고 화질 |
| **1/2 크기** | 960 | 768 | ~19 KB | **기본값 (권장)** |
| **1/4 크기** | 480 | 384 | ~5 KB | 초저용량 |
| **HD** | 1280 | 1024 | ~80 KB | 중간 화질 |

**설정 예시:**
```json
// 원본 해상도로 저장 (고화질)
"stirfry_save_resolution": {
  "width": 1920,
  "height": 1536
}

// 기본값 (권장)
"stirfry_save_resolution": {
  "width": 960,
  "height": 768
}

// 초저용량
"stirfry_save_resolution": {
  "width": 480,
  "height": 384
}
```

---

### 2. `stirfry_jpeg_quality`
**JPEG 압축 품질 (0-100)**

| 값 | 화질 | 파일 크기 | 용도 |
|----|------|-----------|------|
| **100** | 최고 | 최대 | 원본 품질 유지 |
| **85-95** | 매우 좋음 | 큼 | 고품질 필요 시 |
| **70** | 좋음 | 중간 | **기본값 (권장)** |
| **50-60** | 보통 | 작음 | 저용량 필요 시 |
| **30-40** | 낮음 | 매우 작음 | 극저용량 |

**설정 예시:**
```json
// 최고 화질
"stirfry_jpeg_quality": 100

// 기본값 (권장)
"stirfry_jpeg_quality": 70

// 저용량
"stirfry_jpeg_quality": 50
```

---

### 3. `stirfry_frame_skip`
**캡처 주기 (N프레임마다 1장 저장)**

GUI 업데이트: 20 FPS (50ms 간격)

| 값 | 캡처 주기 | 실제 FPS | 용도 |
|----|-----------|----------|------|
| **1** | 매 프레임 | ~20 FPS | 최대 해상도 |
| **3** | 3프레임마다 | ~6.7 FPS | 부드러운 동영상 |
| **6** | 6프레임마다 | ~3.3 FPS | **기본값 (권장)** |
| **10** | 10프레임마다 | ~2 FPS | 저용량 |
| **20** | 20프레임마다 | ~1 FPS | 극저용량 |

**설정 예시:**
```json
// 매 프레임 저장 (최고 해상도)
"stirfry_frame_skip": 1

// 기본값 (권장)
"stirfry_frame_skip": 6

// 저장 빈도 낮춤 (저용량)
"stirfry_frame_skip": 10
```

---

## 💾 저장 용량 계산

### 1분당 저장되는 이미지 수

```
이미지 수/분 = (20 FPS × 60초) ÷ stirfry_frame_skip
```

**예시:**
- `frame_skip = 6`: 200장/분
- `frame_skip = 10`: 120장/분
- `frame_skip = 20`: 60장/분

### 1시간당 예상 용량

| 해상도 | 품질 | frame_skip | 파일 크기 | 1시간 용량 |
|--------|------|------------|-----------|------------|
| 960×768 | 70 | 6 | 19 KB | **228 MB** |
| 960×768 | 70 | 10 | 19 KB | **137 MB** |
| 1920×1536 | 70 | 6 | 80 KB | **960 MB** |
| 1920×1536 | 100 | 6 | 493 KB | **5.9 GB** |
| 480×384 | 50 | 10 | 3 KB | **22 MB** |

**기본 설정 (권장):**
- 해상도: 960×768
- 품질: 70
- frame_skip: 6
- **→ 1시간에 약 228 MB**

---

## 🎯 추천 설정 시나리오

### 시나리오 1: 표준 모니터링 (기본값)
```json
"stirfry_save_resolution": {"width": 960, "height": 768},
"stirfry_jpeg_quality": 70,
"stirfry_frame_skip": 6
```
- **용량**: ~228 MB/시간
- **화질**: 충분히 좋음
- **FPS**: ~3.3 FPS
- **용도**: 대부분의 상황에 적합

### 시나리오 2: 고화질 필요
```json
"stirfry_save_resolution": {"width": 1920, "height": 1536},
"stirfry_jpeg_quality": 85,
"stirfry_frame_skip": 6
```
- **용량**: ~1.2 GB/시간
- **화질**: 매우 좋음
- **용도**: 상세 분석이 필요한 경우

### 시나리오 3: 초저용량 (스토리지 부족)
```json
"stirfry_save_resolution": {"width": 480, "height": 384},
"stirfry_jpeg_quality": 50,
"stirfry_frame_skip": 10
```
- **용량**: ~22 MB/시간
- **화질**: 보통
- **용도**: 스토리지가 매우 제한적인 경우

### 시나리오 4: 균형 잡힌 설정
```json
"stirfry_save_resolution": {"width": 1280, "height": 1024},
"stirfry_jpeg_quality": 70,
"stirfry_frame_skip": 10
```
- **용량**: ~120 MB/시간
- **화질**: 좋음
- **FPS**: ~2 FPS

---

## 🔧 설정 변경 방법

### 1. config.json 편집

```bash
cd ~/jetson-camera-monitor/autostart_autodown
nano config.json
```

### 2. 원하는 값으로 수정

예: 용량을 줄이고 싶은 경우
```json
"stirfry_save_resolution": {"width": 480, "height": 384},
"stirfry_jpeg_quality": 50,
"stirfry_frame_skip": 10
```

### 3. 저장 후 프로그램 재시작

```bash
# Ctrl+X → Y → Enter (nano 편집기)

# 프로그램 재시작
python3 JETSON1_INTEGRATED.py
```

**새로운 설정이 즉시 적용됩니다!**

---

## 📊 용량 확인 방법

### 실시간 용량 확인

```bash
# 왼쪽 카메라 용량 확인
du -sh ~/StirFry_Data/left/

# 오른쪽 카메라 용량 확인
du -sh ~/StirFry_Data/right/

# 전체 용량 확인
du -sh ~/StirFry_Data/
```

### 상세 용량 확인

```bash
# 날짜별 용량 확인
du -h ~/StirFry_Data/left/ | tail -10

# 파일 개수 확인
find ~/StirFry_Data/left/20251105/ -type f | wc -l
```

---

## 💡 팁

### 1. 테스트 권장
새로운 설정 적용 전:
1. 짧은 시간(5분) 녹화
2. 용량 확인
3. 1시간 환산 계산
4. 필요 시 재조정

### 2. 용량 부족 시 긴급 조치
```bash
# 오래된 데이터 삭제
rm -rf ~/StirFry_Data/left/20251101
rm -rf ~/StirFry_Data/right/20251101

# 또는 전체 삭제 (주의!)
rm -rf ~/StirFry_Data/*
```

### 3. 자동 정리 스크립트 (선택사항)
7일 이상 된 데이터 자동 삭제:
```bash
# crontab 추가
crontab -e

# 매일 새벽 3시 실행
0 3 * * * find ~/StirFry_Data -type d -mtime +7 -exec rm -rf {} \;
```

---

## ⚠️ 주의사항

1. **프로그램 재시작 필요**: config.json 수정 후 반드시 프로그램 재시작
2. **녹화 중 변경 불가**: 녹화 중에는 설정 변경해도 적용 안 됨 (재시작 필요)
3. **디스크 공간 체크**: 정기적으로 용량 확인 권장
4. **백업**: 중요한 데이터는 별도 백업

---

## 📞 문제 해결

### 용량이 예상보다 큼
- JPEG 품질 낮추기 (70 → 50)
- frame_skip 늘리기 (6 → 10)
- 해상도 줄이기 (960×768 → 480×384)

### 화질이 너무 나쁨
- JPEG 품질 높이기 (70 → 85)
- 해상도 높이기 (960×768 → 1280×1024)

### FPS가 너무 낮음
- frame_skip 줄이기 (6 → 3)

모든 설정은 **config.json**에서 간단히 변경 가능! 🎉
