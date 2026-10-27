# 조리완료 AI 평가 보고서 템플릿

문서 버전: v1.0  
작성일: YYYY-MM-DD  
작성자: ___

---

## 1. 평가 목적

- 본 평가는 "품질 완성도"가 아니라 **운영상 완료 시점(배출 시점) 예측 정확도**를 측정한다.
- 목표는 조리완료 타이밍 판단의 일관성/재현성을 수치로 제시하는 것이다.

---

## 2. 완료 기준 정의

### 2.1 정답 완료시점 (라벨)
- `t_out`: `HR/Status`에서 해당 Pot의 `ProcessType="배출"`이 **처음 발생한 시각**

### 2.2 AI 예측 완료시점
- `t_pred`: AI 완료 조건을 **처음 만족한 시각**
- 완료 조건 예시:
  - `S >= 85`
  - `running_time_ratio >= 0.9`
  - `color_ratio >= 0.8`

---

## 3. 지표 정의

### 3.1 세션별 시간오차
\[
\Delta t_i = |t_{pred,i} - t_{out,i}|
\]

### 3.2 세션별 적합도 점수 (%)
\[
Score_i = \max\left(0,\ 100 \times \left(1-\frac{\Delta t_i}{W}\right)\right)
\]

- `W`: 허용 오차(예: 30초 또는 60초)

### 3.3 전체 적합도 (%)
\[
Final\% = \frac{1}{N}\sum_{i=1}^{N} Score_i
\]

### 3.4 정확도 계열 지표
- `HitRate@W(%) = (Δt_i <= W 인 세션 수 / N) * 100`
- `MAE(초) = 평균(Δt_i)`
- `P90 Error(초) = Δt_i의 90퍼센타일`
- `Early Rate(%) = t_pred < t_out 비율`
- `Late Rate(%) = t_pred > t_out 비율`

---

## 4. 데이터셋 개요

- 기간: ___ ~ ___
- 총 세션 수: `N = ___`
- Pot1 세션: ___
- Pot2 세션: ___
- 제외 세션 수: ___
- 제외 사유:
  - 카메라 프레임 없음
  - 메타 누락
  - 청소 모드

---

## 5. 요약 결과

| 항목 | 값 |
|---|---|
| Final 적합도 (%) | ___ |
| HitRate@30s (%) | ___ |
| HitRate@60s (%) | ___ |
| MAE (초) | ___ |
| P90 Error (초) | ___ |
| Early Rate (%) | ___ |
| Late Rate (%) | ___ |

---

## 6. 세션별 결과 (샘플 10건)

| Session ID | Pot | Food | t_out | t_pred | Δt(초) | Score(%) | 비고 |
|---|---|---|---|---|---:|---:|---|
| session_xxx | pot1 | ___ | ___ | ___ | ___ | ___ | ___ |
| session_xxx | pot2 | ___ | ___ | ___ | ___ | ___ | ___ |

---

## 7. 판단 근거(설명 지표)

완료 시점 근처(예: t_pred ± 10초)에서 아래 지표를 제시:

- `running_time`
- `target_time`
- `color_delta`
- `brown_ratio`
- `golden_ratio`
- `lift_count`

예시 문장:
- "Session `___`의 완료 예측 시점에서 color_delta=__, lift_count=__, running_time=__s로 완료 조건을 만족했다."

---

## 8. 해석

- 본 모델은 "배출 시점 예측" 기준에서 Final 적합도 `___%`를 달성했다.
- 오차 분포상 지연(또는 조기) 경향이 `___`로 확인되었다.
- 운영 적용 시 `W=___초` 기준 HitRate는 `___%`이다.

---

## 9. 한계

- 현재 라벨은 메뉴별 품질 완료가 아닌 운영 완료(배출) 기준이다.
- 메뉴별 최적 완료 상태(품질 라벨) 데이터가 부족하다.
- 일부 세션은 카메라 프레임 결측으로 평가 제외됨.

---

## 10. 다음 단계

1. 메뉴별 품질 라벨 데이터 수집 (샘플 ___건/메뉴)
2. 품질 완료 기준과 운영 완료 기준 분리 평가
3. 임계값(`S`, `W`) 재튜닝 및 배포 기준 수립

---

## 부록 A. 운영용 점수 정의(선택)

\[
S = 100 \times (w_t T + w_c C + w_l L + w_p P)
\]

- \(T = \min(running\_time/target\_time, 1)\)
- \(C = \min(color\_delta/color\_threshold, 1)\)
- \(L = \min(lift\_count/expected\_lift, 1)\)
- \(P = \min(probe\_temp/target\_temp, 1)\)

권장 초기 가중치:
- \(w_t=0.35,\ w_c=0.35,\ w_l=0.20,\ w_p=0.10\)

