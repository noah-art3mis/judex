"""Custom exceptions for the judex scraper"""


class JudexScraperError(Exception):
    """Base exception for JudexScraper errors"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ValidationError(JudexScraperError):
    """Raised when input validation fails"""

    def __init__(self, message: str, field: str | None = None, value=None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, details)
