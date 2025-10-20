import os
from io import BytesIO
from typing import Any, BinaryIO, List, Optional, cast

from scrapy.exporters import JsonItemExporter


class JsonPipeline:
    """Pipeline to save scraped items to JSON file"""

    def __init__(
        self,
        output_path,
        classe,
        custom_name=None,
        process_numbers=None,
        overwrite=True,
    ):
        self.output_path = output_path
        self.classe = classe
        self.custom_name = custom_name
        self.process_numbers = process_numbers
        self.overwrite = overwrite
        self.file: Optional[BinaryIO] = None
        self.exporter: Optional[JsonItemExporter] = None
        self.fields_to_export: Optional[List[str]] = None

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls(
            output_path=crawler.settings.get("OUTPUT_PATH", "judex_output"),
            classe=crawler.settings.get("CLASSE"),
            custom_name=crawler.settings.get("CUSTOM_NAME"),
            process_numbers=crawler.settings.get("PROCESS_NUMBERS"),
            overwrite=crawler.settings.get("OVERWRITE", True),
        )
        # Pass FEED_EXPORT_FIELDS down to exporter for ordering
        obj.fields_to_export = crawler.settings.getlist("FEED_EXPORT_FIELDS")
        return obj

    def open_spider(self, spider):
        # Generate filename
        if self.custom_name:
            base_name = self.custom_name
        else:
            if self.process_numbers:
                process_str = "_".join(map(str, self.process_numbers))
                base_name = f"{self.classe}_{process_str}"
            else:
                base_name = f"{self.classe}_processos"

        file_path = os.path.join(self.output_path, f"{base_name}.json")

        # Handle overwrite
        if self.overwrite and os.path.exists(file_path):
            os.remove(file_path)

        self.file = cast(BinaryIO, open(file_path, "wb"))
        # Respect top-level order from settings if provided
        fields = self.fields_to_export
        # JsonItemExporter accepts a file-like binary stream; wrap for strict typing
        stream = cast(BinaryIO, self.file)
        if not hasattr(stream, "write"):
            stream = cast(BinaryIO, BytesIO())
        self.exporter = JsonItemExporter(
            cast(Any, stream),
            indent=2,
            ensure_ascii=False,
            export_empty_fields=True,
            fields_to_export=fields,
        )
        self.exporter.start_exporting()

    def close_spider(self, spider):
        if self.exporter:
            self.exporter.finish_exporting()
        if self.file:
            self.file.close()

    def process_item(self, item, spider):
        if self.exporter is not None:
            self.exporter.export_item(item)
        return item
