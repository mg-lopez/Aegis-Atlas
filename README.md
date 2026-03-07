# Aegis Atlas

## Quickstart

### Run in Colab

Open `getting-started.ipynb` in Google Colab and follow the notebook steps.

### Run demo locally

```bash
pip install -r requirements.txt
python3 demo/run_demo.py --bbox "-122.65,38.20,-122.10,38.65" --start-date 2024-08-01 --end-date 2024-08-31
```

### Run web dashboard

```bash
python3 webapp.py
```

Then open `http://localhost:8000`.

### Run scripted demo scenarios (Phase 4)

```bash
python3 demo/run_scenarios.py
```

This generates backup presentation snapshots under `demo/snapshots/` and a fusion report under `demo/debug/scenario_fusion_report.json`.

See `demo/DEMO_RUNBOOK.md` for the 3-minute demo flow and fallback procedure.

### Phase 5 API (notifications, watchlists, history)

- `POST /api/analyze` supports optional notification config:
  - `notify.webhook_url`
  - `notify.email_to`
- `GET /api/history?limit=20` returns recent persisted analyses/scans.
- `GET /api/watchlists` lists watchlists.
- `POST /api/watchlists` creates a multi-location watchlist:
  - body: `{ "name": "...", "members": [{ "label": "...", "lat": ..., "lon": ... }] }`
- `POST /api/watchlists/<watchlist_id>/scan` runs alerts for each member and stores results in history.

Live mode behavior:
- By default, `mode=live` uses fast STAC metadata scoring to keep interactive requests responsive.
- Set `deep_live=true` in request payload to force full imagery analysis.
- Env override: `AEGIS_LIVE_FAST_MODE=0` disables fast-live default.

Email notifications use SMTP env vars:
- `AEGIS_SMTP_HOST`
- `AEGIS_SMTP_PORT` (default `587`)
- `AEGIS_SMTP_USER`
- `AEGIS_SMTP_PASSWORD`
- `AEGIS_SMTP_SENDER`

### Build and run Docker demo

```bash
docker build -t aegis-atlas:demo .
docker run --rm aegis-atlas:demo
```
