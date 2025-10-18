"""
Spider strategy pattern for judex
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from scrapy.spiders import Spider

from ..spiders.stf import StfSpider


class SpiderStrategy(ABC):
    """Abstract base class for spider strategies"""

    @abstractmethod
    def create_spider(
        self,
        classe: str,
        processos: str,
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
        **kwargs,
    ) -> Spider:
        """Create and configure a spider instance"""
        pass

    @abstractmethod
    def get_spider_name(self) -> str:
        """Get the name of the spider strategy"""
        pass

    @abstractmethod
    def get_allowed_domains(self) -> List[str]:
        """Get allowed domains for this strategy"""
        pass

    @abstractmethod
    def validate_inputs(self, classe: str, processos: str) -> None:
        """Validate inputs specific to this strategy"""
        pass


class StfSpiderStrategy(SpiderStrategy):
    """Strategy for STF (Supremo Tribunal Federal) spider"""

    def create_spider(
        self,
        classe: str,
        processos: str,
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
        **kwargs,
    ) -> Spider:
        """Create and configure STF spider instance"""
        return StfSpider(
            classe=classe,
            processos=processos,
            skip_existing=skip_existing,
            retry_failed=retry_failed,
            max_age_hours=max_age_hours,
            **kwargs,
        )

    def get_spider_name(self) -> str:
        """Get the name of the STF spider"""
        return "stf"

    def get_allowed_domains(self) -> List[str]:
        """Get allowed domains for STF spider"""
        return ["portal.stf.jus.br"]

    def validate_inputs(self, classe: str, processos: str) -> None:
        """Validate inputs specific to STF spider"""
        from ..types import validate_case_type

        if not classe:
            raise ValueError("classe is required for STF spider")

        # Validate the case class against the enum
        validate_case_type(classe)

        if not processos:
            raise ValueError("processos is required for STF spider")


class SpiderStrategyFactory:
    """Factory for creating spider strategies"""

    _strategies: Dict[str, SpiderStrategy] = {
        "stf": StfSpiderStrategy(),
    }

    @classmethod
    def get_strategy(cls, strategy_name: str) -> SpiderStrategy:
        """Get a spider strategy by name"""
        if strategy_name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown spider strategy: {strategy_name}. Available: {available}"
            )

        return cls._strategies[strategy_name]

    @classmethod
    def register_strategy(cls, name: str, strategy: SpiderStrategy) -> None:
        """Register a new spider strategy"""
        cls._strategies[name] = strategy

    @classmethod
    def list_strategies(cls) -> List[str]:
        """List all available spider strategies"""
        return list(cls._strategies.keys())
