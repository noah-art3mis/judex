import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.e2e
@pytest.mark.parametrize(
    "classe, processo, output_filename, ground_truth_filename",
    [
        ("AI", 772309, "judex_output/AI_772309.json", "tests/ground_truth/AI_772309.json"),
        # add more pairs as needed
    ],
)
def test_cli_output_matches_ground_truth(classe, processo, output_filename, ground_truth_filename):
    # Ensure no stale output
    out_path = Path(output_filename)
    if out_path.exists():
        out_path.unlink()

    # Run the CLI using uv (as you requested)
    cmd = [
        "uv",
        "run",
        "judex",
        "scrape",
        "-c",
        classe,
        "-p",
        str(processo),
        "-s",
        "json",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        timeout=180,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}\nSTDOUT:\n{result.stdout}"

    # Load actual and expected JSON
    assert out_path.exists(), f"Expected output file {out_path} not found"
    with open(out_path, "r", encoding="utf-8") as f:
        actual = json.load(f)

    with open(ground_truth_filename, "r", encoding="utf-8") as f:
        expected = json.load(f)

    # Exact structural equality
    assert actual == expected, (
        "CLI output does not match ground truth.\n"
        f"Output:   {out_path}\n"
        f"Expected: {ground_truth_filename}\n"
    )