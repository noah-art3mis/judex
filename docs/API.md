# judex API Reference

## 📚 Core API Documentation

This document provides comprehensive API reference for the judex STF data scraper with Pydantic integration.

## 🏗 Core Classes

### `JudexScraper`

Main orchestrator class for the scraping process.

```python
class JudexScraper:
    def __init__(
        self,
        input_file: str | None = None,
        output_dir: str = "judex",
        db_path: str = "judex.db",
        filename: str = "processos.csv",
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
    ) -> None
```

**Parameters**:

-   `input_file` (str | None): Path to YAML input file with process lists
-   `output_dir` (str): Directory for output files (default: "judex")
-   `db_path` (str): Path to SQLite database (default: "judex.db")
-   `filename` (str): Output CSV filename (default: "processos.csv")
-   `skip_existing` (bool): Skip processes already in database (default: True)
-   `retry_failed` (bool): Retry previously failed processes (default: True)
-   `max_age_hours` (int): Maximum age for existing data in hours (default: 24)

**Methods**:

#### `scrape(classe: str, processos: str) -> None`

Scrape cases for a specific class and process list.

**Parameters**:

-   `classe` (str): Case type (e.g., "ADI", "ADPF", "HC")
-   `processos` (str): JSON string of process numbers (e.g., "[1234, 5678]")

**Example**:

```python
scraper = JudexScraper()
scraper.scrape("ADI", "[1234, 5678, 9012]")
```

## 🕷 Spider Classes

### `StfSpider`

Scrapy spider for STF data extraction.

```python
class StfSpider(scrapy.Spider):
    def __init__(
        self,
        classe: str | None = None,
        processos: str | None = None,
        internal_delay: float = 1.0,
        skip_existing: bool = True,
        retry_failed: bool = True,
        max_age_hours: int = 24,
        *args,
        **kwargs,
    ) -> None
```

**Parameters**:

-   `classe` (str | None): Case type to scrape
-   `processos` (str | None): JSON string of process numbers
-   `internal_delay` (float): Delay between requests in seconds (default: 1.0)
-   `skip_existing` (bool): Skip existing processes (default: True)
-   `retry_failed` (bool): Retry failed processes (default: True)
-   `max_age_hours` (int): Maximum age for existing data (default: 24)

**Methods**:

#### `start_requests() -> Iterator[scrapy.Request]`

Generate initial requests for scraping.

**Returns**: Iterator of Scrapy Request objects

#### `parse_main_page_selenium(response: Response) -> Iterator[STFCaseItem]`

Parse main page content using Selenium.

**Parameters**:

-   `response` (Response): Scrapy Response object

**Returns**: Iterator of STFCaseItem objects

#### `get_element_by_id(driver: WebDriver, id: str) -> str`

Extract element value by ID using Selenium.

**Parameters**:

-   `driver` (WebDriver): Selenium WebDriver instance
-   `id` (str): Element ID to extract

**Returns**: Element value as string

#### `get_element_by_xpath(driver: WebDriver, xpath: str) -> str`

Extract element value by XPath using Selenium.

**Parameters**:

-   `driver` (WebDriver): Selenium WebDriver instance
-   `xpath` (str): XPath expression

**Returns**: Element value as string

#### `clean_text(html_text: str) -> str | None`

Clean HTML text by removing tags and normalizing whitespace.

**Parameters**:

-   `html_text` (str): Raw HTML text

**Returns**: Cleaned text or None if empty

## 📊 Data Models

### `STFCaseModel`

Main Pydantic model for STF cases.

```python
class STFCaseModel(BaseModel):
    # IDs
    processo_id: int
    incidente: int
    numero_unico: str | None = None

    # Classification
    classe: str
    tipo_processo: ProcessType | None = None
    liminar: int | None = None
    relator: str | None = None

    # Process details
    origem: str | None = None
    data_protocolo: str | None = None
    origem_orgao: str | None = None
    autor1: str | None = None
    assuntos: str | None = None

    # AJAX-loaded content
    partes: list[Parte] = Field(default_factory=list)
    andamentos: list[Andamento] = Field(default_factory=list)
    decisoes: list[Decisao] = Field(default_factory=list)
    deslocamentos: list[Deslocamento] = Field(default_factory=list)
    peticoes: list[Peticao] = Field(default_factory=list)
    recursos: list[Recurso] = Field(default_factory=list)
    pautas: list[Pauta] = Field(default_factory=list)
    sessao: Sessao | None = None

    # Metadata
    status: int | None = None
    html: str | None = None
    extraido: str | None = None
```

