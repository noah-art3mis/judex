import logging

import scrapy
from itemadapter import ItemAdapter

from ..database import init_database, processo_write

logger = logging.getLogger(__name__)


class DatabasePipeline:
    """Pipeline to save scraped items to database"""

    def __init__(self, db_path):
        self.db_path = db_path
        init_database(db_path)
        logger.info(f"Database pipeline initialized with path: {db_path}")

    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline instance from crawler settings"""
        db_path = crawler.settings.get("DATABASE_PATH", "judex.db")
        return cls(db_path)

    def process_item(self, item, spider: scrapy.Spider) -> ItemAdapter:
        """Process each item and save to database"""
        adapter = ItemAdapter(item)
        item_dict = dict(adapter)
        success = processo_write(self.db_path, item_dict)

        if success:
            logger.info(
                f"Saved item to database: {item_dict.get('numero_unico', 'unknown')}"
            )
        else:
            logger.error(
                f"Failed to save item to database: {item_dict.get('numero_unico', 'unknown')}"
            )

        return item
