# Jetson Food AI - 운영 보고서 가이드

## 📚 문서 개요

본 프로젝트는 NVIDIA Jetson Orin Nano 기반 **식당 자동화 모니터링 시스템**입니다.
AI 기반 사람 감지, 튀김 상태 분석, 바켓 감지를 통해 로봇 PC를 자동 제어합니다.

---

## 📁 문서 구조

### 1. **상세 운영 보고서** (메인 문서)
📄 **파일**: `OPERATIONS_REPORT_AI_FEATURES_DETAILED.md` (~1,000줄)

**내용**:
- ✅ 시스템 아키텍처 (하드웨어/소프트웨어)
- ✅ Jetson #1 구현 기능 60개 (사람 감지, 야간 감시, 릴레이 제어 등)
- ✅ Jetson #2 구현 기능 75개 (튀김 AI, 바켓 감지, DISCHARGE 판정 등)
- ✅ MQTT 통신 프로토콜 (12개 토픽, 메시지 포맷)
- ✅ 데이터 저장 구조 (5종류 데이터, session_info.json)
- ✅ 설정 파라미터 상세 (35개+ 파라미터, 조정 가이드)
- ✅ 성능 최적화 (FPS, GPU, 프레임 스킵 전략)
- ✅ 트러블슈팅 가이드 (8개 주요 문제 해결법)

**특징**:
- 실제 코드 분석 기반 (4,000줄 × 2개 파일)
- 모든 메서드/기능 문서화
- 설정 파라미터 조정 가이드 포함
- 운영 체크리스트 (일일/주간/월간)

---

### 2. **시스템 다이어그램 모음** (시각 자료)
📊 **파일**: `SYSTEM_DIAGRAMS.md`

**포함된 9개 다이어그램**:

| # | 다이어그램 | 타입 | 설명 |
|---|-----------|------|------|
| 1 | **전체 시스템 아키텍처** | Flowchart | Jetson #1/#2, MQTT, 릴레이, 로봇 PC 연결 구조 |
| 2 | **MQTT 통신 플로우** | Sequence | 사람 감지 → 릴레이 ON → 튀김 → DISCHARGE 전체 플로우 |
| 3 | **주야간 상태 머신** | State Diagram | 주간 모드 ↔ 야간 모드 전환 로직 |
| 4 | **튀김 AI 파이프라인** | Flowchart | YOLO → Lift Tracking → DISCHARGE 판정 |
| 5 | **데이터 저장 구조** | Flowchart | 5종류 데이터 저장 디렉토리 구조 |
| 6 | **릴레이 제어 시퀀스** | Sequence | 24V Omron 자기유지 릴레이 ON/OFF |
| 7 | **진동센서 측정 플로우** | Flowchart | Modbus RTU 측정 → NORMAL/ABNORMAL 판정 |
| 8 | **성능 최적화 구조** | Flowchart | 프레임 스킵, 워커 스레드 구조 |
| 9 | **데이터 수집 스케줄** | Gantt | 평일 08:30~12:00 자동 수집 |

**기술**: Mermaid 다이어그램 (GitHub/GitLab 자동 렌더링)

---

### 3. **간단 요약본** (개요)
📄 **파일**: `OPERATIONS_REPORT_AI_FEATURES.md` (~200줄)

**내용**:
- 시스템 개요
- 주요 기능 요약
- 설정 파일 설명
- 주요 파일 목록

**용도**: 빠른 참조용

---

## 🎯 과제 제출 시 읽는 순서

### 추천 순서:

1. **📄 OPERATIONS_REPORT_AI_FEATURES_DETAILED.md** (메인 문서)
   - 전체 시스템 이해
   - 구현된 기능 확인
   - 설정 파라미터 확인

2. **📊 SYSTEM_DIAGRAMS.md** (다이어그램)
   - 시각적으로 시스템 구조 파악
   - 특히 "섹션 1, 2, 4" 중요

3. **📄 OPERATIONS_REPORT_AI_FEATURES.md** (요약본)
   - 빠른 참조용

---

## 🖼️ 다이어그램 보는 방법

### GitHub에서 보기 (권장)
```bash
# GitHub에 푸시
git add docs/
git commit -m "Add operation reports with diagrams"
git push

# GitHub 웹에서 SYSTEM_DIAGRAMS.md 열기
# → Mermaid 자동 렌더링 ✅
```

