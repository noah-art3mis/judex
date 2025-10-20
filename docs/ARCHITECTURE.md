# judex Architecture Documentation

## 🏗 System Architecture Overview

judex is a sophisticated web scraping system designed to extract and validate data from the Brazilian Supreme Court (STF) portal. The architecture emphasizes data integrity, type safety, and maintainability through the use of Pydantic for data validation.

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        judex System                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Input     │  │  Processing │  │   Output    │            │
│  │   Layer     │  │    Layer     │  │   Layer     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Component Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   STF Portal    │───▶│   Scrapy Spider  │───▶│  Pydantic       │
│                 │    │                  │    │  Validation     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Data Pipeline   │───▶│   SQLite DB     │
                       │                  │    │                 │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Export Layer   │    │   Analytics     │
                       │   (CSV/JSON)     │    │   & Reports     │
                       └──────────────────┘    └─────────────────┘
```

## 🔧 Core Components

### 1. Web Scraping Layer

#### `StfSpider` (`judex/spiders/stf.py`)

**Purpose**: Extracts data from STF portal using Selenium WebDriver

**Key Features**:

-   Selenium-based dynamic content handling
-   CAPTCHA and error detection
-   Robust error handling and retry logic
-   Database-aware skipping of existing data

**Architecture**:

```python
class StfSpider(scrapy.Spider):
    def start_requests(self) -> Iterator[scrapy.Request]
    def parse_main_page_selenium(self, response: Response) -> Iterator[STFCaseItem]
    def get_element_by_id(self, driver: WebDriver, id: str) -> str
    def get_element_by_xpath(self, driver: WebDriver, xpath: str) -> str
    def clean_text(self, html_text: str) -> str | None
```

**Data Flow**:

```
STF Portal → Selenium WebDriver → BeautifulSoup → Raw Data Dictionary
```

### 2. Data Validation Layer

#### `STFCaseModel` (`judex/models.py`)

**Purpose**: Pydantic models for data validation and type safety

**Key Features**:

-   Runtime type checking
-   Automatic field mapping (scraping → database)
-   Type conversion (lists → JSON, booleans → integers)
-   Comprehensive validation rules

**Model Hierarchy**:

```python
STFCaseModel (Main Model)
├── CaseType (Enum)
├── ProcessType (Enum)
├── Parte (Sub-model)
├── Andamento (Sub-model)
├── Decisao (Sub-model)
├── Deslocamento (Sub-model)
├── Peticao (Sub-model)
├── Recurso (Sub-model)
├── Pauta (Sub-model)
└── Sessao (Sub-model)
```

**Field Mapping**:

```python
# Scraping field names → Database field names
"index" → "index_num"
"liminar" (list) → "liminar" (int)
"assuntos" (list) → "assuntos" (JSON string)
```

### 3. Pipeline Layer

#### `PydanticValidationPipeline` (`judex/pydantic_pipeline.py`)

**Purpose**: Validates scraped data using Pydantic models

**Key Features**:

-   Automatic data validation
-   Type conversion and field mapping
-   Error logging and handling
-   Database integration

**Pipeline Flow**:

```
Raw Item → ItemAdapter → Pydantic Validation → Database Save → Return Item
```

#### `DatabasePipeline` (`judex/pipelines.py`)

**Purpose**: Saves validated data to SQLite database

**Key Features**:

-   Normalized table structure
-   Foreign key relationships
-   Data integrity constraints
-   Batch operations

### 4. Database Layer

#### Database Schema (`judex/database.py`)

**Purpose**: Structured data storage with normalized tables

**Table Structure**:

```sql
-- Main table
processos (
    numero_unico TEXT PRIMARY KEY,
    incidente INTEGER UNIQUE,
    processo_id INTEGER UNIQUE,
    classe TEXT CHECK (...),
    tipo_processo TEXT CHECK (...),
    liminar INT CHECK (liminar IN (0, 1)),
    -- ... other fields
)

-- Normalized tables
partes (numero_unico, _index, tipo, nome)
andamentos (numero_unico, index_num, data, nome, complemento, julgador)
decisoes (numero_unico, index_num, data, nome, julgador, complemento, link)
deslocamentos (numero_unico, index_num, data_enviado, data_recebido, ...)
peticoes (numero_unico, index_num, data, tipo, autor, ...)
recursos (numero_unico, index_num, data, nome, julgador, ...)
pautas (numero_unico, index_num, data, nome, complemento, relator)
```

### 5. Type System

#### `types.py`

**Purpose**: Type validation and case type management

**Key Features**:

-   STF case type validation
-   Enum consistency checking
-   Error message generation
-   Integration with Pydantic models

## 🔄 Data Flow Architecture

### 1. Scraping Flow

```
User Request → Spider Initialization → Database Check → Request Generation
     ↓