**Fields**:

-   `processo_id` (int): Process ID number
-   `incidente` (int): Incident number
-   `numero_unico` (str | None): Unique process number
-   `classe` (str): Case type (e.g., "ADI", "ADPF")
-   `tipo_processo` (ProcessType | None): Process type ("Físico" or "Eletrônico")
-   `liminar` (int | None): Injunction status (0 or 1)
-   `relator` (str | None): Reporting judge name
-   `origem` (str | None): Process origin
-   `data_protocolo` (str | None): Protocol date
-   `origem_orgao` (str | None): Origin organization
-   `autor1` (str | None): First author/plaintiff
-   `assuntos` (str | None): Subjects as JSON string
-   `partes` (list[Parte]): Parties involved
-   `andamentos` (list[Andamento]): Process movements
-   `decisoes` (list[Decisao]): Decisions made
-   `deslocamentos` (list[Deslocamento]): Displacements
-   `peticoes` (list[Peticao]): Petitions filed
-   `recursos` (list[Recurso]): Appeals filed
-   `pautas` (list[Pauta]): Agendas
-   `sessao` (Sessao | None): Session information
-   `status` (int | None): HTTP response status
-   `html` (str | None): Raw HTML content
-   `extraido` (str | None): Extraction timestamp

### Sub-models

#### `Parte`

Model for process parties.

```python
class Parte(BaseModel):
    index: int | None = None
    tipo: str | None = None
    nome: str | None = None
```

#### `Andamento`

Model for process movements.

```python
class Andamento(BaseModel):
    index_num: int | None = None
    data: str | None = None
    nome: str | None = None
    complemento: str | None = None
    julgador: str | None = None
```

#### `Decisao`

Model for decisions.

```python
class Decisao(BaseModel):
    index_num: int | None = None
    data: str | None = None
    nome: str | None = None
    complemento: str | None = None
    julgador: str | None = None
    link: str | None = None
```

#### `Deslocamento`

Model for displacements.

```python
class Deslocamento(BaseModel):
    index_num: int | None = None
    data_enviado: str | None = None
    data_recebido: str | None = None
    enviado_por: str | None = None
    recebido_por: str | None = None
    guia: str | None = None
```

#### `Peticao`

Model for petitions.

```python
class Peticao(BaseModel):
    index_num: int | None = None
    data: str | None = None
    tipo: str | None = None
    autor: str | None = None
    recebido_data: str | None = None
    recebido_por: str | None = None
```

#### `Recurso`

Model for appeals.

```python
class Recurso(BaseModel):
    index_num: int | None = None
    data: str | None = None
    nome: str | None = None
    julgador: str | None = None
    complemento: str | None = None
    autor: str | None = None
```

#### `Pauta`

Model for agendas.

```python
class Pauta(BaseModel):
    index_num: int | None = None
    data: str | None = None
    nome: str | None = None
    complemento: str | None = None
    relator: str | None = None
```

#### `Sessao`

Model for sessions.

```python
class Sessao(BaseModel):
    data: str | None = None
    tipo: str | None = None
    numero: str | None = None
    relator: str | None = None
```

## 🔧 Enums

### `CaseType`

Enum for STF case types.

```python
class CaseType(str, Enum):
    AC = "AC"      # Ação Cível
    ACO = "ACO"    # Ação Cível Originária
    ADC = "ADC"    # Ação Declaratória de Constitucionalidade
    ADI = "ADI"    # Ação Direta de Inconstitucionalidade
    ADO = "ADO"    # Ação Direta de Inconstitucionalidade por Omissão
    ADPF = "ADPF"  # Arguição de Descumprimento de Preceito Fundamental
    # ... 50+ other case types
```

### `ProcessType`

Enum for process types.

```python
class ProcessType(str, Enum):
    FISICO = "Físico"
    ELETRONICO = "Eletrônico"
```

## 🔄 Pipeline Classes

### `PydanticValidationPipeline`

Pipeline for Pydantic data validation.

```python
class PydanticValidationPipeline:
    def process_item(self, item: Item, spider) -> Item
```

**Parameters**:

-   `item` (Item): Scrapy Item to validate
-   `spider`: Spider instance

**Returns**: Validated Item

**Features**:

-   Automatic data validation using Pydantic models
-   Type conversion and field mapping
-   Error logging and handling
-   Database integration

### `DatabasePipeline`

Pipeline for database operations.

