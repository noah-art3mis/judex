import os
from typing import Literal

from scrapy.utils.project import get_project_settings

from judex.database import init_database

PersistenceTypes = list[Literal["json", "csv", "sql"]] | None


class PipelineManager:
    @staticmethod
    def select_persistence(persistence_types: PersistenceTypes, output_path: str) -> None:
        """Configure persistence pipelines and output files"""
        if not persistence_types:
            return

        settings = get_project_settings()
        pipelines = settings.get("ITEM_PIPELINES", {})

        for persistence_type in persistence_types:
            if persistence_type == "json":
                pipelines["judex.pipelines.JSONPipeline"] = 500
            elif persistence_type == "csv":
                pipelines["judex.pipelines.CSVPipeline"] = 500
            elif persistence_type == "sql":
                pipelines["judex.pipelines.DatabasePipeline"] = 300

        settings.set("ITEM_PIPELINES", pipelines)

        # Set output files with proper paths
        os.makedirs(output_path, exist_ok=True)
        settings.set("JSON_OUTPUT_FILE", os.path.join(output_path, "data.json"))
        settings.set("CSV_OUTPUT_FILE", os.path.join(output_path, "data.csv"))
        settings.set("DATABASE_PATH", os.path.join(output_path, "data.db"))

        if "sql" in persistence_types:
            init_database(settings.get("DATABASE_PATH"))
