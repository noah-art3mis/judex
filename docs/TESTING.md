# judex Testing Guide

## 🧪 Testing Overview

judex uses a comprehensive testing strategy with 86+ unit tests covering all major components. The testing framework ensures data integrity, type safety, and system reliability.

## 📊 Test Coverage

**Current Status**: 89.5% pass rate (77/86 tests passing)

| Component              | Tests | Status   | Coverage            |
| ---------------------- | ----- | -------- | ------------------- |
| **Models**             | 24    | ✅ 100%  | Pydantic validation |
| **Types**              | 20    | ✅ 100%  | Type validation     |
| **Database**           | 13    | ✅ 100%  | Database operations |
| **Pipeline**           | 8     | ⚠️ 12.5% | Data validation     |
| **Spider Integration** | 8     | ⚠️ 87.5% | Web scraping        |
| **Edge Cases**         | 13    | ✅ 100%  | Error handling      |

## 🚀 Running Tests

### Basic Test Execution

```bash
# Run all tests
uv run python -m pytest

# Run with verbose output
uv run python -m pytest -v

# Run specific test file
uv run python -m pytest tests/test_models.py -v

# Run specific test class
uv run python -m pytest tests/test_models.py::TestSTFCaseModel -v

# Run specific test method
uv run python -m pytest tests/test_models.py::TestSTFCaseModel::test_minimal_valid_case -v
```

### Test Categories

```bash
# Model tests (Pydantic validation)
uv run python -m pytest tests/test_models.py -v

# Type validation tests
uv run python -m pytest tests/test_types.py -v

# Database operation tests
uv run python -m pytest tests/test_database_standalone.py -v

# Pipeline tests (data validation)
uv run python -m pytest tests/test_pydantic_pipeline.py -v

# Spider integration tests
uv run python -m pytest tests/test_spider_integration.py -v
```

### Coverage Analysis

```bash
# Run with coverage
uv run python -m pytest --cov=judex --cov-report=html

# Coverage report
uv run python -m pytest --cov=judex --cov-report=term-missing

# Coverage threshold
uv run python -m pytest --cov=judex --cov-fail-under=80
```

## 📋 Test Structure

### Test Organization

```
tests/
├── test_models.py              # Pydantic model tests
├── test_types.py               # Type validation tests
├── test_pydantic_pipeline.py   # Pipeline validation tests
├── test_spider_integration.py  # Spider integration tests
└── test_database_standalone.py # Database operation tests
```

### Test Naming Convention

```python
# Test class naming
class TestSTFCaseModel:          # Tests for STFCaseModel
class TestPydanticValidationPipeline:  # Tests for pipeline
class TestStfSpiderIntegration:   # Tests for spider integration

# Test method naming
def test_minimal_valid_case(self):     # Test minimal valid case
def test_liminar_conversion(self):     # Test liminar field conversion
def test_field_mapping_validation(self): # Test field mapping
```

## 🔧 Test Categories

### 1. Model Tests (`test_models.py`)

**Purpose**: Test Pydantic model validation and data integrity

**Key Test Areas**:

-   Model creation and validation
-   Field type checking
-   Enum validation
-   Field mapping (scraping → database)
-   Type conversion (lists → JSON, booleans → integers)
-   Error handling and validation messages

**Example Tests**:

```python
def test_minimal_valid_case(self):
    """Test creating a minimal valid case"""
    data = {
        "processo_id": 123,
        "incidente": 456,
        "classe": "ADI",
    }
    case = STFCaseModel(**data)
    assert case.processo_id == 123
    assert case.incidente == 456
    assert case.classe == "ADI"

def test_liminar_conversion(self):
    """Test liminar field conversion from list to int"""
    data = {
        "processo_id": 123,
        "incidente": 456,
        "classe": "ADI",
        "liminar": ["liminar1", "liminar2"],
    }
    case = STFCaseModel(**data)
    assert case.liminar == 1
```

### 2. Type Tests (`test_types.py`)

**Purpose**: Test type validation utilities and case type management

**Key Test Areas**:

-   Case type validation
-   Enum consistency
-   Error message generation
-   Edge cases and error handling

**Example Tests**:

```python
def test_valid_case_types(self):
    """Test that all valid case types are accepted"""
    valid_cases = ["ADI", "ADPF", "HC", "MS", "RE"]
    for case in valid_cases:
        assert CaseType(case) == case

def test_invalid_case_type_validation(self):
    """Test validation of invalid case types"""
    with pytest.raises(ValidationError) as exc_info:
        CaseTypeValidator(classe="INVALID")

    error_msg = str(exc_info.value)
    assert "Invalid case type" in error_msg
    assert "ADI" in error_msg
```

### 3. Database Tests (`test_database_standalone.py`)

**Purpose**: Test database operations and data persistence

**Key Test Areas**:

-   Database initialization
-   Data saving and retrieval
-   Foreign key relationships
-   Data integrity constraints
-   Unicode and special character handling

**Example Tests**:

```python
def test_database_initialization(self):
    """Test database initialization with proper schema"""
    # Use temporary database for testing
    import tempfile
    import os

    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    try:
        init_database(temp_db.name)
        # Verify tables exist and have correct structure
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)

def test_processo_write(self):
    """Test saving processo data to database"""
    # Use temporary database for testing
    import tempfile
    import os

    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    try:
        data = sample_processo_data()
        success = processo_write(temp_db.name, data)
        assert success is True
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)
```

### 4. Pipeline Tests (`test_pydantic_pipeline.py`)

