# Aegis-Atlas

## Quickstart

### Run in Google Colab
1. Open `getting-started.ipynb` in Colab.
2. Run the notebook cells in order.

### Run demo locally
```bash
pip install -r requirements.txt
python demo/run_demo.py --bbox -122.6 37.6 -122.3 37.9
```

### Build and run with Docker
```bash
docker build -t aegis-atlas:demo .
docker run --rm aegis-atlas:demo --bbox -122.6 37.6 -122.3 37.9
```
