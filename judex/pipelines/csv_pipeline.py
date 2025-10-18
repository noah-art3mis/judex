"""
CSV export pipeline for judex
"""

import csv
import logging
import os
from typing import Any

import scrapy
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class CSVPipeline:
    """Pipeline to export items to CSV file"""

    def __init__(self, output_file: str = "output.csv"):
        self.output_file = output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        self.items: list[dict] = []

    @classmethod
    def from_crawler(cls, crawler):
        output_file = crawler.settings.get("CSV_OUTPUT_FILE", "output.csv")
        return cls(output_file)

    def close_spider(self, spider):
        if self.items:
            with open(self.output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if self.items:
                    writer.writerow(self.items[0].keys())
                    for item in self.items:
                        writer.writerow(item.values())
            logger.info(f"Exported {len(self.items)} items to {self.output_file}")

    def process_item(self, item: Any, spider: scrapy.Spider) -> Any:
        adapter = ItemAdapter(item)
        self.items.append(dict(adapter))
        return item
