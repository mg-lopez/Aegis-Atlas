import subprocess
import sys


def test_run_demo_help() -> None:
    result = subprocess.run(
        [sys.executable, "demo/run_demo.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--bbox" in result.stdout
