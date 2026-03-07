# Aegis Atlas

Aegis Atlas is an autonomous Earth-intelligence agent that turns satellite data, hazard feeds, and geopolitical context into customer-ready risk decisions. It helps users move from "something may be happening" to "what should I do next?" through an interactive map, explainable AI outputs, watchlists, alerts, and exportable briefs.

The platform is designed for both professional operators and personal users. A logistics team can watch strategic corridors, an insurer can monitor severity and exposure, a security team can track escalation, and a family can keep a watchlist of loved ones and receive alerts when a location becomes high risk.

## What It Does

| Capability | What the user gets | Why it matters |
| --- | --- | --- |
| AOI risk scan | A threat score, confidence, rationale, and recommended action for any selected area | Converts raw geospatial data into a decision-ready output |
| Satellite + feed fusion | Sentinel-2 scene comparison, hazard adapters, and contextual risk signals | Improves trust over single-source alerting |
| Customer lenses | Logistics, Energy, Insurance, Humanitarian, Security, and General views | Reframes the same operating picture for different buyers and use cases |
| Interactive operating picture | A map-first dashboard with threat overlays, incidents, watchlists, and bulletins | Keeps analysis spatial, fast, and intuitive |
| Watchlists | Multi-location monitoring for assets, sites, routes, or family members | Turns one-off scans into repeat monitoring workflows |
| Alerts and exports | Email and SMS alerting, plus HTML export briefs | Makes the product operational, not just analytical |
| History and incidents | Persistent scan history, rescan support, and incident queueing | Supports trend analysis and operational follow-through |

## Who It Is For

- Enterprise security and resilience teams that need escalation, continuity, and protective-posture insight.
- Logistics and supply-chain operators that need route and chokepoint awareness.
- Insurance and risk teams that need severity framing and exposure monitoring.
- Humanitarian and response teams that need access, urgency, and instability context.
- Families or individuals who want to monitor places connected to loved ones and receive clear alerts.

## Product Walkthrough

### Core user flow

1. Select a location on the map or enter coordinates manually.
2. Choose an AOI radius, operating mode, risk profile, and customer lens.
3. Run `Analyze Risk`.
4. Review the `Scan Brief`, AI guidance, and supporting metrics.
5. Optionally create a watchlist, scan it, and save alert delivery settings.
6. Use `Bulletins`, `Analytics`, `Incidents`, and `History` to monitor movement over time.

### Dashboard user manual

#### 1. Control Panel

The left rail is the primary command surface for the product.

| Control | Purpose |
| --- | --- |
| `Latitude / Longitude` | Set the center point of the area of interest |
| `AOI Radius (km)` | Expand or tighten the analysis zone |
| `Mode` | Use `sample` for deterministic demos or `live` for live retrieval |
| `Start Date / End Date` | Define the observation window |
| `Risk Profile` | Tune sensitivity and thresholds |
| `Customer Lens` | Reframe outputs for the intended end user |
| `Deep live imagery` | Force heavier imagery comparison instead of the fast live path |
| `Analyze Risk` | Run the main analysis workflow |
| `Use Location` | Pull the browser location and stage it on the map |

#### 2. Interactive Map

The map is the main product surface. It is not decorative. It is where the operator sees the fused operating picture.

- Threat fields visualize modeled risk intensity.
- Pins show hotspots, incidents, and watchlist locations.
- The threat legend shows the meaning of the active threat colors.
- Clicking the map stages a new analysis location.
- Zoom and panning allow the same product to work for neighborhood, corridor, and regional views.

#### 3. Scan Brief

The `Scan Brief` tab is the fastest path from data to action.

It includes:

- Threat level
- Confidence
- Score
- Last update time
- Decision priority
- AI insight block with practical protective guidance
- Supporting context such as analysis mode, AOI size, dominant signal, quality band, and active lens

#### 4. Bulletins

The `Bulletins` tab provides a compact feed of recent operational items.

- Incident and hotspot bulletins are surfaced directly from the operating picture.
- Headline corroboration and live-news style context are blended into the same feed.
- Bulletin cards can be used to focus the map back onto the relevant location.

