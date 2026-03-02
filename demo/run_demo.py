"""Demo script to execute a single Watch -> Navigate -> Analyze -> Deliver run."""

from __future__ import annotations

import json
from dataclasses import asdict

from agent_skeleton import AegisAtlasAgent


def main() -> None:
    """Run demo pipeline for a sample California bbox and print alert JSON."""

    sample_bbox = [-122.65, 38.20, -122.10, 38.65]
    agent = AegisAtlasAgent()

    signal = agent.watch(sample_bbox, hazard_type="wildfire")
    scenes = agent.navigate(signal, start_date="2024-08-01", end_date="2024-08-31", max_cloud=25.0)
    analysis = agent.analyze(scenes)
    payload = agent.deliver(signal, scenes, analysis)

    print(json.dumps(asdict(payload), indent=2))


if __name__ == "__main__":
    main()
