import json
import logging
import os

from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from scrapy.utils.project import get_project_settings

from .pipelines.manager import PersistenceTypes, PipelineManager
from .spiders.stf import StfSpider

logger = logging.getLogger(__name__)


class JudexScraper:
    """Main scraper class

    Args:
        classe: The class of the process to scrape
        processos: The processes to scrape
        scraper_kind: The kind of scraper to use
        output_path: The path to the output directory
        salvar_como: The persistence types to use
        skip_existing: Whether to skip existing processes
        retry_failed: Whether to retry failed processes
        max_age_hours: The maximum age of the processes to scrape
    """

    def __init__(
        self,
        classe: str,
        processos: str,
        salvar_como: PersistenceTypes | list[PersistenceTypes],
        scraper_kind: str = "stf",
        output_path: str = "judex_output",
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
        db_path: str | None = None,
    ):
        if not isinstance(processos, str):
            raise Exception("processos must be a string")
        if not isinstance(salvar_como, (list, tuple)):
            raise Exception("salvar_como must be a list or tuple")
        if not all(isinstance(item, str) for item in salvar_como):
            raise Exception("salvar_como must be a list or tuple of strings")
        if not all(item in ["json", "csv", "sql"] for item in salvar_como):
            raise Exception(
                "salvar_como must be a list of any of: 'json', 'csv', 'sql' or None"
            )

        if not isinstance(salvar_como, list):
            salvar_como = [salvar_como]

        if not salvar_como:
            salvar_como = ["json"]

        if not isinstance(salvar_como, list[str]):
            raise Exception("salvar_como must be a list of strings")

        os.makedirs(output_path, exist_ok=True)
        self.salvar_como = salvar_como
        self.output_path = output_path
        self.db_path = db_path
        self.spider = self.select_spider(
            scraper_kind, classe, processos, skip_existing, retry_failed, max_age_hours
        )

        # Configure persistence pipelines
        PipelineManager.select_persistence(salvar_como, output_path, classe, db_path)

    def select_spider(
        self,
        spider_kind: str,
        classe: str,
        processos: str,
        skip_existing: bool,
        retry_failed: bool,
        max_age_hours: int,
    ) -> Spider:
        if spider_kind == "stf":
            return StfSpider(
                classe,
                processos,
                skip_existing=skip_existing,
                retry_failed=retry_failed,
                max_age_hours=max_age_hours,
            )
        else:
            raise ValueError(f"Invalid spider kind: {spider_kind}")

    def scrape(self) -> None:
        """Scrape the processes"""
        settings = get_project_settings()

        # Set dynamic feed names based on classe
        classe = getattr(self.spider, "classe", "")
        json_path = f"output/{classe}_cases.json"
        csv_path = f"output/{classe}_processos.csv"

        settings.set(
            "FEEDS",
            {
                json_path: {
                    "format": "json",
                    "indent": 2,
                    "encoding": "utf8",
                    "store_empty": False,
                    "fields": None,
                    "item_export_kwargs": {
                        "export_empty_fields": True,
                    },
                },
                csv_path: {
                    "format": "csv",
                    "encoding": "utf8",
                    "store_empty": False,
                },
            },
        )

        # Log the output paths
        import os

        abs_json_path = os.path.abspath(json_path)
        abs_csv_path = os.path.abspath(csv_path)

        # Use custom db_path if provided, otherwise use default naming
        if self.db_path:
            db_path = self.db_path
        else:
            db_path = f"{self.output_path}/{classe}_cases.db"
        abs_db_path = os.path.abspath(db_path)

        logger.info("📁 Output files will be saved to:")
        logger.info(f"   JSON: {abs_json_path}")
        logger.info(f"   CSV:  {abs_csv_path}")
        logger.info(f"   DB:   {abs_db_path}")

        process = CrawlerProcess(settings)
        process.crawl(
            self.spider.__class__,
            classe=getattr(self.spider, "classe", ""),
            processos=json.dumps(getattr(self.spider, "numeros", [])),
            skip_existing=getattr(self.spider, "skip_existing", True),
            retry_failed=getattr(self.spider, "retry_failed", True),
            max_age_hours=getattr(self.spider, "max_age_hours", 24),
        )
        process.start()
