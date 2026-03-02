# Aegis Atlas

## Quickstart

### Run in Colab

Open `getting-started.ipynb` in Google Colab and follow the notebook steps.

### Run demo locally

```bash
pip install -r requirements.txt
python demo/run_demo.py --bbox "-122.65,38.20,-122.10,38.65" --start-date 2024-08-01 --end-date 2024-08-31
```

### Build and run Docker demo

```bash
docker build -t aegis-atlas:demo .
docker run --rm aegis-atlas:demo
```