Selenium WebDriver → STF Portal → HTML Content → BeautifulSoup Parsing
     ↓
Raw Data Extraction → Field Mapping → Data Dictionary → Pipeline
```

### 2. Validation Flow

```
Raw Data → ItemAdapter → Pydantic Model → Field Validation → Type Conversion
     ↓
Validated Data → Database Model → SQLite Storage → Success/Error Response
```

### 3. Error Handling Flow

```
Error Detection → Error Classification → Logging → Recovery Strategy
     ↓
CAPTCHA → Retry with delay
403/502 → Skip and log
Validation Error → Log and continue
Database Error → Rollback and retry
```

## 🛡 Security and Reliability

### Error Handling Strategy

1. **Network Errors**: Automatic retry with exponential backoff
2. **CAPTCHA Detection**: Skip and log for manual intervention
3. **Validation Errors**: Log detailed errors, continue processing
4. **Database Errors**: Transaction rollback, data integrity preservation

### Data Integrity

1. **Pydantic Validation**: Runtime type checking and validation
2. **Database Constraints**: Foreign keys and check constraints
3. **Transaction Management**: ACID compliance for data operations
4. **Field Mapping**: Automatic conversion between schemas

### Performance Optimization

1. **Database Caching**: Skip existing records
2. **Concurrent Processing**: Controlled parallelism
3. **Memory Management**: Streaming large datasets
4. **Resource Cleanup**: Proper WebDriver disposal

## 🔧 Configuration Architecture

### Settings Hierarchy

```
Command Line Args → Environment Variables → Settings File → Defaults
```

### Key Configuration Areas

1. **Scraping Settings**:

    - Download delays
    - Concurrency limits
    - Retry policies
    - User agents

2. **Database Settings**:

    - Connection strings
    - Pool sizes
    - Transaction timeouts
    - Backup strategies

3. **Validation Settings**:

    - Strict mode
    - Error handling
    - Field mapping rules
    - Type conversion policies

4. **Selenium Settings**:
    - Driver paths
    - Browser options
    - Timeout values
    - Proxy configurations

## 📊 Monitoring and Observability

### Logging Architecture

```
Application Logs → Structured Logging → Log Aggregation → Monitoring
```

### Key Metrics

1. **Scraping Metrics**:

    - Success/failure rates
    - Processing times
    - Data quality scores
    - Error frequencies

2. **Database Metrics**:

    - Query performance
    - Storage utilization
    - Connection pools
    - Transaction rates

3. **System Metrics**:
    - Memory usage
    - CPU utilization
    - Network I/O
    - Disk I/O

## 🚀 Deployment Architecture

### Development Environment

```
Local Machine → Python Environment → SQLite Database → File System
```

### Production Environment

```
Web Server → Application Server → Database Server → File Storage
     ↓
Load Balancer → Multiple Instances → Shared Database → Distributed Storage
```

### Scaling Considerations

1. **Horizontal Scaling**: Multiple spider instances
2. **Database Scaling**: Read replicas, connection pooling
3. **Storage Scaling**: Distributed file systems
4. **Monitoring Scaling**: Centralized logging and metrics

## 🔄 Integration Patterns

### External Integrations

1. **STF Portal**: Selenium-based scraping
2. **Database**: SQLite with potential PostgreSQL migration
3. **File System**: CSV/JSON export capabilities
4. **Monitoring**: Structured logging for observability

### Internal Integrations

1. **Scrapy → Pydantic**: Data validation pipeline
2. **Pydantic → Database**: Type-safe data persistence
3. **Database → Export**: Data transformation and export
4. **Configuration → All Components**: Centralized settings management

## 📈 Future Architecture Considerations

### Planned Enhancements

1. **Microservices**: Split into specialized services
2. **Message Queues**: Asynchronous processing
3. **Cloud Integration**: Cloud storage and databases
4. **API Layer**: RESTful API for data access
5. **Real-time Processing**: Streaming data pipelines

### Scalability Roadmap

1. **Phase 1**: Current monolithic architecture
2. **Phase 2**: Service separation and API layer
3. **Phase 3**: Microservices and containerization
4. **Phase 4**: Cloud-native and serverless components

This architecture provides a solid foundation for reliable, maintainable, and scalable web scraping operations while ensuring data integrity and type safety throughout the entire data processing pipeline.
