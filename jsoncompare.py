#!/usr/bin/env python3
"""
JSON Ground Truth Comparison Script

This script compares scraped JSON files with ground truth files,
identifies differences, and provides analysis for data structure adjustments.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union


@dataclass
class FieldDifference:
    """Represents a difference between two JSON structures"""

    path: str
    ground_truth_value: Any
    scraped_value: Any
    difference_type: str  # 'missing', 'extra', 'different_value', 'different_type'


class JSONComparator:
    """Compares JSON files and identifies structural differences"""

    def __init__(self, ground_truth_dir: str, scraped_dir: str):
        self.ground_truth_dir = Path(ground_truth_dir)
        self.scraped_dir = Path(scraped_dir)
        self.differences: List[FieldDifference] = []

    def load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}

    def compare_structures(
        self, ground_truth: Dict[str, Any], scraped: Dict[str, Any], path: str = ""
    ) -> List[FieldDifference]:
        """Recursively compare two JSON structures"""
        differences = []

        # Get all keys from both structures
        gt_keys = set(ground_truth.keys()) if isinstance(ground_truth, dict) else set()
        scraped_keys = set(scraped.keys()) if isinstance(scraped, dict) else set()

        # Ignore specific fields that should not be compared
        # Currently ignoring raw HTML payloads
        ignored_keys = {"html"}
        gt_keys = gt_keys - ignored_keys
        scraped_keys = scraped_keys - ignored_keys

        # Check for missing keys in scraped data
        for key in gt_keys - scraped_keys:
            differences.append(
                FieldDifference(
                    path=f"{path}.{key}" if path else key,
                    ground_truth_value=ground_truth[key],
                    scraped_value=None,
                    difference_type="missing",
                )
            )

        # Check for extra keys in scraped data
        for key in scraped_keys - gt_keys:
            differences.append(
                FieldDifference(
                    path=f"{path}.{key}" if path else key,
                    ground_truth_value=None,
                    scraped_value=scraped[key],
                    difference_type="extra",
                )
            )

        # Compare common keys
        for key in gt_keys & scraped_keys:
            current_path = f"{path}.{key}" if path else key
            gt_value = ground_truth[key]
            scraped_value = scraped[key]

            if isinstance(gt_value, dict) and isinstance(scraped_value, dict):
                differences.extend(
                    self.compare_structures(gt_value, scraped_value, current_path)
                )
            elif isinstance(gt_value, list) and isinstance(scraped_value, list):
                differences.extend(
                    self.compare_lists(gt_value, scraped_value, current_path)
                )
            elif gt_value != scraped_value:
                differences.append(
                    FieldDifference(
                        path=current_path,
                        ground_truth_value=gt_value,
                        scraped_value=scraped_value,
                        difference_type="different_value",
                    )
                )
            elif type(gt_value) != type(scraped_value):
                differences.append(
                    FieldDifference(
                        path=current_path,
                        ground_truth_value=gt_value,
                        scraped_value=scraped_value,
                        difference_type="different_type",
                    )
                )

        return differences

    def compare_lists(
        self, gt_list: List[Any], scraped_list: List[Any], path: str
    ) -> List[FieldDifference]:
        """Compare two lists"""
        differences = []

        # Compare lengths
        if len(gt_list) != len(scraped_list):
            differences.append(
                FieldDifference(
                    path=f"{path}.length",
                    ground_truth_value=len(gt_list),
                    scraped_value=len(scraped_list),
                    difference_type="different_value",
                )
            )

        # Compare elements up to the minimum length
        min_length = min(len(gt_list), len(scraped_list))
        for i in range(min_length):
            if isinstance(gt_list[i], dict) and isinstance(scraped_list[i], dict):
                differences.extend(
                    self.compare_structures(gt_list[i], scraped_list[i], f"{path}[{i}]")
                )
            elif isinstance(gt_list[i], list) and isinstance(scraped_list[i], list):
                differences.extend(
                    self.compare_lists(gt_list[i], scraped_list[i], f"{path}[{i}]")
                )
            elif gt_list[i] != scraped_list[i]:
                differences.append(
                    FieldDifference(
                        path=f"{path}[{i}]",
                        ground_truth_value=gt_list[i],
                        scraped_value=scraped_list[i],
                        difference_type="different_value",
                    )
                )

        return differences

    def find_matching_files(self) -> List[Tuple[Path, Path]]:
        """Find matching ground truth and scraped files"""
        matches = []

        # Get all ground truth files
        gt_files = list(self.ground_truth_dir.glob("*.json"))

        for gt_file in gt_files:
            # Try to find corresponding scraped file
            scraped_file = self.scraped_dir / gt_file.name
            if scraped_file.exists():
                matches.append((gt_file, scraped_file))
            else:
                print(f"Warning: No matching scraped file for {gt_file.name}")

        return matches

    def analyze_differences(self, differences: List[FieldDifference]) -> Dict[str, Any]:
        """Analyze and categorize differences"""
        analysis = {
            "total_differences": len(differences),
            "by_type": defaultdict(int),
            "by_path": defaultdict(list),
            "critical_missing": [],
            "structural_issues": [],
        }

        for diff in differences:
            analysis["by_type"][diff.difference_type] += 1
            analysis["by_path"][diff.path].append(diff)

            # Identify critical missing fields
            if diff.difference_type == "missing":
                if any(
                    keyword in diff.path.lower()
                    for keyword in [
                        "numero_unico",
                        "classe",
                        "processo_id",
                        "incidente",
                    ]
                ):
                    analysis["critical_missing"].append(diff)

            # Identify structural issues
            if diff.difference_type in ["different_type", "extra"]:
                analysis["structural_issues"].append(diff)

        return analysis

    def generate_html_analysis(
        self,
        file_pairs: List[Tuple[Path, Path]],
        output_file: str = "comparison_report.html",
    ):
        """Generate HTML report with detailed analysis"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>JSON Ground Truth Comparison Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .file-section {{ margin: 20px 0; border: 1px solid #ddd; padding: 15px; }}
                .difference {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; }}
                .missing {{ border-left: 4px solid #ff6b6b; }}
                .extra {{ border-left: 4px solid #4ecdc4; }}
                .different {{ border-left: 4px solid #ffe66d; }}
                .critical {{ background-color: #ffebee; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>JSON Ground Truth Comparison Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """

        total_differences = 0

        for gt_file, scraped_file in file_pairs:
            print(f"Comparing {gt_file.name} with {scraped_file.name}")

            gt_data = self.load_json_file(gt_file)
            scraped_data = self.load_json_file(scraped_file)

            if not gt_data or not scraped_data:
                continue

            # Take first item if it's a list
            if isinstance(gt_data, list) and len(gt_data) > 0:
                gt_data = gt_data[0]
            if isinstance(scraped_data, list) and len(scraped_data) > 0:
                scraped_data = scraped_data[0]

            differences = self.compare_structures(gt_data, scraped_data)
            analysis = self.analyze_differences(differences)
            total_differences += len(differences)

            html_content += f"""
            <div class="file-section">
                <h2>{gt_file.name}</h2>
                <div class="summary">
                    <h3>Summary</h3>
                    <p><strong>Total Differences:</strong> {len(differences)}</p>
                    <p><strong>Missing Fields:</strong> {analysis['by_type']['missing']}</p>
                    <p><strong>Extra Fields:</strong> {analysis['by_type']['extra']}</p>
                    <p><strong>Different Values:</strong> {analysis['by_type']['different_value']}</p>
                    <p><strong>Different Types:</strong> {analysis['by_type']['different_type']}</p>
                </div>
            """

            if analysis["critical_missing"]:
                html_content += """
                <div class="critical">
                    <h3>Critical Missing Fields</h3>
                """
                for diff in analysis["critical_missing"]:
                    html_content += f"""
                    <div class="difference missing">
                        <strong>Path:</strong> {diff.path}<br>
                        <strong>Expected:</strong> {json.dumps(diff.ground_truth_value, indent=2)}<br>
                        <strong>Found:</strong> None
                    </div>
                    """
                html_content += "</div>"

            # Show all differences
            html_content += "<h3>All Differences</h3>"
            for diff in differences:
                css_class = diff.difference_type
                html_content += f"""
                <div class="difference {css_class}">
                    <strong>Path:</strong> {diff.path}<br>
                    <strong>Type:</strong> {diff.difference_type}<br>
                    <strong>Ground Truth:</strong> {json.dumps(diff.ground_truth_value, indent=2)}<br>
                    <strong>Scraped:</strong> {json.dumps(diff.scraped_value, indent=2)}
                </div>
                """

            html_content += "</div>"

        html_content += f"""
            <div class="summary">
                <h2>Overall Summary</h2>
                <p><strong>Total Files Compared:</strong> {len(file_pairs)}</p>
                <p><strong>Total Differences Found:</strong> {total_differences}</p>
            </div>
        </body>
        </html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTML report generated: {output_file}")

    def generate_markdown_report(
        self,
        file_pairs: List[Tuple[Path, Path]],
        output_file: str = "comparison_report.md",
    ) -> None:
        """Generate a concise Markdown report in the requested format.

        Format per difference:
        - <path>
            - ground-truth: "..."
            - actual-result: "..."
        """
        lines: List[str] = []
        lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        total_differences = 0
        for gt_file, scraped_file in file_pairs:
            gt_data = self.load_json_file(gt_file)
            scraped_data = self.load_json_file(scraped_file)
            if not gt_data or not scraped_data:
                continue
            if isinstance(gt_data, list) and len(gt_data) > 0:
                gt_data = gt_data[0]
            if isinstance(scraped_data, list) and len(scraped_data) > 0:
                scraped_data = scraped_data[0]

            differences = self.compare_structures(gt_data, scraped_data)
            total_differences += len(differences)

            if not differences:
                continue

            lines.append(f"- {gt_file.name}")
            for diff in differences:
                # Use the path as the primary bullet text for each difference
                lines.append(f"\t- {diff.path}")
                gt_str = json.dumps(diff.ground_truth_value, ensure_ascii=False)
                scraped_str = json.dumps(diff.scraped_value, ensure_ascii=False)
                lines.append(f'\t\t- ground-truth: "{gt_str}"')
                lines.append(f'\t\t- actual-result: "{scraped_str}"')
            lines.append("")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Markdown report generated: {output_file}")

    def run_comparison(self, output_file: str = "comparison_report.md"):
        """Run the complete comparison process"""
        print("Starting JSON Ground Truth Comparison...")

        # Find matching files
        file_pairs = self.find_matching_files()

        if not file_pairs:
            print("No matching files found!")
            return

        print(f"Found {len(file_pairs)} file pairs to compare")

        # Always generate Markdown report
        self.generate_markdown_report(file_pairs, output_file=output_file)

        # Print summary to console
        total_differences = 0
        for gt_file, scraped_file in file_pairs:
            print(f"\n--- Comparing {gt_file.name} ---")

            gt_data = self.load_json_file(gt_file)
            scraped_data = self.load_json_file(scraped_file)

            if not gt_data or not scraped_data:
                print("Skipping due to loading errors")
                continue

            # Take first item if it's a list
            if isinstance(gt_data, list) and len(gt_data) > 0:
                gt_data = gt_data[0]
            if isinstance(scraped_data, list) and len(scraped_data) > 0:
                scraped_data = scraped_data[0]

            differences = self.compare_structures(gt_data, scraped_data)
            analysis = self.analyze_differences(differences)
            total_differences += len(differences)

            print(f"Differences found: {len(differences)}")
            print(f"  - Missing: {analysis['by_type']['missing']}")
            print(f"  - Extra: {analysis['by_type']['extra']}")
            print(f"  - Different values: {analysis['by_type']['different_value']}")
            print(f"  - Different types: {analysis['by_type']['different_type']}")

            if analysis["critical_missing"]:
                print("  Critical missing fields:")
                for diff in analysis["critical_missing"]:
                    print(f"    - {diff.path}")

        print(f"\nTotal differences across all files: {total_differences}")


def main():
    parser = argparse.ArgumentParser(description="Compare JSON files with ground truth")
    parser.add_argument(
        "--ground-truth-dir",
        "-gt",
        default="tests/ground_truth",
        help="Directory containing ground truth JSON files",
    )
    parser.add_argument(
        "--scraped-dir",
        "-s",
        default="judex_output",
        help="Directory containing scraped JSON files",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="comparison_report.md",
        help="Output Markdown report filename",
    )

    args = parser.parse_args()

    # Validate directories
    if not os.path.exists(args.ground_truth_dir):
        print(f"Error: Ground truth directory '{args.ground_truth_dir}' not found")
        sys.exit(1)

    if not os.path.exists(args.scraped_dir):
        print(f"Error: Scraped directory '{args.scraped_dir}' not found")
        sys.exit(1)

    # Run comparison
    comparator = JSONComparator(args.ground_truth_dir, args.scraped_dir)
    comparator.run_comparison(output_file=args.output)


if __name__ == "__main__":
    main()
