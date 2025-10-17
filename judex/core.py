import json
import logging
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from .database import get_all_processos, save_processo_data
from .exporters import export_to_csv
from .loaders import load_yaml
from .spiders.stf import StfSpider

logger = logging.getLogger(__name__)


class judexScraper:
    """Main scraper class for STF cases"""

    def __init__(
        self,
        input_file: str | None = None,
        output_dir: str = "judex",
        db_path: str = "judex.db",
        filename: str = "processos.csv",
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
    ):
        self.output_dir = output_dir
        self.db_path = db_path
        self.settings = get_project_settings()
        self.skip_existing = skip_existing
        self.retry_failed = retry_failed
        self.max_age_hours = max_age_hours

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def scrape_cases(self, classe: str, processos: str) -> None:
        spider_results = self._run_spider(classe, processos)
        logger.info(f"Processos scraped for {classe}: {len(spider_results)} cases")
        # Database saving is now handled by the pipeline
        export_to_csv(spider_results, os.path.join(self.output_dir, f"{classe}_processos.csv"))
        logger.info(f"Processos scraped for {classe} exported to CSV")

    def _run_spider(self, classe: str, processos: str) -> list[dict]:
        """Run the spider for a specific class and process list"""

        output_file = os.path.join(self.output_dir, f"{classe}_cases.json")

        # Update settings
        self.settings.set(
            "FEEDS",
            {
                output_file: {
                    "format": "json",
                    "indent": 2,
                    "encoding": "utf8",
                    "store_empty": False,
                }
            },
        )

        # Add database pipeline
        self.settings.set(
            "ITEM_PIPELINES",
            {
                "judex.pipelines.DatabasePipeline": 300,
            },
        )

        # Set database path
        self.settings.set("DATABASE_PATH", self.db_path)

        process = CrawlerProcess(self.settings)
        process.crawl(
            StfSpider,
            classe=classe,
            processos=processos,
            skip_existing=self.skip_existing,
            retry_failed=self.retry_failed,
            max_age_hours=self.max_age_hours,
        )
        process.start()

        with open(output_file, encoding="utf-8") as f:
            return json.load(f)
