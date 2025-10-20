import csv
from typing import Any


def export_to_csv(data: list[dict[str, Any]], filename: str) -> bool:
    """Export data to a CSV file"""
    try:
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(data[0].keys())
            for row in data:
                writer.writerow(row.values())
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {str(e)}")
        return False
