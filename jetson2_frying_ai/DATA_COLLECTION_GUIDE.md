# 📊 데이터 수집 및 모델 개발 가이드

**Jetson #2 AI 모니터링 시스템**

---

## 🎯 개요

실제 환경에서 튀김 AI와 바켓 감지 모델을 개발하기 위한 데이터 수집 및 학습 가이드

---

## 📋 모델 개발 우선순위

### 1. 튀김 AI (Frying AI) - 쉬움 ⭐
**현재 상태**: 이미 완성됨 (HSV 기반 색상 분석)

**필요한 작업**:
- 실제 환경에서 샘플 이미지 10-20장 수집
- HSV 범위 파라미터 조정
- **학습 불필요!**

**소요 시간**: 1-2일

---

### 2. 바켓 감지 (Bucket Detection) - 중간 ⭐⭐
**현재 상태**: 모델 파일 필요 (`besta.pt`, `bestb.pt`)

**필요한 작업**:
1. 데이터 수집: 200-300장
2. 라벨링: Roboflow 사용
3. 학습: Roboflow 자동 학습 또는 Colab
4. 모델 배포

**소요 시간**: 1-2주

---

## 🔧 Phase 1: 튀김 AI 테스트 및 조정

### 현재 상태
`frying_segmenter.py`는 HSV 색상 기반으로 이미 완성되어 있습니다.

### 테스트 절차

#### 1. 샘플 이미지 수집
실제 튀김 환경에서 다양한 상태의 이미지 수집:

```bash
# 데이터 수집 디렉토리 생성
mkdir -p ~/frying_test_data
cd ~/frying_test_data
```

**수집할 상태**:
- 빈 냄비 (기름 없음): 5장
- 깨끗한 기름: 10장
- 튀기는 중 (갈색 30-50%): 15장
- 튀기는 중 (갈색 50-70%): 15장
- 다 익음 (황금색 많음): 15장
- 태움 (검은색): 5장

#### 2. HSV 범위 조정

현재 설정 (`frying_segmenter.py`):
```python
# Brown (갈색) - 익고 있는 음식
BROWN_HSV_RANGE = ([5, 40, 40], [25, 255, 200])

# Golden (황금색) - 완벽하게 익은 음식
GOLDEN_HSV_RANGE = ([20, 80, 80], [35, 255, 255])
```

**조정 방법**:
1. 샘플 이미지로 테스트
2. 색상 검출이 잘 안되면 HSV 범위 조정
3. 실제 프로그램에서 재테스트

#### 3. 즉시 사용 가능
조정 완료 후 바로 `JETSON2_INTEGRATED.py`에서 사용!

---

## 📸 Phase 2: 바켓 감지 데이터 수집

### 데이터 수집 계획

#### 필요한 데이터 양
| 상태 | 이미지 수 | 설명 |
|------|----------|------|
| 바켓 없음 (No Basket) | 50장 | 빈 공간만 |
| 바켓 있음 - 비어있음 (Empty) | 100장 | 다양한 각도, 조명 |
| 바켓 있음 - 음식 있음 (Filled) | 100장 | 음식 양 다양하게 |
| **총합** | **250장** | |

#### 수집 조건
- **다양한 각도**: 정면, 약간 옆, 위에서
- **다양한 조명**: 밝음, 보통, 어두움
- **다양한 음식 양** (Filled):
  - 10% 채움
  - 50% 채움
  - 100% 채움 (가득)
- **다양한 음식 종류**: 감자튀김, 치킨, 새우 등

---

## 🛠️ 데이터 수집 도구

### 자동 수집 도구 사용 (추천!) ⭐

**파일**: `data_collector.py`

#### 기본 사용법
```bash
cd ~/jetson-camera-monitor/jetson2_ai

# 튀김 AI 데이터 수집 (카메라 0, 1)
python3 data_collector.py --cameras 0,1 --output ./data/frying --mode manual

# 바켓 감지 데이터 수집 (카메라 2, 3)
python3 data_collector.py --cameras 2,3 --output ./data/bucket --mode manual

# 모든 카메라 (0, 1, 2, 3)
python3 data_collector.py --cameras 0,1,2,3 --output ./data/all --mode manual
```

#### 수동 모드 (Manual Mode)
화면을 보면서 직접 캡처:

```bash
python3 data_collector.py --cameras 0,1 --output ./data/frying --mode manual
```

**키 조작**:
- **스페이스바**: 즉시 캡처 (모든 카메라)
- **'a'**: 자동 캡처 시작/중지
- **'q'**: 종료