### VS Code에서 보기
```bash
# Markdown Preview Enhanced 확장 설치
code --install-extension shd101wyy.markdown-preview-enhanced

# 파일 열고 우클릭 → "Markdown Preview Enhanced: Open Preview"
```

### 온라인 편집기에서 보기
1. https://mermaid.live/ 접속
2. 다이어그램 코드 복사-붙여넣기
3. 실시간 렌더링 확인

### PNG로 변환 (발표용)
```bash
# Mermaid CLI 설치
npm install -g @mermaid-js/mermaid-cli

# 이미지 변환
mmdc -i docs/SYSTEM_DIAGRAMS.md -o diagrams.png
```

---

## 📊 핵심 통계

| 항목 | 수치 |
|------|------|
| **총 문서 분량** | ~1,200줄 |
| **다이어그램 수** | 9개 + 본문 삽입 1개 |
| **구현 기능** | Jetson #1: 60개<br/>Jetson #2: 75개 |
| **MQTT 토픽** | 12개 |
| **설정 파라미터** | 35개+ |
| **코드 예시** | 20개+ |
| **트러블슈팅** | 8개 |

---

## 💡 주요 강조 포인트 (과제용)

### 1. **실제 구현 완료**
- 코드 4,000줄 × 2개 파일 분석
- 모든 메서드 문서화
- 실제 운영 중인 시스템

### 2. **다양한 AI 기술**
- YOLO 사람 감지 (GPU 가속)
- YOLOv8-seg 튀김 분석 (v3 모델, mAP 67.8%)
- Lift Tracking 알고리즘 (탈탈 이벤트 추적)
- MOG2 모션 감지 (야간 스냅샷)

### 3. **시스템 통합**
- MQTT 통신 (QoS 1 보장)
- GPIO 릴레이 제어 (24V Omron 자기유지형)
- 진동센서 통합 (Modbus RTU)
- 4-카메라 동시 처리

### 4. **성능 최적화**
- 프레임 스킵 전략 (AI 2fps, GUI 10fps)
- 워커 스레드 분리 (메인/카메라/추론/저장)
- 비동기 파일 저장
- GPU 사용률 30~50%

### 5. **운영 자동화**
- 주야간 자동 전환 (04:00~21:00)
- 사람 감지 → 릴레이 자동 ON
- 야간 미감지 → 릴레이 자동 OFF
- 평일 데이터 자동 수집 (08:30~12:00)

---

## 🔧 추가 참고 문서

### 프로젝트 루트 문서
- `CLAUDE.md`: 프로젝트 전체 가이드
- `배포가이드.md`: 설치 및 배포
- `jetson1_monitoring/JETSON1_GUIDE.md`: Jetson #1 상세 가이드

### 설정 파일
- `jetson1_monitoring/config.json`: Jetson #1 설정
- `jetson2_frying_ai/config_jetson2.json`: Jetson #2 설정
- `vibration_config.json`: 진동센서 임계값

---

## 📞 문의

**프로젝트**: Jetson Food AI
**작성일**: 2026-02-02
**버전**: 2.0 (상세 확장판)

---

## ✨ 과제 제출 Tip

### 발표 시 강조할 부분:
1. **다이어그램 1, 2, 4번** 먼저 보여주기
   - 전체 시스템 아키텍처
   - MQTT 통신 플로우
   - 튀김 AI 파이프라인

2. **실제 동작 영상** (있다면)
   - 사람 감지 → 릴레이 ON
   - 튀김 AI → DISCHARGE 판정
   - 야간 스냅샷 저장

3. **성능 지표** 강조
   - GPU 사용률 30~50%
   - 실시간 처리 (30fps 입력)
   - 데이터 저장 (~800KB/장)

4. **운영 자동화** 강조
   - 24시간 무인 운영
   - 주야간 자동 전환
   - 자동 데이터 수집

### 보고서 인쇄 시:
- **A4 기준 약 50페이지**
- 다이어그램은 PNG로 변환해서 삽입 권장
- 목차 활용 (섹션별 페이지 번호)

---

**Good Luck! 🚀**