#### 5. Analytics

The `Analytics` tab provides fast visual interpretation instead of raw logs.

Sub-tabs include:

- `Trend`
- `Signals`
- `Health`
- `Instability`
- `Feed`
- `Watchlist`

These help the user answer questions such as:

- Is the threat moving up or down?
- Which signal is driving the score?
- How trustworthy is the evidence?
- How active is the bulletin stream?
- Which watchlist members are diverging from the rest?

#### 6. Watchlists

The `Watchlists` tab supports continuous monitoring across multiple places.

Use cases include:

- Family members in different cities or countries
- Offices, depots, and sites
- Maritime or logistics nodes
- Critical infrastructure assets

Watchlists have three internal sub-tabs:

| Watchlist tab | Purpose |
| --- | --- |
| `Overview` | Create/edit a watchlist and review summary posture |
| `Alerts` | Configure email and SMS delivery |
| `Results` | Review prioritized outputs from the latest scan |

Alerting behavior:

- Email alerts can include a richer export digest with analytics, top movements, and bulletin context.
- SMS alerts are designed for short escalation notifications when any member becomes `high` or `critical`.

#### 7. Incidents and History

- `Incidents` turns important scans into a queue the operator can revisit, rescan, and close.
- `History` stores prior analyses and watchlist scans so the platform can provide trend-aware outputs.

## Architecture

Aegis Atlas is structured as a lightweight intelligence application with a Python analysis backend and a browser-based operating picture.

### System view

```text
                         +----------------------+
                         |   Browser Frontend   |
                         |  Map + Dashboard UI  |
                         +----------+-----------+
                                    |
                                    | HTTP / JSON
                                    v
                      +-------------+--------------+
                      |        Flask Web App       |
                      |  routing, briefs, history  |
                      +------+------+------+-------+
                             |      |      |
                             |      |      |
                  +----------+      |      +-------------------+
                  |                 |                          |
                  v                 v                          v
        +----------------+  +---------------+        +------------------+
        | Analysis Agent |  | Persistence   |        | Notifications    |
        | risk scoring,  |  | history,      |        | email, SMS,      |
        | explainability |  | watchlists,   |        | webhook delivery |
        +--------+-------+  | incidents     |        +------------------+
                 |          +---------------+
                 |
                 v
   +-------------+------------------------------------------------------+
   | External intelligence inputs                                       |
   | Sentinel-2 / STAC, hazard feeds, travel advisories, headlines,     |
   | regional conflict context, synthetic demo fallbacks                |
   +--------------------------------------------------------------------+
```

### Analysis pipeline

```text
User AOI
  |
  v
Parse query -> Build bbox -> Retrieve scenes / feeds -> Score signals
  |
  v
Fuse weighted signals -> Apply risk profile + customer lens
  |
  v
Generate:
  - threat level
  - score
  - confidence
  - explainability
  - AI brief
  - recommended action
```

### Frontend architecture

```text
index.html
  |
  +-- Control Panel
  +-- Map Shell
  +-- Threat Legend
  +-- Bottom Dock
        |
        +-- Scan Brief
        +-- Bulletins
        +-- Analytics
        +-- Watchlists
        +-- Incidents
```

### Backend modules

| File | Responsibility |
| --- | --- |
| `webapp.py` | Flask app, API routes, dashboard orchestration, brief/export generation |
| `agent_skeleton.py` | Core analysis pipeline and risk scoring logic |
| `analyze.py` | Scene-pair and sample TIFF image analysis |
| `stac_fetcher.py` | Sentinel-2 discovery and scene selection |
| `risk_intel.py` | Contextual risk signals such as travel, conflict, and geopolitical context |
| `lens_profiles.py` | Customer-lens configuration and scoring emphasis |
| `trend_intel.py` | Trend summaries for scans and watchlists |
| `watchlists.py` | Watchlist persistence |
| `incident_store.py` | Incident queue persistence |
| `history_store.py` | Scan history persistence |
| `notifications.py` | Email, SMS, and webhook notification hooks |
| `static/app.js` | Frontend behavior, map layers, dock state, and rendering |
| `static/style.css` | Dashboard visual system and responsive layout |
| `templates/*.html` | Dashboard and export templates |

