# Lexicon - STF Data Scraper

A web scraper for the Brazilian Supreme Court (STF) with Pydantic data validation.

## 🚀 Features

-   **Web Scraping**: Automated data extraction from STF portal
-   **Data Validation**: Pydantic models ensure data integrity
-   **Database Integration**: SQLite storage with normalized tables
-   **Type Safety**: Runtime validation with clear error messages
-   **Field Mapping**: Automatic conversion between scraping and database schemas

## ⚖️ Legal and Ethical Considerations

### Robots.txt and Terms of Service

**Important Legal Notice**: This project scrapes publicly available data from the STF (Supreme Federal Court) portal. Please note:

-   **robots.txt is not legally binding** - It's a voluntary protocol that websites use to communicate with web crawlers, but it has no legal force
-   **No Terms of Service found** - Despite extensive searching, the STF portal does not have publicly accessible terms of service that would legally restrict data access
-   **Public data only** - This scraper only accesses publicly available case information that is already accessible through the web interface
-   **Respectful scraping** - The scraper implements delays and follows ethical scraping practices to avoid overloading the server

### STF Portal robots.txt Analysis

```
User-agent: *
Disallow: /processos

User-agent: AhrefsBot
Disallow: /
```

The robots.txt file disallows access to `/processos` for all user agents, but this is not legally enforceable. The scraper accesses individual case pages through direct URLs, not the disallowed `/processos` directory.

> 📋 **For detailed legal analysis**, see [LEGAL.md](LEGAL.md) for comprehensive information about robots.txt, terms of service, and legal considerations.

## 🛠 Installation

```bash
# Clone and install
git clone <repository-url>
cd lexicon
uv sync

# Install ChromeDriver
sudo apt-get install chromium-chromedriver
```

## 🚀 Quick Start

```python
from lexicon.core import LexiconScraper

# Initialize and scrape
scraper = LexiconScraper(output_dir="output", db_path="lexicon.db")
scraper.scrape_cases("ADI", "[1234, 5678, 9012]")
```

### Command Line

```bash
# Scrape specific cases
scrapy crawl stf -a classe='ADI' -a processos='[1234, 5678]'
```

## 🏗 Architecture

```
STF Portal → Scrapy Spider → Pydantic Validation → SQLite DB
```

**Key Components**:

-   **Spider**: Web scraping logic
-   **Models**: Pydantic data validation
-   **Pipeline**: Data processing
-   **Database**: SQLite storage

## 📊 Data Models

```python
from lexicon.models import STFCaseModel

case = STFCaseModel(
    processo_id=123,
    incidente=456,
    classe="ADI",
    numero_unico="ADI 123456",
    tipo_processo="Eletrônico",
    # ... other fields
)
```

**Supported Case Types**: ADI, ADPF, HC, MS, RE, and 50+ others

## ⚙️ Configuration

```python
# lexicon/settings.py
DATABASE_PATH = "lexicon.db"
DOWNLOAD_DELAY = 2.0
CONCURRENT_REQUESTS = 1
ITEM_PIPELINES = {
    "lexicon.pydantic_pipeline.PydanticValidationPipeline": 200,
    "lexicon.pipelines.DatabasePipeline": 300,
}
```

## 🧪 Testing

### Local Testing

```bash
# Run all tests
uv run python -m pytest

# Run with coverage
uv run python -m pytest --cov=lexicon --cov-report=html
```

### Docker Testing (Cross-Platform)

```bash
# Test across Python versions (3.9, 3.10, 3.11)
./scripts/docker-test.sh build
./scripts/docker-test.sh test

# Test specific components
./scripts/docker-test.sh test-models
./scripts/docker-test.sh test-database
```

**Test Coverage**: 89.5% (77/86 tests passing)

> 📋 **For detailed Docker testing**, see [DOCKER.md](DOCKER.md) for cross-platform testing instructions.

## 📚 API Reference

```python
# Main scraper
scraper = LexiconScraper(output_dir="output", db_path="lexicon.db")
scraper.scrape_cases("ADI", "[1234, 5678]")

# Data model
case = STFCaseModel(
    processo_id=123,
    incidente=456,
    classe="ADI"
)
```

## 🐛 Troubleshooting

```bash
# ChromeDriver issues
chromedriver --version
sudo apt-get install chromium-chromedriver

# Database locked
ps aux | grep lexicon
pkill -f lexicon
```

```python
# Validation errors
try:
    case = STFCaseModel(**data)
except ValidationError as e:
    print(f"Validation errors: {e.errors()}")
```

## 🤝 Contributing

```bash
# Development setup
uv sync --group dev
uv run ruff check .
uv run black .
uv run mypy lexicon/
```

## 📄 License

MIT License - see LICENSE file for details.
