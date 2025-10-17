#!/usr/bin/env python3
"""
Example script demonstrating the database-first optimization for the STF scraper.

This script shows how the scraper now checks the database before making requests,
significantly reducing the number of HTTP requests made to the STF portal.
"""

from lexicon.core import LexiconScraper
from lexicon.database import (
    get_existing_processo_ids,
    get_failed_processo_ids,
    init_database,
)


def demonstrate_database_optimization():
    """Demonstrate the database-first approach"""

    # Initialize database
    db_path = "lexicon.db"
    init_database(db_path)

    print("=== STF Scraper Database-First Optimization Demo ===\n")

    # Check what's already in the database
    existing_adi = get_existing_processo_ids(db_path, "ADI", max_age_hours=24)
    failed_adi = get_failed_processo_ids(db_path, "ADI", max_age_hours=24)

    print(f"Existing ADI cases in database (last 24h): {len(existing_adi)}")
    print(f"Failed ADI cases in database (last 24h): {len(failed_adi)}")

    if existing_adi:
        print(f"Existing cases: {sorted(existing_adi)}")
    if failed_adi:
        print(f"Failed cases: {sorted(failed_adi)}")

    print("\n=== Running Scraper with Database Optimization ===")

    # Create scraper with database-first optimization
    scraper = LexiconScraper(
        output_dir="output",
        db_path=db_path,
        skip_existing=True,  # Skip cases already in database
        retry_failed=True,  # Retry cases that previously failed
        max_age_hours=24,  # Only skip cases scraped within last 24 hours
    )

    # Example: Scrape some ADI cases
    # The scraper will automatically skip cases that already exist
    # and only retry failed cases
    test_cases = "[4916, 4917, 4918, 4919, 4920]"

    print(f"Requesting to scrape cases: {test_cases}")
    print("The scraper will:")
    print("- Skip cases that already exist in the database")
    print("- Retry cases that previously failed")
    print("- Only scrape new cases")
    print("- Log how many cases were skipped vs scraped")

    # This would normally be called like:
    # scraper.scrape_cases("ADI", test_cases)

    print(f"\nTo run the actual scraping, uncomment the line below:")
    print(f"# scraper.scrape_cases('ADI', '{test_cases}')")


def show_optimization_benefits():
    """Show the benefits of the database-first approach"""

    print("\n=== Optimization Benefits ===")
    print("1. REDUCED REQUESTS: Skip already-scraped cases")
    print("2. SMART RETRY: Only retry cases that actually failed")
    print("3. TIME SAVINGS: No duplicate work")
    print("4. RESPECTFUL SCRAPING: Fewer requests to STF servers")
    print("5. INCREMENTAL UPDATES: Easy to add new cases to existing dataset")

    print("\n=== Usage Examples ===")
    print("# Skip existing cases, retry failed ones:")
    print("scraper = LexiconScraper(skip_existing=True, retry_failed=True)")

    print("\n# Force re-scrape everything (disable optimization):")
    print("scraper = LexiconScraper(skip_existing=False, retry_failed=False)")

    print("\n# Only retry failed cases, don't skip existing:")
    print("scraper = LexiconScraper(skip_existing=False, retry_failed=True)")

    print("\n# Custom age threshold (skip cases older than 12 hours):")
    print("scraper = LexiconScraper(max_age_hours=12)")


if __name__ == "__main__":
    demonstrate_database_optimization()
    show_optimization_benefits()
