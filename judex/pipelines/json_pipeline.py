"""
JSON export pipeline for judex
"""

import json
import logging
import os
from typing import Any

import scrapy
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class JSONPipeline:
    """Pipeline to export items to JSON file"""

    def __init__(self, output_file: str = "output.json"):
        self.output_file = output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        self.items: list[dict] = []

    @classmethod
    def from_crawler(cls, crawler):
        output_file = crawler.settings.get("JSON_OUTPUT_FILE", "output.json")
        return cls(output_file)

    def close_spider(self, spider):
        if self.items:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Exported {len(self.items)} items to {self.output_file}")

    def process_item(self, item: Any, spider: scrapy.Spider) -> Any:
        adapter = ItemAdapter(item)
        self.items.append(dict(adapter))
        return item
