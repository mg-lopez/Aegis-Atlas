# Aegis Atlas 3-Minute Demo Runbook

## Goal
Show low/medium/high risk outputs with explainable multi-source fusion, then show live map interaction.

## Pre-Demo Prep (2-3 minutes before presenting)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Generate deterministic scenario snapshots:
   ```bash
   python3 demo/run_scenarios.py
   ```
3. Start the dashboard:
   ```bash
   python3 webapp.py
   ```
4. Open `http://localhost:8000`.

## 3-Minute Live Flow
1. **0:00-0:40** - "What this does"
   - Explain that Aegis Atlas fuses Sentinel-2 change detection with hazard feeds.
   - Mention outputs: threat level, confidence, and explainability.
2. **0:40-1:40** - Scripted scenarios
   - Open `demo/snapshots/low.json`, `medium.json`, `high.json`.
   - Point out the threat level progression and rationale entries.
3. **1:40-2:40** - Dashboard interaction
   - Click a map location and run `Sample (Reliable Demo)` mode.
   - Show "Why This Alert" and "Signal Breakdown" sections.
4. **2:40-3:00** - Close
   - Summarize: multi-source fusion + explainability + reproducible backup artifacts.

## Fallback Flow (if live demo degrades)
1. If network/STAC calls are slow, keep mode on `Sample (Reliable Demo)`.
2. If browser UI has issues, present `demo/snapshots/summary.json` and per-scenario JSON files.
3. If API fails entirely, run:
   ```bash
   python3 demo/run_scenarios.py
   ```
   Then present the generated snapshots from `demo/snapshots/`.

## Backup Artifacts
- `demo/snapshots/low.json`
- `demo/snapshots/medium.json`
- `demo/snapshots/high.json`
- `demo/snapshots/summary.json`
- `demo/debug/scenario_fusion_report.json`
