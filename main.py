from judex.core import judexScraper


def main():
    scraper = judexScraper(
        input_file="processos.yaml",
        output_dir="output",
        db_path="judex.db",
        filename="processos.csv",
        skip_existing=True,  # Skip cases already in database
        retry_failed=True,  # Retry cases that previously failed
        max_age_hours=24,  # Only skip cases scraped within last 24 hours
    )
    scraper.scrape_cases("ADI", "[4916, 4917]")


if __name__ == "__main__":
    main()
