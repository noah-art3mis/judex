"""
Pydantic validation pipeline for STF case data
"""

import logging
from typing import Any, Dict

from itemadapter import ItemAdapter
from pydantic import ValidationError
from scrapy import Item

from .models import STFCaseModel

logger = logging.getLogger(__name__)


class PydanticValidationPipeline:
    """Pipeline to validate scraped data with Pydantic models"""

    def process_item(self, item: Item, spider) -> Item:
        """Validate item with Pydantic model"""
        adapter = ItemAdapter(item)
        item_dict = dict(adapter)

        try:
            # Validate with Pydantic model
            validated_item = STFCaseModel(**item_dict)

            # Convert back to dict and update the item with validated data
            validated_dict = validated_item.model_dump()

            # Update the item with validated data
            for key, value in validated_dict.items():
                item[key] = value

            logger.info(f"Validated case: {validated_dict.get('numero_unico', 'unknown')}")

            return item

        except ValidationError as e:
            logger.error(
                f"Pydantic validation failed for case {item_dict.get('processo_id', 'unknown')}: {e}"
            )
            # Log the specific validation errors for debugging
            for error in e.errors():
                logger.error(f"Validation error in field '{error['loc']}': {error['msg']}")

            # You can choose to yield the item anyway or skip it
            # For now, we'll return the item to continue processing
            return item
        except Exception as e:
            logger.error(
                f"Unexpected error in Pydantic validation for case {item_dict.get('processo_id', 'unknown')}: {e}"
            )
            return item
