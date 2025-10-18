import os

from scrapy.exporters import JsonLinesItemExporter


class JsonLinesPipeline:
    """Pipeline to save scraped items to JSONLines file"""

    def __init__(
        self,
        output_path,
        classe,
        custom_name=None,
        process_numbers=None,
        overwrite=False,
    ):
        self.output_path = output_path
        self.classe = classe
        self.custom_name = custom_name
        self.process_numbers = process_numbers
        self.overwrite = overwrite
        self.file = None
        self.exporter = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_path=crawler.settings.get("OUTPUT_PATH", "judex_output"),
            classe=crawler.settings.get("CLASSE"),
            custom_name=crawler.settings.get("CUSTOM_NAME"),
            process_numbers=crawler.settings.get("PROCESS_NUMBERS"),
            overwrite=crawler.settings.get("OVERWRITE", False),
        )

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

        file_path = os.path.join(self.output_path, f"{base_name}.jsonl")

        # Handle overwrite (JSONLines typically appends)
        if self.overwrite and os.path.exists(file_path):
            os.remove(file_path)

        self.file = open(file_path, "ab")  # Append mode
        self.exporter = JsonLinesItemExporter(self.file, encoding="utf-8")
        self.exporter.start_exporting()

    def close_spider(self, spider):
        if self.exporter:
            self.exporter.finish_exporting()
        if self.file:
            self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
