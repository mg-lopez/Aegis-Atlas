# Aegis Atlas (prototype)

Bootstrap for a Watch → Navigate → Analyze → Deliver hazard-intelligence agent.

## What this PR includes

- `agent_skeleton.py`: minimal end-to-end pipeline with CLI.
- `stac_fetcher.py`: Sentinel-2 L2A discovery from Microsoft Planetary Computer STAC.
- `analyze.py`: simple cloud-mask helper + band-difference change detection.
- `demo/run_demo.py`: single-run demonstration for a sample bbox.
- `tests/test_stac_fetcher.py`: unit tests with mocked STAC client.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python demo/run_demo.py --bbox "-122.65,38.20,-122.10,38.65" --start-date 2024-08-01 --end-date 2024-08-31
```

## Run tests

```bash
pytest -q
```

## Run in Docker

```bash
docker build -t aegis-atlas .
docker run --rm aegis-atlas
```

## Run in Google Colab (starter)

1. Upload project files to Colab runtime (or mount Drive).
2. Install dependencies:

   ```python
   !pip install -r requirements.txt
   ```

3. Run demo:

   ```python
   !python demo/run_demo.py --bbox "-122.65,38.20,-122.10,38.65" --start-date 2024-08-01 --end-date 2024-08-31
   ```

The demo writes the latest alert payload to `demo/last_alert.json` for quick inspection.

## Environment variables

Do not hardcode secrets. Use environment variables when credentials are required:

- `OPENAI_API_KEY`
- `PLANETARY_COMPUTER_CLIENT_ID`
- `TWILIO_SID`
- `TWILIO_TOKEN`