**Purpose**: Test data validation pipeline

**Key Test Areas**:

-   Pipeline initialization
-   Data validation flow
-   Error handling
-   Database integration
-   Field mapping validation

**Example Tests**:

```python
def test_valid_item_processing(self, mock_save):
    """Test processing a valid item"""
    mock_save.return_value = True

    item_data = {
        "processo_id": 123,
        "incidente": 456,
        "classe": "ADI",
    }

    with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
        mock_adapter.return_value = item_data

        result = self.pipeline.process_item(mock_item, self.mock_spider)
        assert result == mock_item
        mock_save.assert_called_once()
```

### 5. Spider Integration Tests (`test_spider_integration.py`)

**Purpose**: Test web scraping integration

**Key Test Areas**:

-   Spider initialization
-   Request generation
-   Data extraction
-   Error handling (CAPTCHA, 403, 502)
-   Selenium integration

**Example Tests**:

```python
def test_spider_initialization(self):
    """Test spider initialization with Pydantic integration"""
    spider = StfSpider(
        classe="ADI",
        processos="[123, 456]",
        skip_existing=False,
        retry_failed=False,
    )
    assert spider.name == "stf"
    assert spider.classe == CaseType.ADI
    assert spider.numeros == [123, 456]

def test_parse_main_page_selenium_success(self):
    """Test successful parsing of main page with all extractors"""
    # Mock all extractors and test successful parsing
```

## 🛠 Test Utilities

### Mocking Strategies

#### Database Mocking

```python
@patch("judex.pydantic_pipeline.processo_write")
def test_database_save_failure(self, mock_save):
    """Test handling of database save failures"""
    mock_save.return_value = False  # Simulate save failure
    # Test error handling
```

#### Selenium Mocking

```python
def test_get_element_by_id(self):
    """Test get_element_by_id method"""
    mock_driver = Mock()
    mock_element = Mock()
    mock_element.get_attribute.return_value = "test_value"
    mock_driver.find_element.return_value = mock_element

    with patch("judex.spiders.stf.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.return_value = None

        result = self.spider.get_element_by_id(mock_driver, "test_id")
        assert result == "test_value"
```

#### ItemAdapter Mocking

```python
with patch("judex.pydantic_pipeline.ItemAdapter") as mock_adapter:
    mock_adapter.return_value = item_data
    # Test pipeline processing
```

### Test Data Generation

#### Sample Data

```python
def sample_processo_data():
    """Generate sample processo data for testing"""
    return {
        "processo_id": 123,
        "incidente": 456,
        "numero_unico": "ADI 123456",
        "classe": "ADI",
        "tipo_processo": "Eletrônico",
        "liminar": 1,
        "relator": "Ministro Silva",
        # ... other fields
    }
```

#### Edge Case Data

```python
def test_edge_cases(self):
    """Test edge cases and error conditions"""
    # Test None input
    assert is_valid_case_type(None) is False

    # Test empty string
    assert is_valid_case_type("") is False

    # Test whitespace strings
    assert is_valid_case_type(" ") is False
```

## 🐛 Debugging Tests

### Verbose Output

```bash
# Show detailed test output
uv run python -m pytest -v -s

# Show print statements
uv run python -m pytest -s

# Show local variables on failure
uv run python -m pytest --tb=long
```

### Test Debugging

```python
# Add debug prints in tests
def test_debug_example(self):
    print(f"Debug: Testing with data: {data}")
    result = function_under_test(data)
    print(f"Debug: Result: {result}")
    assert result == expected
```

### Isolating Failing Tests

```bash
# Run only failing tests
uv run python -m pytest tests/test_pydantic_pipeline.py::TestPydanticValidationPipeline::test_invalid_item_validation_error -v

# Run with specific markers
uv run python -m pytest -m "not slow" -v
```

## 📈 Test Metrics

### Coverage Goals

-   **Overall Coverage**: > 80%
-   **Model Coverage**: > 95%
-   **Pipeline Coverage**: > 85%
-   **Database Coverage**: > 90%

### Performance Benchmarks

-   **Model Validation**: < 10ms per case
-   **Database Operations**: < 100ms per batch
-   **Pipeline Processing**: < 50ms per item

### Quality Metrics

-   **Test Reliability**: > 95% pass rate
-   **Error Detection**: 100% of known issues covered
-   **Edge Case Coverage**: > 90% of edge cases tested

## 🔧 Continuous Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
    test:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v3
            - uses: actions/setup-python@v4
              with:
                  python-version: '3.10'
            - run: uv sync
            - run: uv run python -m pytest --cov=judex --cov-report=xml
            - uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
    - repo: local
      hooks:
          - id: pytest
            name: pytest
            entry: uv run python -m pytest
            language: system
            pass_filenames: false
            always_run: true
```

## 🚀 Best Practices

### Test Writing Guidelines

1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: Each test should test one thing
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Edge Cases**: Include boundary conditions and error cases

### Test Maintenance

1. **Regular Updates**: Update tests when code changes
2. **Refactoring**: Refactor tests to match code changes
3. **Documentation**: Document complex test scenarios
4. **Performance**: Monitor test execution time

### Test Data Management

1. **Isolation**: Each test should be independent
2. **Cleanup**: Clean up test data after tests
3. **Fixtures**: Use pytest fixtures for common setup
4. **Factories**: Use factory functions for test data generation

This testing guide provides comprehensive coverage of the judex testing strategy, enabling developers to write, run, and maintain high-quality tests for the system.