```python
class DatabasePipeline:
    def __init__(self, db_path: str)
    def process_item(self, item: Item, spider: scrapy.Spider) -> ItemAdapter
```

**Parameters**:

-   `db_path` (str): Path to SQLite database

**Features**:

-   Normalized table structure
-   Foreign key relationships
-   Data integrity constraints
-   Batch operations

## 🗄 Database Functions

### `processo_write(db_path: str, processo_data: dict[str, Any]) -> bool`

Save processed case data to database.

**Parameters**:

-   `db_path` (str): Path to SQLite database
-   `processo_data` (dict[str, Any]): Case data dictionary

**Returns**: Success status (bool)

**Example**:

```python
success = processo_write("judex.db", {
    "processo_id": 123,
    "incidente": 456,
    "classe": "ADI",
    # ... other fields
})
```

### `get_existing_processo_ids(db_path: str, classe: str, max_age_hours: int = 24) -> set[int]`

Get existing process IDs from database.

**Parameters**:

-   `db_path` (str): Path to SQLite database
-   `classe` (str): Case type
-   `max_age_hours` (int): Maximum age in hours (default: 24)

**Returns**: Set of existing process IDs

### `get_failed_processo_ids(db_path: str, classe: str, max_age_hours: int = 24) -> set[int]`

Get failed process IDs from database.

**Parameters**:

-   `db_path` (str): Path to SQLite database
-   `classe` (str): Case type
-   `max_age_hours` (int): Maximum age in hours (default: 24)

**Returns**: Set of failed process IDs

### `init_database(db_path: str) -> None`

Initialize database with required tables.

**Parameters**:

-   `db_path` (str): Path to SQLite database

## 🔍 Type Validation

### `validate_case_type(classe: str) -> str`

Validate that the case type is a valid STF case type.

**Parameters**:

-   `classe` (str): Case type to validate

**Returns**: Validated case type string

**Raises**: `ValueError` if invalid case type

### `is_valid_case_type(classe: str) -> bool`

Check if a case type is valid without raising an exception.

**Parameters**:

-   `classe` (str): Case type to check

**Returns**: True if valid, False otherwise

### `get_all_case_types() -> list[str]`

Get all valid STF case types as a list.

**Returns**: Sorted list of valid case types

## 🛠 Utility Functions

### `clean_text(html_text: str) -> str | None`

Clean HTML text by removing tags and normalizing whitespace.

**Parameters**:

-   `html_text` (str): Raw HTML text

**Returns**: Cleaned text or None if empty

### `load_yaml(file_path: str) -> dict`

Load YAML configuration file.

**Parameters**:

-   `file_path` (str): Path to YAML file

**Returns**: Parsed YAML data as dictionary

### `export_to_csv(data: list[dict], output_path: str) -> None`

Export data to CSV file.

**Parameters**:

-   `data` (list[dict]): Data to export
-   `output_path` (str): Output file path

## 🔧 Configuration

### Settings

Key configuration options in `judex/settings.py`:

```python
# Database configuration
DATABASE_PATH = "judex.db"

# Scraping settings
DOWNLOAD_DELAY = 2.0
CONCURRENT_REQUESTS = 1
AUTOTHROTTLE_ENABLED = True

# Pipeline configuration
ITEM_PIPELINES = {
    "judex.pydantic_pipeline.PydanticValidationPipeline": 200,
    "judex.pipelines.DatabasePipeline": 300,
}

# Selenium settings
SELENIUM_DRIVER_NAME = "chrome"
SELENIUM_DRIVER_ARGUMENTS = [
    "--headless",
    "--incognito",
    "--window-size=920,600",
]
```

## 📝 Examples

### Basic Usage

```python
from judex.core import JudexScraper

# Initialize scraper
scraper = JudexScraper(
    output_dir="output",
    db_path="judex.db",
    skip_existing=True
)

# Scrape ADI cases
scraper.scrape("ADI", "[1234, 5678, 9012]")
```

### Custom Validation

```python
from judex.models import STFCaseModel
from pydantic import ValidationError

# Validate data
try:
    case = STFCaseModel(**data)
    print(f"Valid case: {case.numero_unico}")
except ValidationError as e:
    print(f"Validation errors: {e.errors()}")
```

### Database Queries

```python
import sqlite3

# Query cases
with sqlite3.connect("judex.db") as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT numero_unico, relator, data_protocolo
        FROM processos
        WHERE classe = 'ADI'
    """)
    results = cursor.fetchall()
```

This API reference provides comprehensive documentation for all public interfaces in the judex system, enabling developers to effectively use and extend the functionality.
