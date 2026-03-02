"""Simple demo entrypoint for Aegis-Atlas."""

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Aegis-Atlas demo")
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        required=True,
        help="Bounding box coordinates for the demo run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Running demo with bbox={args.bbox}")


if __name__ == "__main__":
    main()
