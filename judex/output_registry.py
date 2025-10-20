"""
Output format registry for judex
"""

import os
from typing import Any, Dict, Optional


class OutputFormatRegistry:
    """Registry for output formats and their configurations"""

    _formats: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_format(cls, name: str, config: Dict[str, Any]) -> None:
        """Register a new output format"""
        cls._formats[name] = config

    @classmethod
    def get_format(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a format"""
        return cls._formats.get(name)

    @classmethod
    def get_all_formats(cls) -> Dict[str, Dict[str, Any]]:
        """Get all registered formats"""
        return cls._formats.copy()

    @classmethod
    def configure_pipelines(
        cls,
        output_path: str,
        classe: str,
        custom_name: Optional[str] = None,
        requested_formats: Optional[list] = None,
        process_numbers: Optional[list] = None,
        overwrite: bool = False,
    ) -> Dict[str, int]:
        """Configure pipelines based on registered formats and user input"""
        pipelines = {}

        # Only configure pipelines for requested formats
        formats_to_check = requested_formats if requested_formats else cls._formats.keys()

        for format_name in formats_to_check:
            config = cls._formats.get(format_name)
            if config and config.get("pipeline"):
                pipeline_class = config.get("pipeline")
                priority = config.get("priority", 300)
                pipelines[pipeline_class] = priority

        return pipelines

    @classmethod
    def get_pipeline_config(
        cls,
        format_name: str,
        output_path: str,
        classe: str,
        custom_name: Optional[str] = None,
        process_numbers: Optional[list] = None,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Get pipeline configuration for a specific format"""
        config = cls._formats.get(format_name)
        if not config or not config.get("pipeline"):
            return {}

        # Generate filename
        if custom_name:
            base_name = custom_name
        else:
            if process_numbers:
                process_str = "_".join(map(str, process_numbers))
                base_name = f"{classe}_{process_str}"
            else:
                base_name = f"{classe}_processos"

        file_path = os.path.join(output_path, f"{base_name}.{config['extension']}")

        return {
            "output_path": output_path,
            "classe": classe,
            "custom_name": custom_name,
            "process_numbers": process_numbers,
            "overwrite": overwrite,
            "file_path": file_path,
            "base_name": base_name,
            **config.get("extra_config", {}),
        }


# Register default formats
OutputFormatRegistry.register_format(
    "json",
    {
        "format": "json",
        "extension": "json",
        "pipeline": "judex.pipelines.JsonPipeline",
        "priority": 300,
        "overwrite": True,
        "extra_config": {
            "indent": 2,
            "export_empty_fields": True,
        },
    },
)

OutputFormatRegistry.register_format(
    "csv",
    {
        "format": "csv",
        "extension": "csv",
        "pipeline": "judex.pipelines.CsvPipeline",
        "priority": 300,
        "overwrite": True,
        "encoding": "utf8",
        "extra_config": {
            "include_headers_line": True,
        },
    },
)

OutputFormatRegistry.register_format(
    "jsonl",
    {
        "format": "jsonl",
        "extension": "jsonl",
        "pipeline": "judex.pipelines.JsonLinesPipeline",
        "priority": 300,
        "overwrite": False,  # Use append mode for JSONLines
        "encoding": "utf8",
        "extra_config": {},
    },
)

OutputFormatRegistry.register_format(
    "sql",
    {
        "format": "sql",
        "extension": "db",
        "pipeline": "judex.pipelines.DatabasePipeline",
        "priority": 300,
        "extra_config": {},
    },
)
