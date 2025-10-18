import argparse
import json
import logging
import sys

from judex.core import JudexScraper


def main():
    parser = argparse.ArgumentParser(
        prog="judex",
        description="Judex Legal Case Scraper - Scrape legal cases from STF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  judex -c ADI -p 987 -o json
  judex -c ADI -p 987 988 989 -o json csv
  judex -c ADI -p 987 -o json --output-path ./data --verbose
        """,
    )

    # Required arguments with short names
    parser.add_argument(
        "-c",
        "--classe",
        required=True,
        help="The class of the process to scrape (e.g., ADI, ADPF, ACI, etc.)",
    )

    parser.add_argument(
        "-p",
        "--processos",
        nargs="+",
        type=int,
        required=True,
        help="The process numbers to scrape (can specify multiple)",
    )

    parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        choices=["json", "csv", "sql"],
        required=True,
        help="Persistence types to use (required)",
    )

    # Optional arguments
    parser.add_argument(
        "--scraper-kind",
        default="stf",
        choices=["stf"],
        help="The kind of scraper to use (default: stf)",
    )

    parser.add_argument(
        "--output-path",
        default="judex_output",
        help="The path to the output directory (default: judex_output)",
    )

    parser.add_argument(
        "--save-to-db",
        default=False,
        help="Whether to save to sqlite database (default: false)",
    )

    parser.add_argument(
        "--db-path", help="Path to the database file (default: auto-generated)"
    )

    parser.add_argument(
        "--custom-name",
        help="Custom name for output files (default: classe + processo)",
    )

    parser.add_argument(
        "--skip-existing",
        type=lambda x: x.lower() in ["true", "1", "yes", "on"],
        default=True,
        help="Whether to skip existing processes (default: true)",
    )

    parser.add_argument(
        "--retry-failed",
        type=lambda x: x.lower() in ["true", "1", "yes", "on"],
        default=True,
        help="Whether to retry failed processes (default: true)",
    )

    parser.add_argument(
        "--max-age",
        type=int,
        default=24,
        help="Maximum age of processes to scrape in hours (default: 24)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files instead of appending (default: false)",
    )

    args = parser.parse_args()

    # Validate JSON output requires overwrite flag
    if "json" in args.output and not args.overwrite:
        print(
            "❌ Error: JSON output format requires the --overwrite flag.",
            file=sys.stderr,
        )
        print(
            "   Reason: Appending to JSON files creates invalid JSON arrays.",
            file=sys.stderr,
        )
        print("   Solution: Add --overwrite flag to your command.", file=sys.stderr)
        sys.exit(1)

    try:
        # Convert process numbers to JSON string format expected by JudexScraper
        processos_json = json.dumps(args.processos)

        # Create and run the scraper
        scraper = JudexScraper(
            classe=args.classe,
            processos=processos_json,
            scraper_kind=args.scraper_kind,
            output_path=args.output_path,
            salvar_como=args.output,
            skip_existing=args.skip_existing,
            retry_failed=args.retry_failed,
            max_age_hours=args.max_age,
            db_path=args.db_path,
            custom_name=args.custom_name,
            verbose=args.verbose,
            overwrite=args.overwrite,
        )

        print(
            f"🚀 Starting scraper for class '{args.classe}' with processes {args.processos}"
        )
        print(f"📁 Output directory: {args.output_path}")
        print(f"💾 Output types: {', '.join(args.output)}")
        print(f"💾 Save to SQL database: {args.save_to_db}")

        scraper.scrape()

        print("✅ Scraping completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
