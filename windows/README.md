# Windows Toolkit (색변화 분석 + 리프트 점검)

`windows/` 폴더는 현장/개발 윈도우 PC에서 `AI_Data`만 넣고 분석할 수 있게 분리한 도구입니다.

## 포함 기능
- `색변화 분석 실행`
  - `*_lift_events.json`이 없는 세션은 프레임 기반 fallback으로 자동 재생성 후 분석
  - `lift_event_trends/lift_event_trends.csv`
  - `lift_event_trends/lift_event_session_summary.csv`
  - `plots/session_flows_with_thumbs/*.png` (세션 흐름 + 썸네일)
  - `completion_suitability_*.csv`
- `리프트 점검 실행`
  - `*_lift_events.json`이 없는 세션은 프레임 기반 fallback으로 자동 재생성 후 점검
  - `lift_audit_summary.csv`
  - `lift_audit_issues.csv`

## 파일
- `app.py`: GUI
- `frying_toolkit.py`: 분석 코어/CLI
- `build_exe.bat`: exe 빌드
- `requirements.txt`: 의존성

## 윈도우에서 exe 만들기
1. `windows` 폴더에서 `build_exe.bat` 더블클릭
2. 완료 후 `windows/dist/FryingDataAnalyzer.exe` 실행

## Python으로 바로 실행
```bat
cd windows
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## CLI (선택)
```bat
python frying_toolkit.py analyze --base-dir D:\AI_Data --out-dir D:\reports
python frying_toolkit.py lift-audit --base-dir D:\AI_Data --out-dir D:\reports
```

## 데이터 구조 가정
- `AI_Data/pot1/session_*/<food>/*_lift_events.json`
- `AI_Data/pot2/session_*/<food>/*_lift_events.json`
- 프레임은 pot1=`camera_0`, pot2=`camera_1` 기준으로 매칭

## 참고
- fallback 재생성(`source=frame_fallback_simple`)은 기존 실시간 추론 결과와 100% 동일하지 않습니다.
- 목적은 누락 세션을 분석에서 제외하지 않기 위한 보완입니다.
