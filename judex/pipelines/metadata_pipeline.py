"""
Metadata pipeline for judex - adds metadata to items
"""

from typing import Any

import scrapy


class MetadataPipeline:
    """
    Pipeline to add metadata to items (spider name, timestamp, etc.)w
    """

    def process_item(self, item: Any, spider: scrapy.Spider) -> Any:
        # Metadata fields removed - just return the item unchanged
        return item
