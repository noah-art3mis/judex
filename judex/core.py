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
    """Main scraper class"""

    def __init__(
        self,
        classe: str,
        processos: str,
        scraper_kind: str = "stf",
        output_path: str = "judex_output",
        persistence_types: PersistenceTypes = None,
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
    ):
        if not isinstance(processos, str):
            raise Exception("processos must be a string")
        if not isinstance(persistence_types, (list, tuple)):
            raise Exception("persistence_types must be a list or tuple")
        if not all(isinstance(item, str) for item in persistence_types):
            raise Exception("persistence_types must be a list or tuple of strings")
        if not all(item in ["json", "csv", "sql"] for item in persistence_types):
            raise Exception(
                "persistence_types must be a list of any of: 'json', 'csv', 'sql' or None"
            )

        os.makedirs(output_path, exist_ok=True)
        PipelineManager.select_persistence(persistence_types, output_path)
        self.spider = self.select_spider(
            scraper_kind, classe, processos, skip_existing, retry_failed, max_age_hours
        )

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
        settings = get_project_settings()
        process = CrawlerProcess(settings)
        process.crawl(
            self.spider.__class__,
            classe=self.spider.classe,
            processos=json.dumps(self.spider.numeros),
            skip_existing=self.spider.skip_existing,
            retry_failed=self.spider.retry_failed,
            max_age_hours=self.spider.max_age_hours,
        )
        process.start()