**장점**:
- 원하는 순간에 정확히 캡처
- 실시간 프리뷰 확인
- 수동 + 자동 모드 전환 가능

#### 자동 모드 (Auto Mode)
일정 간격으로 자동 캡처 (백그라운드):

```bash
# 5초마다 자동 캡처
python3 data_collector.py --cameras 2,3 --output ./data/bucket --mode auto --interval 5

# 10초마다 자동 캡처
python3 data_collector.py --cameras 0,1 --output ./data/frying --mode auto --interval 10
```

**장점**:
- 헤드리스 모드 (화면 없어도 됨)
- 장시간 자동 수집 가능
- Ctrl+C로 중지

#### 저장 구조
```
data/
├── frying/
│   ├── camera_0/
│   │   ├── cam0_20250105_140530.jpg
│   │   ├── cam0_20250105_140535.jpg
│   │   └── ...
│   └── camera_1/
│       ├── cam1_20250105_140530.jpg
│       └── ...
└── bucket/
    ├── camera_2/
    │   └── cam2_20250105_141000.jpg
    └── camera_3/
        └── cam3_20250105_141000.jpg
```

---

### 수동 수집 방법 (간단함, data_collector 없이)
현재 실행 중인 `JETSON2_INTEGRATED.py`를 사용:

1. 프로그램 실행
2. 카메라 화면 확인
3. 스크린샷 도구로 캡처
4. 파일명에 라벨 표시
   - `basket_empty_001.jpg`
   - `basket_filled_50percent_002.jpg`
   - `no_basket_001.jpg`

### 자동 수집 도구 (추천)
간단한 데이터 수집 스크립트 작성 가능:

```bash
# 예시: 5초마다 자동 캡처
python3 data_collector.py --cameras 2,3 --interval 5 --output ./data/bucket
```

**필요하면 요청 시 작성 가능합니다!**

---

## 🏷️ Phase 3: 데이터 라벨링

### Roboflow 사용 (추천)

#### 1. 계정 생성
- https://roboflow.com/
- 무료 계정: 10,000 이미지, 3개 프로젝트

#### 2. 프로젝트 생성
- Project Name: `bucket-detection`
- Project Type: **Instance Segmentation**
- License: Private

#### 3. 이미지 업로드
```bash
# 수집한 이미지를 Roboflow에 드래그 앤 드롭
```

#### 4. 라벨링
**Segmentation 모델용** (`besta.pt`):
- 바켓 영역을 다각형으로 표시
- 클래스: `basket`
- 바켓이 없는 이미지는 라벨 없이 저장

**Classification 모델용** (`bestb.pt`):
- 바켓 영역만 crop한 이미지 준비
- 클래스: `empty`, `filled`

#### 5. Dataset 생성
- Train/Valid/Test 분할: 70% / 20% / 10%
- Augmentation:
  - Flip: Horizontal
  - Rotate: ±15°
  - Brightness: ±15%
- Export Format: **YOLOv8**

---

## 🧠 Phase 4: 모델 학습

### 옵션 A: Roboflow 자동 학습 (가장 쉬움)
1. Roboflow에서 "Train with Roboflow"
2. 무료 크레딧으로 학습 (소형 모델)
3. 학습 완료 후 모델 다운로드
4. `besta.pt`, `bestb.pt` → Jetson에 복사

**장점**: 클릭 몇 번으로 완료
**단점**: 무료 크레딧 제한

---

### 옵션 B: Google Colab 학습 (무료 + 자유도 높음)

#### 1. Colab 노트북 생성
```python
# Install Ultralytics
!pip install ultralytics

# Download dataset from Roboflow
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_API_KEY")
project = rf.workspace().project("bucket-detection")
dataset = project.version(1).download("yolov8")
```

#### 2. Segmentation 모델 학습
```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO('yolov8n-seg.pt')  # nano 모델 (가장 빠름)

# Train
model.train(
    data='data.yaml',
    epochs=50,
    imgsz=512,
    batch=16,
    device=0  # GPU
)

# Export
model.export(format='torchscript')  # 또는 'onnx'
```

#### 3. Classification 모델 학습
```python
# Crop된 바켓 이미지로 학습
model = YOLO('yolov8n-cls.pt')

model.train(
    data='bucket_crops/',  # empty/, filled/ 폴더
    epochs=30,
    imgsz=160,
    batch=32
)
```

#### 4. 모델 다운로드
```python
# Colab에서 다운로드
from google.colab import files
files.download('runs/segment/train/weights/best.pt')  # besta.pt
files.download('runs/classify/train/weights/best.pt')  # bestb.pt
```

