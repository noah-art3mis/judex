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
    def configure_feeds(
        cls,
        output_path: str,
        classe: str,
        custom_name: Optional[str] = None,
        requested_formats: Optional[list] = None,
        process_numbers: Optional[list] = None,
        overwrite: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """Configure FEEDS based on registered formats and user input"""
        feeds = {}

        # Generate file names
        if custom_name:
            base_name = custom_name
        else:
            if process_numbers:
                # Include process numbers in the filename
                process_str = "_".join(map(str, process_numbers))

                # Limit filename length to avoid filesystem issues
                # Most filesystems support 255 characters, but we'll be conservative
                max_filename_length = 200
                full_name = f"{classe}_{process_str}"

                if len(full_name) > max_filename_length:
                    # If too long, use a truncated version with count
                    truncated_processes = process_numbers[:5]  # Show first 5 processes
                    remaining_count = len(process_numbers) - 5
                    process_str = "_".join(map(str, truncated_processes))
                    if remaining_count > 0:
                        process_str += f"_and_{remaining_count}_more"
                    base_name = f"{classe}_{process_str}"
                else:
                    base_name = full_name
            else:
                base_name = f"{classe}_processos"

        # Only configure feeds for requested formats
        formats_to_check = (
            requested_formats if requested_formats else cls._formats.keys()
        )

        for format_name in formats_to_check:
            config = cls._formats.get(format_name)
            if config and config.get("use_feeds", False):
                file_path = os.path.join(
                    output_path, f"{base_name}.{config['extension']}"
                )
                # Create a copy of the config and add overwrite setting
                feed_config = config.copy()
                feed_config["overwrite"] = overwrite
                feeds[file_path] = feed_config

        return feeds


# Register default formats
OutputFormatRegistry.register_format(
    "json",
    {
        "format": "json",
        "extension": "json",
        "use_feeds": True,
        "overwrite": True,  # Force overwrite existing files
        # "encoding": "utf8",
        "store_empty": False,
        "extra_config": {
            "indent": 2,
            "fields": None,
            "item_export_kwargs": {
                "export_empty_fields": True,
            },
        },
    },
)

OutputFormatRegistry.register_format(
    "csv",
    {
        "format": "csv",
        "extension": "csv",
        "use_feeds": True,
        "overwrite": True,  # Force overwrite existing files
        "encoding": "utf8",
        "store_empty": False,
        "extra_config": {},
    },
)

OutputFormatRegistry.register_format(
    "sql",
    {
        "format": "sql",
        "extension": "db",
        "use_feeds": False,  # Uses custom pipeline
        "pipeline": "judex.pipelines.DatabasePipeline",
        "priority": 300,
    },
)
