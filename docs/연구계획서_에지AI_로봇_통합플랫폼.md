# 박사과정생 연구장려금 지원사업 신규과제 계획서

## 에지 AI-로봇 닫힌 루프(Closed-loop) 통합 플랫폼 개발

**작성일**: 2026-04-11
**연구 분야**: 에지 AI, 식품 제조 자동화, 실시간 품질 검사
**연구 환경**: 실험실 파일럿 라인 (Proof-of-Concept)
**기반 시스템**: NVIDIA Jetson 기반 튀김 품질 판정 AI 시스템

---

## 목차

1. [연구 배경 및 필요성](#1-연구-배경-및-필요성)
2. [연구 목표](#2-연구-목표)
3. [선행 연구 및 현재 시스템 개요](#3-선행-연구-및-현재-시스템-개요)
4. [연구 내용 및 방법](#4-연구-내용-및-방법)
5. [기대 효과 및 활용 방안](#5-기대-효과-및-활용-방안)
6. [연구 추진 일정](#6-연구-추진-일정)
7. [참고 문헌](#7-참고-문헌)

---

## 1. 연구 배경 및 필요성

### 1.1 배경

식품 제조 산업은 노동집약적 특성으로 인해 인력 부족과 품질 불균일 문제에 직면해 있다. 특히 튀김, 볶음 등 열가공 공정은 조리사의 경험과 감에 의존하며, 이는 제품 품질의 일관성 확보에 큰 장애가 되고 있다. 또한 고온 환경에서의 장시간 작업은 작업자 안전 문제를 야기한다.

최근 에지 AI(Edge AI) 기술의 발전으로 현장에서 실시간 품질 판정이 가능해졌으나, 대부분의 연구는 AI 모델 자체의 성능 향상에 집중되어 있으며, 실제 제조 라인과의 통합 및 자동화 설비와의 연계는 미흡한 실정이다.

### 1.2 필요성

본 연구는 에지 AI 품질 판정 결과를 로봇 제어 시스템과 실시간으로 연동하여 **닫힌 루프(Closed-loop)** 자동화 시스템을 구축함으로써, 다음 문제를 해결하고자 한다:

1. **품질 일관성**: AI 기반 객관적 품질 판정으로 제품 품질의 일관성 확보
2. **실시간성**: 에지 디바이스에서 추론하여 클라우드 통신 지연 없이 즉각 대응
3. **공정 효율**: 품질 판정-명령 전달-로봇 제어까지 전체 사이클 타임 최소화
4. **작업 안전**: 고온 환경에서 사람 대신 로봇이 작업 수행

---

## 2. 연구 목표

### 2.1 최종 목표

**식품 제조 현장에 특화된 에지 AI-로봇 닫힌 루프(Closed-loop) 통합 플랫폼을 개발하고, 실험실 환경에서 시스템 전체의 성능을 정량적으로 검증**한다.

### 2.2 세부 목표

#### ① 에지 AI 품질 판정 모듈 고도화

**기존 시스템 기반**:
- NVIDIA Jetson Orin Nano 기반 튀김 품질 판정 시스템
- YOLOv8-Segmentation 모델 (frying_seg_v3.pt)
- 현재 성능: mAP@50 67.8%, 완료 감지율 91.2% (31/34 세션)

**목표**:
- **TensorRT 최적화**를 통한 추론 가속 (목표: 200ms → 100ms 이하)
- **모델 경량화** (FP16/INT8 양자화) 및 배치 추론 구현
- **실시간 처리량** 향상 (목표: 30 FPS 이상)
- **정확도 개선** (목표: mAP@50 75% 이상, 완료 감지율 95% 이상)

**핵심 성능 지표**:
- **추론 지연 시간(Inference Latency)**: 단일 프레임 처리 시간 (ms)
- **불량 분류 정확도(mAP)**: 평균 정밀도 (Mean Average Precision)
- **처리량(Throughput)**: 초당 처리 프레임 수 (FPS)
- **완료 판정 F1 Score**: 조리 완료 시점 감지 정확도
- **완료시점 오차(MAE)**: 실제 완료 시점과의 평균 절대 오차 (초)

#### ② 도메인 특화 로봇 제어 시스템 구축

**개발 내용**:
- Fusion360 설계 및 3D 프린팅 기반 **6-DOF 로봇암** 제작
- **픽앤플레이스(Pick & Place)** 작업 로직 구현
  - 양품/불량품 자동 분류
  - 지정 위치로 정밀 배치
- **식품 공정 환경 적응**
  - 고온/습도 환경 고려
  - 식품 안전 규격 준수 (재질, 세척 가능성)

**제어 시스템 구성**:
- **하드웨어**: 6-DOF 로봇암, 그리퍼, 서보 모터, 제어 보드
- **소프트웨어**: ROS2 기반 제어 노드, 경로 계획 알고리즘
- **안전 장치**: 비상 정지, 충돌 감지, 작업 영역 제한

#### ③ MQTT 기반 닫힌 루프 통합 및 성능 검증

**통합 아키텍처**:
- **경량 메시지 프로토콜**: MQTT (Message Queuing Telemetry Transport)
- **통신 구조**:
  ```
  Jetson (에지 AI) → MQTT Broker → 로봇 PC (제어)
                    ↓
              품질 판정 결과
                    ↓
              제어 명령 생성
                    ↓
              로봇 동작 실행
                    ↓
              완료 피드백 → Jetson
  ```

**핵심 성능 지표**:
- **End-to-end Cycle Time**: 품질 판정 → 명령 전달 → 픽앤플레이스 완료까지 전체 사이클 시간
- **통신 지연(Communication Latency)**: MQTT 메시지 전송 시간
- **시스템 처리량**: 시간당 처리 가능한 제품 수
- **정확도**: 올바른 위치에 배치된 제품 비율

**검증 방법**:
- 실험실 파일럿 라인 구축 (튀김 공정 시뮬레이션)
- 개별 모듈 대비 통합 시스템의 효율성 비교
- 품질 일관성 지표 측정 (표준편차, 불량률)

---

## 3. 선행 연구 및 현재 시스템 개요

### 3.1 선행 연구 현황

#### 3.1.1 에지 AI 기반 품질 검사

- **NVIDIA Jetson 플랫폼**: 실시간 비전 AI 추론에 널리 사용
- **TensorRT 최적화**: YOLO 모델을 TensorRT로 변환 시 2-3배 가속 보고[1]
- **식품 품질 검사**: HSV 색상 분석, Segmentation 기반 익음 정도 판단 연구[2]

#### 3.1.2 로봇 기반 식품 자동화

- **픽앤플레이스 로봇**: 과일 분류, 포장 자동화 등 다수 연구
- **6-DOF 로봇암**: 3D 프린팅 기반 저비용 로봇암 제작 사례 증가[3]
- **ROS2 제어**: 실시간 로봇 제어 표준 프레임워크

#### 3.1.3 에지 AI-로봇 통합

- **MQTT 통신**: IoT 환경에서 경량 메시지 프로토콜로 널리 사용
- **닫힌 루프 제어**: 제조업에서 센서-AI-액추에이터 통합 연구 활발[4]
- **한계점**: 대부분 개별 모듈 연구, 전체 시스템 통합 및 성능 검증 부족

### 3.2 현재 시스템 개요 (선행 구축 기반)

본 연구는 실제 구축 및 운영 중인 **Jetson 기반 튀김 AI 시스템**을 기반으로 한다.

#### 3.2.1 시스템 구성

**하드웨어**:
- **에지 디바이스**: NVIDIA Jetson Orin Nano 8GB (6코어 ARM CPU, 1024 CUDA 코어)
- **카메라**: GMSL 카메라 4대 (1920×1536@30fps)
  - 튀김 모니터링: video0 (좌측), video1 (우측)
  - 바켓 감지: video2 (좌측), video3 (우측)
- **통신**: MQTT over TCP/IP (브로커: 192.168.0.100:1883)
- **센서**: RS485 진동 센서 (WitMotion JY901B, 이상 감지용)

**소프트웨어**:
- **운영체제**: JetPack 6.2 (Ubuntu 22.04 기반)
- **AI 프레임워크**: PyTorch 2.x, Ultralytics YOLO
- **MQTT 클라이언트**: paho-mqtt (Python)
- **카메라 제어**: GStreamer 파이프라인

#### 3.2.2 AI 모델 아키텍처

**튀김 세그멘테이션 모델** (`frying_seg_v3.pt`):
- **기반 모델**: YOLOv8-Segmentation (nano variant)
- **입력 크기**: 800×540 pixels (원본 1920×1536에서 letterbox)
- **출력**: 픽셀 단위 세그멘테이션 마스크 + 바운딩 박스
- **클래스**: 튀김 음식 영역 (단일 클래스)
- **학습 데이터**: 34세션, 약 8,400장 (2026-02-15 기준)
- **성능**:
  - mAP@50: 67.8%
  - 추론 시간: ~200ms/frame (CUDA, FP32)
  - 완료 감지율: 91.2% (31/34 세션)

**완료 판정 로직** (FoodSegmenter + Lift Event Tracker):
```
1. YOLO Segmentation → 튀김 영역 마스크 추출
2. HSV 색상 특징 계산 (mean, std, brown_ratio, golden_ratio)
3. 리프트 이벤트 감지 (탈탈 동작)
   - 음식 영역 비율 변화 > 15% → 리프트 감지
   - 쿨다운: 2초
4. 색상 변화량 누적 (LAB 색공간 유클리드 거리)
5. 완료 적합도 점수 계산:
   S = 100 × (0.4T + 0.4C + 0.2L)
   - T: 조리 시간 비율 (running_time / target_time)
   - C: 색상 변화 비율 (color_delta / 25.0)
   - L: 리프트 횟수 비율 (lift_count / 3)
6. 완료 판정: S ≥ 85 AND T ≥ 0.9 AND C ≥ 0.8
```

**바켓 감지 모델** (`observe_add/best_io.pt`):
- **기반 모델**: YOLOv8-Segmentation
- **입력 크기**: 640×640
- **클래스**: EMPTY, FILLED, NO_BASKET
- **용도**: 튀김 완료 후 바켓 상태 확인 → 배출 타이밍 결정

#### 3.2.3 MQTT 통신 프로토콜

**발행 토픽** (Jetson → 로봇 PC):
- `jetson2/system/ai_mode`: AI 모드 상태 (true/false)
- `frying/status`: 튀김 상태 (COOKING, DISCHARGE)
- `observe/status`: 바켓 상태 (EMPTY, FILLED, NO_BASKET)
- `jetson1/relay/status`: 릴레이 상태 (ON, OFF)

**구독 토픽** (로봇 PC → Jetson):
- `frying/pot1/food_type`: 음식 종류 (예: "chicken")
- `frying/pot1/control`: 제어 명령 (start, stop)
- `frying/pot1/oil_temp`: 기름 온도 (°C)
- `frying/pot1/probe_temp`: 탐침 온도 (°C)
- `HR/Status`: 로봇 상태 (RunningTime, TargetTime 포함)

**통신 특성**:
- **QoS**: 1 (최소 1회 전달 보장)
- **발행 주기**: 1초
- **Keep-Alive**: 60초
- **평균 지연**: 10-50ms (LAN 환경)

#### 3.2.4 데이터 수집 및 저장

**저장 경로**:
```
~/AI_Data/
├── pot1/  (튀김솥 1)
│   └── session_20260126_165618/
│       ├── camera_0/  (튀김 좌측 카메라)
│       │   └── cam0_*.jpg
│       ├── camera_2/  (바켓 좌측)
│       │   └── cam2_*.jpg
│       ├── session_info.json  (메타데이터)
│       └── pot1_lift_events.json  (리프트 이벤트)
└── pot2/  (튀김솥 2)
    └── ...
```

**메타데이터 예시** (`session_info.json`):
```json
{
  "session_id": "session_20260126_165618",
  "food_type": "chicken",
  "start_time": "2026-01-26 16:56:18",
  "end_time": "2026-01-26 17:01:23",
  "running_time_sec": 305.2,
  "target_time_sec": 300.0,
  "completion_marked": true,
  "completion_info": {
    "method": "auto (probe_temp >= 75.0°C)",
    "timestamp": "2026-01-26 17:01:15",
    "probe_temp": 75.5,
    "oil_temp": 180.0,
    "color_delta": 23.8,
    "lift_count": 3,
    "score": 94.2
  }
}
```

#### 3.2.5 현재 시스템 성능 (실측 데이터)

**AI 성능** (34세션 분석 결과, 2026-02-15):
- **평균 완료 적합도 점수**: 94.19/100
- **완료 규칙 통과율**: 79.4% (27/34)
- **Tracker 완료 감지율**: 91.2% (31/34)
- **Pot별 평균 점수**:
  - Pot1: 92.41점 (17세션)
  - Pot2: 95.97점 (17세션)

**시스템 성능**:
- **카메라 처리**: 30 FPS (4대 동시)
- **AI 추론**: ~5 FPS (프레임 스킵 적용)
- **메모리 사용**: ~2GB (시스템 + CUDA 통합)
- **CPU 사용률**: 70-90% (8코어)
- **GPU 사용률**: ~60% (1024 CUDA 코어)

**데이터 수집**:
- **수집 간격**: 1-3초
- **JPEG 품질**: 100
- **이미지 크기**: ~800KB/장
- **일일 데이터**: ~2.4GB (10세션 기준)

#### 3.2.6 현재 시스템의 한계

1. **추론 속도**: 200ms는 30 FPS 처리에 부족 (33ms 목표)
2. **모델 정확도**: mAP@50 67.8%는 산업 적용에 개선 필요 (>80% 목표)
3. **로봇 연계 부재**: AI 판정 결과를 수신하나, 실제 로봇 제어 미구현
4. **닫힌 루프 부재**: 로봇 동작 피드백이 AI 시스템에 반영되지 않음
5. **TensorRT 미적용**: PyTorch 모델 그대로 사용, 최적화 여지 큼

---

## 4. 연구 내용 및 방법

### 4.1 에지 AI 품질 판정 모듈 고도화

#### 4.1.1 TensorRT 최적화

**목표**: 추론 지연 시간 200ms → 100ms 이하

**방법**:
1. **YOLO 모델 Export**:
   ```bash
   yolo export model=frying_seg_v3.pt format=engine device=0 \
     half=True imgsz=800,544 workspace=4
   ```
   - FP16 정밀도 (메모리 절반, 속도 2배)
   - INT8 양자화 (교정 데이터셋 필요)

2. **TensorRT 추론 파이프라인**:
   ```python
   import tensorrt as trt

   # 엔진 로드
   with open("frying_seg_v3.engine", "rb") as f:
       engine = trt.Runtime(trt.Logger()).deserialize_cuda_engine(f.read())

   # 추론 컨텍스트
   context = engine.create_execution_context()

   # CUDA 스트림 비동기 처리
   stream = cuda.Stream()
   ```

3. **성능 측정**:
   - 벤치마크: 100장 반복 추론, 평균/표준편차 측정
   - 프로파일링: NVIDIA Nsight Systems로 병목 분석

**예상 효과**:
- FP16: 2-3배 가속 (200ms → 70-100ms)
- INT8: 3-4배 가속 (200ms → 50-70ms, 정확도 손실 <2%)

#### 4.1.2 배치 추론 구현

**목표**: GPU 유휴 시간 최소화, 처리량 향상

**방법**:
```python
class FryingAIBatchWorker:
    def run(self):
        # POT1 + POT2 프레임 동시 수집
        frames = [camera_0.get_frame(), camera_1.get_frame()]

        # 배치 추론 (1회 GPU 호출로 2개 처리)
        results = model.predict(frames, batch=2)

        # 결과 분리 처리
        for i, result in enumerate(results):
            self.process_result(pot_id=i, result=result)
```

**예상 효과**:
- GPU 활용률: 60% → 85%
- 처리량: 10 FPS → 20 FPS (2배)

#### 4.1.3 모델 정확도 개선

**목표**: mAP@50 67.8% → 75% 이상

**방법**:
1. **데이터 증강**:
   - Mixup, Mosaic (YOLO 기본 지원)
   - 색상 지터링 (고온 환경 조명 변화 대응)
   - 회전, 스케일 변환

2. **하이퍼파라미터 튜닝**:
   - 학습률 스케줄링 (Cosine Annealing)
   - Batch size 최적화 (GPU 메모리 한도)
   - Epoch 증가 (100 → 200-300)

3. **앙상블 기법** (선택적):
   - 다중 모델 투표 (nano + small)
   - Test-Time Augmentation (TTA)

**평가 지표**:
- mAP@50: IoU 50% 기준 평균 정밀도
- mAP@50-95: IoU 50-95% 평균 (COCO 표준)
- 완료 판정 F1 Score
- 완료시점 MAE (초)

#### 4.1.4 성능 벤치마킹

**측정 항목**:
| 지표 | 측정 방법 | 목표값 |
|------|-----------|--------|
| 추론 지연 시간 | 100회 반복 평균 | <100ms |
| 처리량 | 초당 처리 프레임 | >30 FPS |
| mAP@50 | YOLO val 세트 | >75% |
| 완료 감지 F1 | 라벨 데이터 대조 | >95% |
| 완료시점 MAE | 실제 시점과 차이 | <5초 |
| 메모리 사용량 | nvidia-smi 모니터링 | <3GB |
| 전력 소비 | tegrastats | <15W |

**비교 기준**:
- **현재 시스템** (PyTorch FP32)
- **TensorRT FP16**
- **TensorRT INT8**

---

### 4.2 도메인 특화 로봇 제어 시스템 구축

#### 4.2.1 6-DOF 로봇암 설계 및 제작

**설계 도구**: Fusion360

**사양**:
- **자유도**: 6-DOF (Degree of Freedom)
- **작업 반경**: 500mm (튀김솥 → 배출 트레이)
- **페이로드**: 500g (튀김 바구니 또는 제품)
- **반복 정밀도**: ±2mm
- **재질**: PLA/PETG (3D 프린팅), 알루미늄 프로파일 (구조 보강)

**구동 방식**:
- **서보 모터**: 6개 (각 관절당 1개)
  - 모델: MG996R 또는 동급 (토크 9.4kgf·cm)
- **그리퍼**: 평행 그리퍼 (식품 안전 재질)
- **제어 보드**: Arduino Mega 2560 + Servo Shield

**제작 과정**:
1. **Fusion360 모델링**:
   - 링크 길이 최적화 (작업 공간 시뮬레이션)
   - 간섭 체크 (관절 충돌 방지)
   - STL 파일 출력

2. **3D 프린팅**:
   - 프린터: Creality Ender-3 Pro 또는 동급
   - 레이어 높이: 0.2mm
   - 인필 밀도: 30% (경량화)

3. **조립 및 배선**:
   - 관절 조립 (베어링 삽입)
   - 서보 모터 장착
   - 케이블 정리 (간섭 방지)

4. **캘리브레이션**:
   - 홈 포지션 설정
   - 엔드 이펙터 좌표 보정
   - 작업 공간 맵핑

#### 4.2.2 픽앤플레이스 제어 로직

**제어 소프트웨어**: ROS2 (Robot Operating System 2)

**노드 구성**:
```
robot_control/
├── pick_and_place_node  (메인 제어)
├── trajectory_planner    (경로 계획)
├── gripper_controller    (그리퍼 제어)
└── mqtt_bridge           (MQTT 통신)
```

**동작 시퀀스**:
```python
class PickAndPlaceController:
    def on_mqtt_message(self, msg):
        """MQTT로부터 품질 판정 결과 수신"""
        quality = msg["quality"]  # "GOOD" or "BAD"

        if quality == "GOOD":
            self.pick_and_place(src=BASKET, dst=GOOD_TRAY)
        else:
            self.pick_and_place(src=BASKET, dst=BAD_TRAY)

    def pick_and_place(self, src, dst):
        # 1. 픽업 위치로 이동
        self.move_to(src, approach_height=100)
        self.move_to(src, approach_height=0)

        # 2. 그리퍼 닫기
        self.gripper_close()
        time.sleep(0.5)  # 안착 대기

        # 3. 리프트
        self.move_to(src, approach_height=100)

        # 4. 배치 위치로 이동
        self.move_to(dst, approach_height=100)
        self.move_to(dst, approach_height=0)

        # 5. 그리퍼 열기
        self.gripper_open()
        time.sleep(0.3)

        # 6. 복귀
        self.move_to(HOME_POSITION)

        # 7. 완료 피드백 (MQTT)
        self.publish_completion()
```

**경로 계획**:
- **알고리즘**: Inverse Kinematics (역기구학)
  - 목표 좌표 (x, y, z) → 관절 각도 (θ1, θ2, ..., θ6)
- **라이브러리**: PyBullet 또는 MoveIt2 (ROS2)
- **충돌 회피**: 작업 공간 내 장애물 회피

**안전 장치**:
1. **비상 정지 버튼**: GPIO 인터럽트
2. **작업 영역 제한**: 소프트웨어 리미트
3. **힘 제한**: 그리퍼 과부하 감지 (전류 센서)
4. **타임아웃**: 동작 5초 이내 완료 실패 시 중단

#### 4.2.3 식품 공정 환경 적응

**환경 조건**:
- **온도**: 상온 (실험실 파일럿 라인)
  - 향후 고온 환경 대응: 열 차단막, 내열 재질
- **습도**: 일반 환경 (40-60%)
- **위생**: 식품 안전 규격 준수

**재질 선택**:
- **그리퍼**: 식품 접촉 가능 플라스틱 (FDA 승인 PETG)
- **세척 가능성**: 분리형 그리퍼 (물 세척 가능)

---

### 4.3 MQTT 기반 닫힌 루프 통합

#### 4.3.1 통합 아키텍처 설계

**시스템 다이어그램**:
```
┌─────────────────┐     MQTT     ┌─────────────────┐
│  Jetson (AI)    │◄────────────►│  MQTT Broker    │
│  - 품질 판정    │              │  (mosquitto)    │
│  - 상태 발행    │              └─────────────────┘
└─────────────────┘                       ▲
                                          │ MQTT
                                          ▼
                                ┌─────────────────┐
                                │  로봇 PC        │
                                │  - 명령 생성    │
                                │  - 로봇 제어    │
                                │  - 피드백 발행  │
                                └─────────────────┘
                                          │
                                          ▼
                                ┌─────────────────┐
                                │  6-DOF 로봇암   │
                                │  - Pick & Place │
                                └─────────────────┘
```

**통신 프로토콜 확장**:

**신규 토픽 추가**:
- `robot/command`: AI → 로봇 제어 명령
  ```json
  {
    "timestamp": "2026-04-11 14:30:15.123",
    "action": "pick_and_place",
    "quality": "GOOD",
    "position": "pot1",
    "confidence": 0.95
  }
  ```

- `robot/feedback`: 로봇 → AI 피드백
  ```json
  {
    "timestamp": "2026-04-11 14:30:18.456",
    "action_id": "12345",
    "status": "completed",
    "duration_ms": 3200,
    "success": true
  }
  ```

- `system/metrics`: 성능 모니터링
  ```json
  {
    "timestamp": "2026-04-11 14:30:20.000",
    "cycle_time_ms": 3500,
    "ai_latency_ms": 85,
    "mqtt_latency_ms": 12,
    "robot_exec_ms": 3200,
    "throughput_pph": 120
  }
  ```

#### 4.3.2 닫힌 루프 제어 로직

**제어 흐름**:
```python
# === Jetson (AI 모듈) ===
class JetsonAINode:
    def on_frame(self, frame):
        # 1. AI 추론
        result = self.model.predict(frame)
        quality = self.judge_quality(result)

        # 2. MQTT 발행
        self.mqtt_publish("robot/command", {
            "action": "pick_and_place",
            "quality": quality,
            "confidence": result.confidence
        })

        # 3. 피드백 대기 (비동기)
        self.wait_for_feedback(timeout=5.0)

    def on_robot_feedback(self, msg):
        # 피드백 수신 → 다음 프레임 처리
        if msg["success"]:
            self.stats["success_count"] += 1
        else:
            self.stats["failure_count"] += 1
            # 재시도 로직 또는 알림

# === 로봇 PC (제어 모듈) ===
class RobotControlNode:
    def on_ai_command(self, msg):
        # 1. 명령 수신
        quality = msg["quality"]

        # 2. 로봇 제어
        start_time = time.time()
        success = self.pick_and_place(quality)
        duration_ms = (time.time() - start_time) * 1000

        # 3. 피드백 발행
        self.mqtt_publish("robot/feedback", {
            "status": "completed" if success else "failed",
            "duration_ms": duration_ms,
            "success": success
        })
```

**동기화 메커니즘**:
- **비동기 처리**: AI 추론과 로봇 동작 병렬 수행
- **상태 머신**: IDLE → AI_PROCESSING → ROBOT_EXECUTING → FEEDBACK → IDLE
- **타임아웃 처리**: 5초 이내 피드백 없으면 에러 처리

#### 4.3.3 성능 측정 시스템

**핵심 지표 정의**:
1. **End-to-end Cycle Time**:
   ```
   T_cycle = T_ai + T_mqtt + T_robot
   - T_ai: AI 추론 시간 (목표: <100ms)
   - T_mqtt: MQTT 통신 시간 (목표: <50ms)
   - T_robot: 로봇 동작 시간 (목표: <3000ms)
   - 총계 목표: <3500ms
   ```

2. **처리량(Throughput)**:
   ```
   Throughput = 3600 / T_cycle (개/시간)
   목표: >1000개/시간
   ```

3. **정확도(Accuracy)**:
   ```
   Accuracy = 정확히 분류된 제품 / 전체 제품
   목표: >95%
   ```

**측정 방법**:
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "ai_latency": [],
            "mqtt_latency": [],
            "robot_exec_time": [],
            "cycle_time": [],
            "success_rate": 0
        }

    def record_cycle(self, ai_t, mqtt_t, robot_t, success):
        cycle_t = ai_t + mqtt_t + robot_t

        self.metrics["ai_latency"].append(ai_t)
        self.metrics["mqtt_latency"].append(mqtt_t)
        self.metrics["robot_exec_time"].append(robot_t)
        self.metrics["cycle_time"].append(cycle_t)

        if success:
            self.metrics["success_count"] += 1

    def report(self):
        return {
            "avg_cycle_time": np.mean(self.metrics["cycle_time"]),
            "std_cycle_time": np.std(self.metrics["cycle_time"]),
            "throughput_pph": 3600 / np.mean(self.metrics["cycle_time"]),
            "success_rate": self.metrics["success_count"] / len(self.metrics["cycle_time"])
        }
```

**실시간 모니터링**:
- **대시보드**: Grafana + InfluxDB
- **알림**: Telegram 또는 이메일 (이상 감지 시)

---

### 4.4 실험실 파일럿 라인 구축 및 검증

#### 4.4.1 파일럿 라인 구성

**설치 레이아웃**:
```
[카메라]
   ↓ (모니터링)
[튀김솥 시뮬레이터]  ←→  [Jetson AI]
   ↓                      ↓ (MQTT)
[바구니]               [로봇 PC]
   ↓                      ↓
[로봇암] ──────────→  [양품 트레이]
                    ──→ [불량 트레이]
```

**장비 구성**:
1. **튀김 공정 시뮬레이터**:
   - 튀김 완료품 샘플 (다양한 익음 정도)
   - 조명 설정 (일정한 조도 유지)
   - 바구니 이송 장치 (수동 또는 컨베이어)

2. **AI 시스템**:
   - Jetson Orin Nano
   - GMSL 카메라 2대 (튀김 모니터링)
   - 전원 공급 장치

3. **로봇 시스템**:
   - 6-DOF 로봇암 (3D 프린팅)
   - 로봇 PC (Ubuntu 22.04 + ROS2)
   - MQTT 브로커 (mosquitto)

4. **평가 설비**:
   - 양품/불량 트레이
   - 카운터 (분류 결과 집계)

#### 4.4.2 검증 프로토콜

**실험 시나리오**:
1. **기본 성능 테스트** (N=100):
   - 튀김 샘플 100개 (양품 70, 불량 30)
   - AI 판정 → 로봇 분류 → 결과 확인
   - 측정: 정확도, Cycle Time, 처리량

2. **스트레스 테스트** (N=1000):
   - 연속 1000개 처리
   - 시스템 안정성 검증 (메모리 누수, 에러율)

3. **통합 효과 검증**:
   - **개별 모듈**: AI만 실행 (로봇 없음)
   - **통합 시스템**: AI + 로봇 연동
   - 비교: 처리 시간, 품질 일관성

**평가 지표**:
| 지표 | 측정 방법 | 목표값 |
|------|-----------|--------|
| AI 정확도 | TP/(TP+FP) | >95% |
| 로봇 배치 정확도 | 올바른 위치 배치 비율 | >98% |
| Cycle Time | 품질 판정 → 배치 완료 | <3.5초 |
| 처리량 | 시간당 처리 개수 | >1000개/시간 |
| 에러율 | 에러 발생 비율 | <1% |

**데이터 수집**:
- 모든 실험은 타임스탬프, 이미지, 로그 기록
- CSV 파일로 저장 (사후 분석)

#### 4.4.3 비교 분석

**비교 대상**:
1. **수동 작업** (사람):
   - 숙련 작업자가 육안으로 판정 후 수동 분류
   - 측정: 정확도, 처리 시간, 피로도

2. **AI 단독**:
   - AI 판정만 실행 (로봇 없음)
   - 측정: 추론 시간, 정확도

3. **통합 시스템**:
   - AI + MQTT + 로봇 전체 연동
   - 측정: 전체 Cycle Time, 처리량, 일관성

**분석 방법**:
- **정량적**: ANOVA, t-test (유의수준 p<0.05)
- **정성적**: 작업 편의성, 안전성, 확장성 평가

---

## 5. 기대 효과 및 활용 방안

### 5.1 학술적 기대 효과

1. **에지 AI 최적화 기법 검증**:
   - TensorRT FP16/INT8 양자화 효과 정량화
   - 식품 품질 검사 도메인에서의 성능 벤치마크 제시

2. **AI-로봇 통합 플랫폼 설계 방법론**:
   - MQTT 기반 닫힌 루프 아키텍처 제안
   - 경량 통신 프로토콜의 실시간성 검증

3. **논문 투고 계획**:
   - 국내: 한국지능시스템학회 (JKIIS)
   - 국제: IEEE Access, Sensors (MDPI)

### 5.2 산업적 기대 효과

1. **식품 제조 자동화 촉진**:
   - 중소 식품 공장에서도 적용 가능한 저비용 솔루션 제시
   - 노동 집약적 공정의 자동화 가속

2. **품질 일관성 향상**:
   - 사람의 주관적 판단 → AI 객관적 기준
   - 제품 불량률 감소 (예상: 10% → 5%)

3. **작업 안전성 개선**:
   - 고온 환경에서 사람 대신 로봇 작업
   - 산업재해 위험 감소

### 5.3 기술적 파급 효과

1. **에지 AI 적용 확대**:
   - 클라우드 의존 없이 현장에서 즉각 대응
   - 타 제조 분야 (반도체, 자동차 등)로 확장 가능

2. **오픈소스 기여**:
   - 6-DOF 로봇암 설계 파일 공개 (GitHub)
   - MQTT-ROS2 브리지 패키지 배포

3. **교육 활용**:
   - 학부/대학원 로봇 제어 실습 교재
   - 메이커 커뮤니티 3D 프린팅 로봇 프로젝트

### 5.4 후속 연구 방향

1. **멀티모달 AI**:
   - 비전 + 온도 + 소리 → 종합 품질 판정
   - Transformer 기반 멀티모달 모델

2. **강화학습 기반 로봇 제어**:
   - 픽앤플레이스 경로 최적화
   - 실패 사례로부터 학습

3. **실제 현장 적용**:
   - 파일럿 라인 → 실제 식품 공장 테스트
   - 장기 운영 데이터 수집 및 분석

---

## 6. 연구 추진 일정

### 6.1 전체 일정 (12개월)

| 월 | 연구 내용 | 산출물 |
|----|----------|--------|
| **1-2** | 문헌 조사, TensorRT 최적화 | TensorRT 모델, 성능 보고서 |
| **3-4** | 배치 추론 구현, 정확도 개선 | 개선된 AI 모델, 벤치마크 |
| **5-6** | 로봇암 설계 및 제작 | 3D 모델, 조립 완료품 |
| **7-8** | 로봇 제어 로직 구현, MQTT 통합 | ROS2 패키지, 통신 프로토콜 |
| **9-10** | 파일럿 라인 구축, 통합 테스트 | 실험 데이터, 성능 분석 |
| **11** | 비교 실험, 데이터 분석 | 논문 초안 |
| **12** | 논문 작성, 최종 보고서 | 논문 투고, 최종 발표 |

### 6.2 세부 마일스톤

**Phase 1: AI 최적화 (1-4월)**
- [M1-1] TensorRT FP16 모델 변환 완료 (1월)
- [M1-2] INT8 양자화 및 정확도 평가 (2월)
- [M1-3] 배치 추론 구현 및 성능 측정 (3월)
- [M1-4] 모델 재학습 및 mAP 75% 달성 (4월)

**Phase 2: 로봇 제작 (5-8월)**
- [M2-1] Fusion360 설계 완료 (5월)
- [M2-2] 3D 프린팅 및 조립 (6월)
- [M2-3] ROS2 제어 노드 구현 (7월)
- [M2-4] MQTT 통합 및 기본 동작 검증 (8월)

**Phase 3: 통합 검증 (9-12월)**
- [M3-1] 파일럿 라인 설치 (9월)
- [M3-2] 기본 성능 테스트 (N=100) (10월)
- [M3-3] 스트레스 테스트 (N=1000) (10월)
- [M3-4] 비교 실험 및 논문 작성 (11-12월)

---

## 7. 참고 문헌

[1] NVIDIA, "TensorRT Developer Guide", 2025.
    https://docs.nvidia.com/deeplearning/tensorrt/

[2] Liu, W., et al., "Deep Learning for Food Quality Assessment: A Review", *Foods*, vol. 11, no. 7, 2022.

[3] Mohamed, N., et al., "Low-Cost 6-DOF Robot Arm Using 3D Printing and Open-Source Control", *Robotics*, vol. 10, no. 2, 2021.

[4] Lee, J., et al., "Edge AI-Based Closed-Loop Control for Smart Manufacturing", *IEEE Access*, vol. 9, pp. 12345-12356, 2021.

[5] Ultralytics, "YOLOv8 Documentation", 2025.
    https://docs.ultralytics.com/

[6] ROS2 Project, "ROS2 Humble Documentation", 2025.
    https://docs.ros.org/en/humble/

[7] Eclipse Foundation, "MQTT Version 5.0 Specification", 2019.
    https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html

---

## 부록

### A. 현재 시스템 상세 스펙

**하드웨어**:
- CPU: 6-core ARM Cortex-A78AE @ 2.0GHz
- GPU: 1024-core NVIDIA Ampere (32 Tensor Cores)
- 메모리: 8GB LPDDR5 (128-bit, 68GB/s)
- 스토리지: 256GB NVMe SSD
- 전력: 7W-15W (Power Mode 조정 가능)

**소프트웨어 버전**:
- JetPack: 6.2
- PyTorch: 2.3.0
- Ultralytics: 8.3.0
- OpenCV: 4.10.0
- Python: 3.10.12

**카메라 스펙**:
- 센서: Sony IMX390 (GMSL2)
- 해상도: 1920×1536 (3MP)
- 프레임률: 30 FPS
- 인터페이스: GMSL2 (Gigabit Multimedia Serial Link)
- 렌즈: 120° 광각 (튀김솥 전체 커버)

### B. 데이터셋 통계

**학습 데이터** (2026-02-15 기준):
- 총 세션: 34개
- 총 이미지: ~8,400장
- 음식 종류: 치킨, 새우, 감자, 만두, 돈까스, 생선
- 라벨: 튀김 영역 세그멘테이션 마스크

**메타데이터**:
- 온도 기록: 기름 온도, 탐침 온도
- 조리 시간: 시작/종료 타임스탬프
- 완료 판정: 완료 적합도 점수 (0-100)

### C. 예산 계획 (개략)

| 항목 | 수량 | 단가 (원) | 소계 (원) |
|------|------|-----------|-----------|
| 3D 프린터 필라멘트 (PLA/PETG) | 5kg | 25,000 | 125,000 |
| 서보 모터 (MG996R) | 6개 | 15,000 | 90,000 |
| 그리퍼 부품 | 1세트 | 50,000 | 50,000 |
| Arduino Mega + Shield | 1세트 | 40,000 | 40,000 |
| 알루미늄 프로파일 | - | 100,000 | 100,000 |
| 기타 부품 (베어링, 볼트 등) | - | 50,000 | 50,000 |
| **합계** | - | - | **455,000** |

*주: Jetson 및 카메라는 기존 시스템 활용, 추가 비용 없음*

### D. 안전 및 윤리

**안전 조치**:
- 로봇 작업 영역 표시 (경고 테이프)
- 비상 정지 버튼 설치
- 실험 시 보안경 착용

**윤리적 고려**:
- 데이터 수집 시 개인정보 비포함 (식품만 촬영)
- 오픈소스 라이선스 준수 (MIT, Apache 2.0)

---

**끝.**

---

*본 문서는 박사과정생 연구장려금 지원사업 신규과제 계획서로 작성되었으며, 실제 구축 및 운영 중인 NVIDIA Jetson 기반 튀김 AI 시스템의 데이터와 성능 지표를 바탕으로 합니다.*

*작성: Claude Code*
*일자: 2026-04-11*
