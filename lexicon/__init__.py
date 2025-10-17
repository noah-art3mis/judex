"""
Lexicon - STF Case Scraping Library
"""

from .database import LexiconDatabase
from .export import LexiconExporter
from .spiders import StfSpider

__version__ = "1.0.0"
__all__ = ["LexiconScraper", "LexiconDatabase", "LexiconExporter"]
