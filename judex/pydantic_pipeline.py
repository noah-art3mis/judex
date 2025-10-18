"""
Pydantic validation pipeline for STF case data
"""

import logging

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

        # Filter out metadata fields before validation
        metadata_fields = {'_spider_name', '_scraped_at', '_item_count'}
        filtered_dict = {k: v for k, v in item_dict.items() if k not in metadata_fields}

        try:
            # Validate with Pydantic model
            validated_item = STFCaseModel(**filtered_dict)

            # Convert back to dict and update the item with validated data
            validated_dict = validated_item.model_dump()

            # Clear the item and update with validated data only
            for key in list(item.keys()):
                del item[key]
            
            for key, value in validated_dict.items():
                item[key] = value

            logger.info(
                f"Validated case: {validated_dict.get('numero_unico', 'unknown')}"
            )

            return item

        except ValidationError as e:
            logger.error(
                f"Pydantic validation failed for case {item_dict.get('processo_id', 'unknown')}: {e}"
            )
            # Log the specific validation errors for debugging
            for error in e.errors():
                logger.error(
                    f"Validation error in field '{error['loc']}': {error['msg']}"
                )

            # You can choose to yield the item anyway or skip it
            # For now, we'll return the item to continue processing
            return item
        except Exception as e:
            logger.error(
                f"Unexpected error in Pydantic validation for case {item_dict.get('processo_id', 'unknown')}: {e}"
            )
            return item
