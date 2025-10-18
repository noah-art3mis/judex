import os
from typing import Literal

from scrapy.utils.project import get_project_settings

from judex.database import init_database

PersistenceTypes = list[Literal["json", "csv", "sql"]]


class PipelineManager:
    @staticmethod
    def select_persistence(
        salvar_como: PersistenceTypes,
        output_path: str,
        classe: str | None = None,
        db_path: str | None = None,
    ) -> None:
        """Configure persistence pipelines and output files"""
        if not salvar_como:
            return

        settings = get_project_settings()
        pipelines = settings.get("ITEM_PIPELINES", {})

        for persistence_type in salvar_como:
            if persistence_type == "json":
                pipelines["judex.pipelines.JSONPipeline"] = 500
            elif persistence_type == "csv":
                pipelines["judex.pipelines.CSVPipeline"] = 500
            elif persistence_type == "sql":
                pipelines["judex.pipelines.DatabasePipeline"] = 300

        settings.set("ITEM_PIPELINES", pipelines)

        # Set output files with proper paths
        os.makedirs(output_path, exist_ok=True)

        # Use custom db_path if provided, otherwise use classe-specific naming
        if db_path:
            settings.set("DATABASE_PATH", db_path)
        elif classe:
            settings.set(
                "DATABASE_PATH", os.path.join(output_path, f"{classe}_cases.db")
            )
        else:
            settings.set("DATABASE_PATH", os.path.join(output_path, "data.db"))

        # Set JSON and CSV output files
        if classe:
            settings.set(
                "JSON_OUTPUT_FILE", os.path.join(output_path, f"{classe}_cases.json")
            )
            settings.set(
                "CSV_OUTPUT_FILE", os.path.join(output_path, f"{classe}_processos.csv")
            )
        else:
            settings.set("JSON_OUTPUT_FILE", os.path.join(output_path, "data.json"))
            settings.set("CSV_OUTPUT_FILE", os.path.join(output_path, "data.csv"))

        if "sql" in salvar_como:
            init_database(settings.get("DATABASE_PATH"))
