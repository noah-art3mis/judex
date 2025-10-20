#!/usr/bin/env python3
"""
Script to test if all fields from ground truth JSON are present in the HTML field
of the AI output JSON.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set


def extract_text_from_html(html_content: str) -> str:
    """Extract text content from HTML, removing tags and normalizing whitespace."""
    if not html_content:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html_content)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove extra spaces
    text = text.strip()
    return text


def extract_field_values(data: Dict[str, Any], prefix: str = "") -> Set[str]:
    """Recursively extract all string values from a JSON structure."""
    values = set()

    for key, value in data.items():
        if isinstance(value, str):
            if value.strip():  # Only add non-empty strings
                values.add(value.strip())
        elif isinstance(value, (int, float)):
            values.add(str(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    values.update(extract_field_values(item, f"{prefix}.{key}"))
                elif isinstance(item, str) and item.strip():
                    values.add(item.strip())
                elif isinstance(item, (int, float)):
                    values.add(str(item))
        elif isinstance(value, dict):
            values.update(extract_field_values(value, f"{prefix}.{key}"))

    return values


def test_fields_in_html(ground_truth_path: str, ai_output_path: str) -> Dict[str, Any]:
    """Test if all ground truth field values are present in the AI output HTML."""

    # Load ground truth data
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)[0]  # Get first (and only) case

    # Load AI output data with error handling
    try:
        with open(ai_output_path, "r", encoding="utf-8") as f:
            ai_data = json.load(f)[0]  # Get first (and only) case
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Error at line {e.lineno}, column {e.colno}")
        # Try to read the file content around the error
        with open(ai_output_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if e.lineno <= len(lines):
                print(f"Problematic line: {repr(lines[e.lineno-1])}")
                if e.lineno > 1:
                    print(f"Previous line: {repr(lines[e.lineno-2])}")
                if e.lineno < len(lines):
                    print(f"Next line: {repr(lines[e.lineno])}")
        raise

    # Extract HTML content
    html_content = ai_data.get("html", "")
    html_text = extract_text_from_html(html_content)

    # Extract all field values from ground truth
    gt_values = extract_field_values(gt_data)

    # Test each value
    results = {
        "total_fields": len(gt_values),
        "found_in_html": 0,
        "missing_from_html": 0,
        "found_values": [],
        "missing_values": [],
        "html_length": len(html_content),
        "html_text_length": len(html_text),
    }

    for value in gt_values:
        # Check if value appears in HTML text (case-insensitive)
        if value.lower() in html_text.lower():
            results["found_in_html"] += 1
            results["found_values"].append(value)
        else:
            results["missing_from_html"] += 1
            results["missing_values"].append(value)

    return results


def main():
    """Main function to run the test."""
    ground_truth_path = "tests/ground_truth/AI_772309_fixed.json"
    ai_output_path = "judex_output/AI_772309.json"

    print("Testing if ground truth fields are present in AI output HTML...")
    print("=" * 60)

    try:
        # Test file loading first
        print("Loading ground truth file...")
        with open(ground_truth_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)[0]
        print("✓ Ground truth loaded successfully")

        print("Loading AI output file...")
        with open(ai_output_path, "r", encoding="utf-8") as f:
            ai_data = json.load(f)[0]
        print("✓ AI output loaded successfully")

        results = test_fields_in_html(ground_truth_path, ai_output_path)

        print(f"Total fields in ground truth: {results['total_fields']}")
        print(f"Fields found in HTML: {results['found_in_html']}")
        print(f"Fields missing from HTML: {results['missing_from_html']}")
        print(
            f"Success rate: {(results['found_in_html'] / results['total_fields'] * 100):.1f}%"
        )
        print()
        print(f"HTML content length: {results['html_length']} characters")
        print(
            f"HTML text length (after cleaning): {results['html_text_length']} characters"
        )
        print()

        if results["missing_values"]:
            print("Missing values:")
            for value in results["missing_values"][:10]:  # Show first 10
                print(f"  - {value}")
            if len(results["missing_values"]) > 10:
                print(f"  ... and {len(results['missing_values']) - 10} more")

        print()
        if results["found_values"]:
            print("Found values (first 10):")
            for value in results["found_values"][:10]:
                print(f"  + {value}")
            if len(results["found_values"]) > 10:
                print(f"  ... and {len(results['found_values']) - 10} more")

    except FileNotFoundError as e:
        print(f"Error: Could not find file - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        print(f"Line: {e.lineno}, Column: {e.colno}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