---

### 옵션 C: Jetson에서 직접 학습 (느림)
**비추천**: Jetson은 추론용, 학습은 너무 느림

---

## 📦 Phase 5: 모델 배포

### 1. 모델 파일 복사
```bash
# 개발 PC에서
scp besta.pt dkuyj@jetson2:~/jetson-camera-monitor/observe_add/
scp bestb.pt dkuyj@jetson2:~/jetson-camera-monitor/observe_add/

# Jetson에서 확인
ls -la ~/jetson-camera-monitor/observe_add/*.pt
```

### 2. Config 확인
```bash
cd ~/jetson-camera-monitor/jetson2_ai
cat config_jetson2.json
```

```json
{
  "observe_seg_model": "../observe_add/besta.pt",
  "observe_cls_model": "../observe_add/bestb.pt"
}
```

### 3. 테스트 실행
```bash
python3 JETSON2_INTEGRATED.py
```

GUI에서:
1. "바켓 감지 시작" 클릭
2. 실시간 검출 확인
3. 상태 변화 로그 확인

---

## 🧪 Phase 6: 모델 평가 및 개선

### 평가 지표

#### Segmentation 모델
- **IoU (Intersection over Union)**: 바켓 영역 정확도
- **목표**: IoU > 0.7

#### Classification 모델
- **Accuracy**: 전체 정확도
- **Precision/Recall**: Empty vs Filled 구분 정확도
- **목표**: Accuracy > 90%

### 개선 방법

#### 정확도가 낮을 때
1. **데이터 추가 수집**: 특히 실패한 케이스
2. **Augmentation 조정**: 더 다양한 변형
3. **모델 크기 증가**: nano → small → medium
4. **학습 epoch 증가**: 50 → 100

#### False Positive 많을 때
- Confidence threshold 조정:
```json
"conf_seg": 0.5  // → 0.6 또는 0.7로 증가
```

#### False Negative 많을 때
- Confidence threshold 감소:
```json
"conf_seg": 0.5  // → 0.3 또는 0.4로 감소
```

---

## 📅 전체 타임라인

| 주차 | 작업 | 소요 시간 |
|------|------|----------|
| 1주 | 튀김 AI 테스트 및 조정 | 1-2일 |
| 1주 | 바켓 데이터 수집 (자동) | 3-5일 (백그라운드) |
| 2주 | 데이터 라벨링 (Roboflow) | 2-3일 |
| 2주 | 모델 학습 (Roboflow/Colab) | 1일 (자동) |
| 2주 | 모델 배포 및 테스트 | 1일 |
| 3주 | 모델 개선 및 최종 조정 | 2-3일 |

**총 소요 시간**: 약 2-3주

---

## 💡 빠른 시작 팁

### 최소 작업으로 시작하기

#### Day 1: 튀김 AI
- 샘플 이미지 5장만 수집
- HSV 범위 조정
- **즉시 사용 가능!**

#### Day 2-7: 바켓 데이터 수집
- 자동 캡처 프로그램 실행
- 백그라운드로 이미지 수집
- 작업 중단 없음

#### Week 2: 바켓 모델 개발
- Roboflow에 업로드 (30분)
- 라벨링 (2-3시간, 한 번에 안 해도 됨)
- 자동 학습 (클릭 한 번)
- 모델 다운로드 및 배포

---

## 🆘 문제 해결

### 데이터가 부족할 때
- **최소 필요 데이터**: 각 클래스당 50장
- **권장 데이터**: 각 클래스당 100-200장
- **Augmentation 활용**: 원본 100장 → 500장으로 증폭

### 라벨링이 너무 오래 걸릴 때
- **Pre-annotation 사용**: Roboflow의 자동 라벨링 기능
- **단순화**: Bounding box만 (Segmentation 대신)
- **외주**: Freelancer 활용

### 모델 성능이 낮을 때
- **데이터 품질 확인**: 흐릿한 이미지 제거
- **라벨 정확도 확인**: 잘못된 라벨 수정
- **하이퍼파라미터 조정**: Learning rate, batch size

---

## 📞 다음 단계

### 즉시 시작 가능
1. ✅ 튀김 AI: 샘플 이미지만 수집하면 바로 테스트
2. ✅ 바켓 감지: 데이터 수집 도구 필요하면 요청

### 추가 도구 제작 가능
- [ ] 자동 데이터 수집 스크립트
- [ ] 이미지 전처리 도구
- [ ] 모델 성능 평가 스크립트

**필요한 도구 있으면 말씀해주세요!**