## Repository Structure

```text
Aegis-Atlas/
|-- webapp.py
|-- agent_skeleton.py
|-- analyze.py
|-- stac_fetcher.py
|-- risk_intel.py
|-- lens_profiles.py
|-- trend_intel.py
|-- watchlists.py
|-- incident_store.py
|-- history_store.py
|-- notifications.py
|-- static/
|   |-- app.js
|   `-- style.css
|-- templates/
|   |-- index.html
|   |-- analysis_brief.html
|   `-- watchlist_brief.html
|-- demo/
|   |-- run_demo.py
|   |-- run_scenarios.py
|   `-- DEMO_RUNBOOK.md
`-- tests/
```

## How To Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the web application

```bash
python3 webapp.py
```

Then open:

```text
http://127.0.0.1:8000
```

### 3. Run the demo CLI

```bash
python3 demo/run_demo.py --bbox "-122.65,38.20,-122.10,38.65" --start-date 2024-08-01 --end-date 2024-08-31
```

### 4. Run scripted scenarios

```bash
python3 demo/run_scenarios.py
```

### 5. Run tests

```bash
python3 -m pytest tests -q
```

### 6. Run in Docker

```bash
docker build -t aegis-atlas:demo .
docker run --rm -p 8000:8000 aegis-atlas:demo
```

## Operating Modes

| Mode | Best for | Behavior |
| --- | --- | --- |
| `sample` | Safe demos, deterministic fallback, quick validation | Uses local/sample analysis paths |
| `live` | Real operating picture and current retrieval | Uses live adapters and fast live defaults |
| `deep_live=true` | Higher-fidelity live inspection | Forces heavier imagery analysis instead of the fast live path |

## API Summary

### Primary endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/analyze` | Run a single-location analysis |
| `GET` | `/api/feed/bulletins` | Get the current bulletin feed |
| `GET` | `/api/history` | Retrieve recent scans |
| `GET` | `/api/watchlists` | List watchlists |
| `POST` | `/api/watchlists` | Create a watchlist |
| `PUT` | `/api/watchlists/<id>/alerts` | Save watchlist alert preferences |
| `POST` | `/api/watchlists/<id>/scan` | Scan all members in a watchlist |
| `DELETE` | `/api/watchlists/<id>` | Remove a watchlist |
| `GET` | `/api/incidents` | List incidents |
| `POST` | `/api/incidents` | Create/update an incident from a scan |

### Example: analyze a location

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 37.7749,
    "lon": -122.4194,
    "radius_km": 25,
    "mode": "live",
    "risk_profile": "balanced",
    "lens": "general"
  }'
```

## Configuration

### Notification environment variables

| Variable | Purpose |
| --- | --- |
| `AEGIS_SMTP_HOST` | SMTP server hostname |
| `AEGIS_SMTP_PORT` | SMTP port, default `587` |
| `AEGIS_SMTP_USER` | SMTP username |
| `AEGIS_SMTP_PASSWORD` | SMTP password |
| `AEGIS_SMTP_SENDER` | Sender address for email alerts |
| `AEGIS_SMS_WEBHOOK_URL` | Webhook target for SMS delivery integration |
| `AEGIS_LIVE_FAST_MODE` | `1` by default; disables deep analysis unless explicitly requested |
| `AEGIS_PIPELINE_TIMEOUT_SECONDS` | Max analysis runtime before timeout |

## Why The Product Is Strong

Aegis Atlas is valuable because it is not just a detector, not just a map, and not just a report generator. It is a workflow product.

- It detects and contextualizes.
- It explains why a score was produced.
- It adapts to different customer lenses without changing the underlying engine.
- It supports operational follow-through through watchlists, incidents, history, and alerts.
- It works for both business and personal safety use cases.

That combination makes it easier to imagine real customer adoption: not just "interesting intelligence," but a product people would rely on.
