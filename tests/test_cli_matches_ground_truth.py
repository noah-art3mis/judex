import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

IGNORED_KEYS = {"extraido", "html"}


def _assert_json_equal(expected, actual, path: str = "") -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(k for k in expected.keys() if k not in IGNORED_KEYS)
        actual_keys = set(actual.keys())
        missing_keys = expected_keys - actual_keys

        assert not missing_keys, f"Missing keys at '{path}': {sorted(missing_keys)}"

        for key in sorted(expected_keys):
            next_path = f"{path}.{key}" if path else key
            _assert_json_equal(expected[key], actual[key], next_path)
        return

    if isinstance(expected, list) and isinstance(actual, list):
        assert len(expected) == len(
            actual
        ), f"List length mismatch at '{path}': {len(expected)} != {len(actual)}"

        for index, (exp_item, act_item) in enumerate(zip(expected, actual)):
            _assert_json_equal(exp_item, act_item, f"{path}[{index}]")
        return

    assert (
        expected == actual
    ), f"Value mismatch at '{path}': expected {expected!r}, got {actual!r}"


@pytest.mark.e2e
@pytest.mark.parametrize(
    "classe, processo, ground_truth_filename",
    [
        ("AI", 772309, "tests/ground_truth/AI_772309.json"),
        ("MI", 12, "tests/ground_truth/MI_12.json"),
        ("RE", 1234567, "tests/ground_truth/RE_1234567.json"),
    ],
)
def test_cli_output_matches_ground_truth(classe, processo, ground_truth_filename):
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / f"{classe}_{processo}.json"

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
            "--output-path",
            tmpdir,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=180,
        )
        assert (
            result.returncode == 0
        ), f"CLI failed: {result.stderr}\nSTDOUT:\n{result.stdout}"

        # Load actual and expected JSON
        assert out_path.exists(), f"Expected output file {out_path} not found"
        with open(out_path, "r", encoding="utf-8") as f:
            actual = json.load(f)

        with open(ground_truth_filename, "r", encoding="utf-8") as f:
            expected = json.load(f)

        # Deep, recursive structural equality with clear diffs
        _assert_json_equal(expected, actual)
