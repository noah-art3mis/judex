"""
Pipelines package for judex
"""

from .csv_pipeline import CSVPipeline
from .database_pipeline import DatabasePipeline
from .json_pipeline import JSONPipeline
from .metadata_pipeline import MetadataPipeline

__all__ = [
    "DatabasePipeline",
    "MetadataPipeline",
    "JSONPipeline",
    "CSVPipeline",
]
