import json
import os

from exporters import export_to_csv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from .database import get_all_processos, save_processo_data
from .loaders import load_yaml
from .spiders.stf import STFSpider


class LexiconScraper:
    """Main scraper class for STF cases"""

    def __init__(
        self,
        output_dir: str = "lexicon",
        db_path: str = "lexicon.db",
        filename: str = "processos.csv",
    ):
        self.output_dir = output_dir
        self.settings = get_project_settings()

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        processos_query = load_yaml(yaml_file=os.path.join(output_dir, "processos.yaml"))

        for classe, processos in processos_query.items():
            print(f"Scraping {classe} cases: {len(processos)} processes")

            spider_results = self._run_spider(classe, processos)

            save_processo_data(db_path, spider_results)

            export_to_csv(spider_results, os.path.join(self.output_dir, f"{classe}_processos.csv"))

            return get_all_processos(db_path)

    def scrape_cases(self, classe: str, processos: list[int]) -> list[dict]:
        """Scrape specific cases"""
        return self._run_spider(classe, processos)

    def _run_spider(self, classe: str, processos: list[int]) -> list[dict]:
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

        process = CrawlerProcess(self.settings)
        process.crawl(STFSpider, classe=classe, processos=processos)
        process.start()

        with open(output_file, encoding="utf-8") as f:
            return json.load(f)
