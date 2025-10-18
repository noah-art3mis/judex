"""
Metadata pipeline for judex - adds metadata to items
"""

from typing import Any

import scrapy
from itemadapter import ItemAdapter


class MetadataPipeline:
    """
    Pipeline to add metadata to items (spider name, timestamp, etc.)
    """

    def process_item(self, item: Any, spider: scrapy.Spider) -> Any:
        adapter = ItemAdapter(item)
        adapter["_spider_name"] = spider.name
        adapter["_scraped_at"] = (
            spider.crawler.stats.get_value("start_time") if spider.crawler.stats else None
        )
        adapter["_item_count"] = (
            spider.crawler.stats.get_value("item_scraped_count", 0) if spider.crawler.stats else 0
        )
        return item
