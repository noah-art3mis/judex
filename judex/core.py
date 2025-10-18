import json
import logging
import os
from typing import Literal

from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from scrapy.utils.project import get_project_settings

from .exceptions import JudexScraperError, ValidationError
from .spiders.stf import StfSpider

logger = logging.getLogger(__name__)

PersistenceTypes = list[Literal["json", "csv", "sql"]]


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
        salvar_como: PersistenceTypes,
        scraper_kind: str = "stf",
        output_path: str = "judex_output",
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
        db_path: str | None = None,
        custom_name: str | None = None,
        verbose: bool = False,
        overwrite: bool = False,
    ):
        # Validate inputs
        self._validate_inputs(processos, salvar_como)

        self.classe = classe
        self.processos = processos
        self.salvar_como = salvar_como
        self.scraper_kind = scraper_kind
        self.output_path = output_path
        self.skip_existing = skip_existing
        self.retry_failed = retry_failed
        self.max_age_hours = max_age_hours
        self.db_path = db_path
        self.custom_name = custom_name
        self.verbose = verbose
        self.overwrite = overwrite
        self.settings = get_project_settings()

        # Normalize salvar_como to list
        if not isinstance(salvar_como, list):
            salvar_como = [salvar_como]

        # Parse process numbers for filename generation
        self.process_numbers = self._parse_process_numbers()

        # Initialize spider and persistence components
        self.spider = self._select_spider()
        self.select_persistence()

    def _validate_inputs(self, processos: str, salvar_como: PersistenceTypes) -> None:
        """Validate input parameters"""
        if not isinstance(processos, str):
            raise ValidationError(
                "processos must be a string",
                field="processos",
                value=type(processos).__name__,
            )

        if not isinstance(salvar_como, (list, tuple)):
            raise ValidationError(
                "salvar_como must be a list or tuple",
                field="salvar_como",
                value=type(salvar_como).__name__,
            )

        if not all(isinstance(item, str) for item in salvar_como):
            raise ValidationError(
                "salvar_como must be a list or tuple of strings",
                field="salvar_como",
                value=[type(item).__name__ for item in salvar_como],
            )

        valid_formats = {"json", "csv", "sql", "jsonlines"}
        invalid_formats = [item for item in salvar_como if item not in valid_formats]
        if invalid_formats:
            raise ValidationError(
                f"salvar_como must contain only: {', '.join(valid_formats)}",
                field="salvar_como",
                value=invalid_formats,
            )

    def _parse_process_numbers(self) -> list | None:
        """Parse process numbers from JSON string"""
        try:
            return (
                json.loads(self.processos)
                if isinstance(self.processos, str)
                else self.processos
            )
        except (json.JSONDecodeError, TypeError):
            return None

    def _select_spider(self) -> Spider:
        """Select and initialize the appropriate spider using instance variables"""
        if self.scraper_kind == "stf":
            return StfSpider(
                self.classe,
                self.processos,
                skip_existing=self.skip_existing,
                retry_failed=self.retry_failed,
                max_age_hours=self.max_age_hours,
            )
        else:
            raise ValueError(f"Invalid spider kind: {self.scraper_kind}")

    def scrape(self) -> None:
        """Scrape the processes using instance variables"""
        self._log_scraping_info()

        try:
            process = CrawlerProcess(self.settings)
            process.crawl(
                self.spider.__class__,
                classe=self.classe,
                processos=self.processos,
                skip_existing=self.skip_existing,
                retry_failed=self.retry_failed,
                max_age_hours=self.max_age_hours,
            )
            process.start()
        except Exception as e:
            raise JudexScraperError(f"Scraping failed: {e}") from e

    def _log_scraping_info(self) -> None:
        """Log information about the scraping process"""
        logger.info("🚀 Starting scraping process")
        logger.info("📁 Output files will be saved to:")
        logger.info(f"   Output directory: {os.path.abspath(self.output_path)}")
        logger.info(f"   Classe: {self.classe}")
        logger.info(f"   Formats: {', '.join(self.salvar_como)}")
        logger.info(f"   Skip existing: {self.skip_existing}")
        logger.info(f"   Retry failed: {self.retry_failed}")
        logger.info(f"   Max age (hours): {self.max_age_hours}")

        # Show actual request count
        if self.process_numbers:
            total_processes = len(self.process_numbers)
            estimated_requests = total_processes * 5  # ~5 requests per process
            logger.info(
                f"📊 Expected requests: ~{estimated_requests} for {total_processes} processes"
            )

    def select_persistence(self) -> None:
        """Configure persistence pipelines and output files using instance variables"""
        from judex.output_registry import OutputFormatRegistry

        pipelines = self.settings.get("ITEM_PIPELINES", {})

        # Setup environment
        os.makedirs(self.output_path, exist_ok=True)

        # Configure FEEDS for formats that use it (JSON, CSV)
        self._configure_feeds(OutputFormatRegistry)

        # Configure pipelines for formats that don't use FEEDS (SQL)
        self._configure_pipelines(pipelines, OutputFormatRegistry)

        self.settings.set("ITEM_PIPELINES", pipelines)

    def _configure_feeds(self, OutputFormatRegistry) -> None:
        """Configure FEEDS for JSON and CSV formats"""
        feeds = OutputFormatRegistry.configure_feeds(
            self.output_path,
            self.classe,
            self.custom_name,
            self.salvar_como,
            self.process_numbers,
            self.overwrite,
        )
        if feeds:
            self.settings.set("FEEDS", feeds)

    def _configure_pipelines(self, pipelines: dict, OutputFormatRegistry) -> None:
        """Configure pipelines for formats that don't use FEEDS (SQL)"""
        for format_name in self.salvar_como:
            format_config = OutputFormatRegistry.get_format(format_name)
            if not format_config or format_config.get("use_feeds", True):
                continue

            pipeline_class = format_config.get("pipeline")
            priority = format_config.get("priority", 500)

            if pipeline_class:
                pipelines[pipeline_class] = priority

                if format_name == "sql":
                    self._configure_database_path()

    def _configure_database_path(self) -> None:
        """Configure database path for SQL persistence"""
        from .database import init_database

        if self.db_path:
            db_path = self.db_path
        else:
            db_path = os.path.join(self.output_path, "judex.db")

        self.settings.set("DATABASE_PATH", db_path)
        init_database(db_path)

    def get_status(self) -> dict:
        """Get current scraper status and configuration"""
        return {
            "classe": self.classe,
            "output_path": self.output_path,
            "formats": self.salvar_como,
            "skip_existing": self.skip_existing,
            "retry_failed": self.retry_failed,
            "max_age_hours": self.max_age_hours,
            "db_path": self.db_path,
            "custom_name": self.custom_name,
            "verbose": self.verbose,
            "process_numbers": self.process_numbers,
        }
