"""
Pipelines for the lexicon project
"""

from pydantic import ValidationError
from scrapy.exceptions import DropItem


class PydanticValidationPipeline:
    """Pipeline to validate items using Pydantic models"""

    def process_item(self, item, spider):
        try:
            # Convert Scrapy item to dict and validate with Pydantic
            item_dict = dict(item)
            validated_item = STFCaseItemPydantic(**item_dict)

            # Convert back to dict for Scrapy
            return validated_item.dict()

        except ValidationError as e:
            spider.logger.error(
                f"Validation error for item {item.get('processo_id', 'unknown')}: {e}"
            )
            raise DropItem(f"Invalid item: {e}")
        except Exception as e:
            spider.logger.error(f"Unexpected error validating item: {e}")
            raise DropItem(f"Validation failed: {e}")


class DataCleaningPipeline:
    """Pipeline to clean and normalize data"""

    def process_item(self, item, spider):
        # Clean string fields
        string_fields = [
            "numero_unico",
            "classe",
            "nome_processo",
            "tipo_processo",
            "origem",
            "relator",
            "liminar",
            "data_protocolo",
            "origem_orgao",
            "autor1",
            "assuntos",
        ]

        for field in string_fields:
            if field in item and item[field] is not None:
                # Strip whitespace and clean up
                cleaned = str(item[field]).strip()
                if cleaned == "":
                    item[field] = None
                else:
                    item[field] = cleaned

        return item
