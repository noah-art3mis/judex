#!/usr/bin/env python3
"""
Test script to scrape one processo, find it in database, and compare results.
"""

import argparse
import json
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict


def run_scraper(classe: str, incidente: int, output_path: str) -> Dict[str, Any]:
    """Run the scraper and return the scraped data"""
    print(f"🔍 Scraping {classe} {incidente}...")

    # Run the scraper
    cmd = [
        "uv",
        "run",
        "main.py",
        "-c",
        classe,
        "-p",
        str(incidente),
        "-s",
        "json",
        "--output-path",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"❌ Scraper failed: {result.stderr}")
            return {}

        print("✅ Scraper completed successfully")
        return {"status": "success", "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        print("❌ Scraper timed out")
        return {"status": "timeout"}
    except Exception as e:
        print(f"❌ Scraper error: {e}")
        return {"status": "error", "error": str(e)}


def get_database_processo(db_path: str, incidente: int) -> Dict[str, Any]:
    """Get processo data from database"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get main processo data
            cursor.execute("SELECT * FROM processos WHERE incidente = ?", (incidente,))
            processo_row = cursor.fetchone()

            if not processo_row:
                return {}

            # Get column names
            columns = [description[0] for description in cursor.description]
            processo_data = dict(zip(columns, processo_row))

            # Get related data
            tables = [
                "partes",
                "andamentos",
                "decisoes",
                "deslocamentos",
                "peticoes",
                "recursos",
                "pautas",
            ]
            for table in tables:
                try:
                    cursor.execute(
                        f"SELECT * FROM {table} WHERE numero_unico = ?",
                        (processo_data["numero_unico"],),
                    )
                    rows = cursor.fetchall()
                    if rows:
                        table_columns = [description[0] for description in cursor.description]
                        processo_data[table] = [dict(zip(table_columns, row)) for row in rows]
                    else:
                        processo_data[table] = []
                except sqlite3.OperationalError:
                    processo_data[table] = []

            return processo_data

    except Exception as e:
        print(f"❌ Database error: {e}")
        return {}


def load_scraped_json(output_path: str, classe: str) -> Dict[str, Any]:
    """Load the scraped JSON data"""
    json_file = Path(output_path) / f"{classe}_processos.json"

    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        return {}

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # If it's a list, take the first item
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        elif isinstance(data, dict):
            return data
        else:
            print("❌ Unexpected JSON format")
            return {}

    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return {}


def compare_data(scraped_data: Dict[str, Any], db_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compare scraped data with database data"""
    comparison = {
        "matches": {},
        "differences": {},
        "missing_in_db": [],
        "missing_in_scraped": [],
        "summary": {},
    }

    # Key fields to compare
    key_fields = [
        "incidente",
        "numero_unico",
        "classe",
        "tipo_processo",
        "liminar",
        "relator",
        "origem",
        "origem_orgao",
        "data_protocolo",
        "autor1",
    ]

    for field in key_fields:
        scraped_val = scraped_data.get(field)
        db_val = db_data.get(field)

        if scraped_val == db_val:
            comparison["matches"][field] = scraped_val
        else:
            comparison["differences"][field] = {
                "scraped": scraped_val,
                "database": db_val,
            }

    # Compare related data counts
    related_tables = [
        "partes",
        "andamentos",
        "decisoes",
        "deslocamentos",
        "peticoes",
        "recursos",
        "pautas",
    ]

    for table in related_tables:
        scraped_count = len(scraped_data.get(table, []))
        db_count = len(db_data.get(table, []))

        comparison["summary"][f"{table}_count"] = {
            "scraped": scraped_count,
            "database": db_count,
            "match": scraped_count == db_count,
        }

    return comparison


def print_comparison_report(comparison: Dict[str, Any], incidente: int):
    """Print a detailed comparison report"""
    print(f"\n📊 COMPARISON REPORT FOR INCIDENTE {incidente}")
    print("=" * 60)

    # Matches
    if comparison["matches"]:
        print(f"\n✅ MATCHING FIELDS ({len(comparison['matches'])}):")
        for field, value in comparison["matches"].items():
            print(f"  {field}: {value}")

    # Differences
    if comparison["differences"]:
        print(f"\n❌ DIFFERENT FIELDS ({len(comparison['differences'])}):")
        for field, values in comparison["differences"].items():
            print(f"  {field}:")
            print(f"    Scraped: {values['scraped']}")
            print(f"    Database: {values['database']}")

    # Related data counts
    print("\n📈 RELATED DATA COUNTS:")
    for table, counts in comparison["summary"].items():
        if table.endswith("_count"):
            table_name = table.replace("_count", "")
            status = "✅" if counts["match"] else "❌"
            print(f"  {status} {table_name}: Scraped={counts['scraped']}, DB={counts['database']}")


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Compare scraped data with database data")
    parser.add_argument("classe", help="Classe do processo (e.g. ADI)")
    parser.add_argument("incidente", type=int, help="Número do incidente")
    args = parser.parse_args()

    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "judex.db")

    print("🧪 TESTING SCRAPER vs DATABASE COMPARISON")
    print(f"📋 Target: {args.classe} {args.incidente}")
    print(f"🗄️  Database: {db_path}")
    print("=" * 60)

    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = temp_dir

        # Step 1: Run scraper
        print("\n1️⃣ RUNNING SCRAPER...")
        scrape_result = run_scraper(args.classe, args.incidente, output_path)

        if scrape_result.get("status") != "success":
            print("❌ Scraper failed, cannot continue")
            return

        # Step 2: Load scraped data
        print("\n2️⃣ LOADING SCRAPED DATA...")
        scraped_data = load_scraped_json(output_path, args.classe)

        if not scraped_data:
            print("❌ No scraped data found")
            return

        print(f"✅ Loaded scraped data with {len(scraped_data)} fields")

        # Step 3: Get database data
        print("\n3️⃣ LOADING DATABASE DATA...")
        db_data = get_database_processo(db_path, args.incidente)

        if not db_data:
            print("❌ No database data found")
            return

        print(f"✅ Loaded database data with {len(db_data)} fields")

        # Step 4: Compare data
        print("\n4️⃣ COMPARING DATA...")
        comparison = compare_data(scraped_data, db_data)

        # Step 5: Print report
        print_comparison_report(comparison, args.incidente)

        # Step 6: Summary
        print("\n📋 SUMMARY:")
        print(f"  Scraped fields: {len(scraped_data)}")
        print(f"  Database fields: {len(db_data)}")
        print(f"  Matching fields: {len(comparison['matches'])}")
        print(f"  Different fields: {len(comparison['differences'])}")

        # Check if data matches
        all_match = len(comparison["differences"]) == 0
        print(f"\n🎯 RESULT: {'✅ DATA MATCHES' if all_match else '❌ DATA DIFFERS'}")


if __name__ == "__main__":
    main()
