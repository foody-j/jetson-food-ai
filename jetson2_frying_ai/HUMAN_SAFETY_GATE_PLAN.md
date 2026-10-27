# Jetson2 Observe Human Safety Gate Plan

## Goal
- Restore cam2/cam3 web preview to full frame (remove ROI crop from preview path).
- Block automatic "투입" when a person is detected around basket danger zones.
- Keep block reasons visible in logs/UI for fast debugging.

## Scope
- Target service: `jetson2_frying_ai/JETSON2_web.py`
- Target web UI: `jetson2_frying_ai/web/templates/dashboard.html`
- Config: `jetson2_frying_ai/config_jetson2_web.json`

## Implementation Plan

### 1) Separate Preview ROI and AI ROI
- Add config switches:
  - `web_use_roi_cam2` (default: `false`)
  - `web_use_roi_cam3` (default: `false`)
  - `observe_use_roi_cam2` (default: `true`)
  - `observe_use_roi_cam3` (default: `true`)
- Web preview should show full frame by default.
- Observe inference can still use ROI for speed/accuracy.

### 2) Add Human Detection Worker
- Add lightweight `HumanSafetyWorker` for cam2/cam3.
- Input: latest full frame from camera worker.
- Output state (per side):
  - `human_detected`
  - `confidence_max`
  - `zone_overlap`
  - `boxes` (optional for debug)
- Run at low FPS (3~5) to control load.

### 3) Danger Zone Definition
- Add zone config:
  - `human_zone_cam2`
  - `human_zone_cam3`
- Zone format: polygon points (recommended).
- Trigger rule:
  - person confidence >= `human_conf_min`
  - overlap with zone >= `human_overlap_min`

### 4) Safety Gate State Machine
- Gate state: `SAFE` / `BLOCKED_HUMAN`
- Enter blocked:
  - detected for `human_block_enter_frames` consecutive frames
- Exit blocked:
  - not detected for `human_block_exit_frames` consecutive frames
  - plus cooldown `human_block_cooldown_sec`

### 5) Integrate with Observe Input Decision
- Current input condition:
  - FILLED + temp threshold + valid recipe + not cleaning
- Add new condition:
  - gate must be `SAFE`
- When blocked:
  - effective observe state should be `BLOCKED_HUMAN` (recommended)

### 6) Logging and Visibility
- Add ops events:
  - `human_block_enter`
  - `human_block_exit`
  - `observe_input_blocked` (reason: human/temp/recipe)
- Add terminal logs for block enter/exit with confidence and overlap.
- Add web status fields:
  - `Human: SAFE/DETECTED`
  - `Input Gate: OPEN/BLOCKED`
  - latest block reason/time

### 6-1) Text-First Operation Policy (Preview is Secondary)
- Do not rely on video preview for decision making.
- Keep preview for reference only; decision authority must come from text status.
- Always expose a single decision line in UI/log:
  - `observe_raw`
  - `observe_effective`
  - `oil_temp`
  - `recipe`
  - `human_gate`
  - `final_decision` (`투입` / `BLOCKED_HUMAN` / etc.)
  - `block_reason` (`human` / `temp` / `recipe` / `cleaning`)
- Require state-change logs in both terminal and `ops_logs` for traceability.
- UI recommendation:
  - Default view = RAW preview + text status panel
  - Overlay view = optional debug mode (manual toggle)

### 7) Stability and Failure Policy
- Human worker must not block camera preview pipeline.
- Define fail-safe policy if detector fails:
  - Option A: temporary UNKNOWN then BLOCKED after timeout
  - Option B: keep SAFE (not recommended for safety)
- Add worker health metric to status API.

### 8) Test Scenarios
- 정상 투입: no person, all input conditions satisfied.
- 차단: person enters zone during FILLED+hot state.
- 해제: person leaves zone, gate reopens after configured exit/cooldown.
- 청소 레시피: must remain blocked from input regardless of person.
- Robustness: partial person visibility, lighting changes, occlusion.
- Long-run: verify no freeze, no worker deadlock, no memory leak.

## Config Draft (to add later)
- `web_use_roi_cam2`: false
- `web_use_roi_cam3`: false
- `observe_use_roi_cam2`: true
- `observe_use_roi_cam3`: true
- `human_conf_min`: 0.4
- `human_overlap_min`: 0.2
- `human_block_enter_frames`: 2
- `human_block_exit_frames`: 5
- `human_block_cooldown_sec`: 1.5
- `human_zone_cam2`: []
- `human_zone_cam3`: []

## Decisions to Confirm Before Coding
1. Block state string: `BLOCKED_HUMAN`
2. Zone definition format: polygon point list
3. Fail-safe policy: detector-down => BLOCKED or SAFE
4. Enter/exit frame counts and cooldown defaults
5. Apply to both cam2 and cam3
