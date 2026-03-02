"""
TESTING - SCR Pipeline Test Suite

Complete guide to testing the SCR extraction pipeline.
"""

# ==================== TEST SUITE OVERVIEW ====================

## What is Tested

The SCR Pipeline includes comprehensive test coverage for:

1. **Unit Tests** (per-module)
   - Case splitting logic
   - Metadata extraction
   - Data normalization
   
2. **Integration Tests** (cross-module)
   - Full extraction workflow
   - Data preservation through pipeline
   - Error handling and recovery
   
3. **Edge Cases**
   - Empty inputs
   - Malformed data
   - Boundary conditions


## Test Structure

```
tests/
├── __init__.py                      # Test package
├── conftest.py                      # Pytest fixtures
├── test_scr_case_splitter.py       # Case splitting tests
├── test_scr_metadata_extractor.py  # Metadata extraction tests
├── test_normalizer.py               # Data normalization tests
└── test_integration.py              # End-to-end tests
```


# ==================== RUNNING TESTS ====================

## Prerequisites

```bash
pip install -r requirements.txt
```

Ensure pytest is installed (it's in requirements.txt):
- pytest==7.4.0
- pytest-cov==4.1.0


## Basic Usage

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_scr_case_splitter.py
```

### Run Specific Test Class
```bash
pytest tests/test_scr_case_splitter.py::TestCaseBoundaryDetection
```

### Run Specific Test
```bash
pytest tests/test_scr_case_splitter.py::TestCaseBoundaryDetection::test_all_caps_detection
```

### View Verbose Output
```bash
pytest -v
```

### Show Print Statements (Debugging)
```bash
pytest -s
```

### Stop After First Failure
```bash
pytest -x
```

### Run Last Failed Tests
```bash
pytest --lf
```

### Run Specific Marker
```bash
pytest -m "slow"    # Runs only slow tests
```


## Coverage Report

### Generate Coverage Report
```bash
pytest --cov=src tests/
```

### HTML Coverage Report
```bash
pytest --cov=src --cov-report=html tests/
open htmlcov/index.html    # macOS
start htmlcov/index.html   # Windows
```

### Coverage by Module
```bash
pytest --cov=src --cov-report=term-missing tests/
```


# ==================== TEST CATEGORIES ====================

## Case Splitter Tests (test_scr_case_splitter.py)

### TestCaseBoundaryDetection
- Tests detection of case title markers
- Tests CORAM/Bench brackets
- Tests "v." and "vs." patterns
- Tests non-boundary lines

### TestCaseSplitting
- Single case extraction
- Multiple case splitting
- Minimum length enforcement
- Ambiguous split tracking

### TestEdgeCases
- Empty text handling
- No case markers
- Mixed patterns
- Very long cases

**Run these tests:**
```bash
pytest tests/test_scr_case_splitter.py -v
```


## Metadata Extractor Tests (test_scr_metadata_extractor.py)

### TestCaseNameExtraction
- Simple case names
- Various separators (v., vs.)
- Missing case names
- Lowercase patterns

### TestJudgeExtraction
- [Coram: ...] format
- (Coram: ...) format
- Multiple judges
- No judges found

### TestActExtraction
- Named acts
- Abbreviations (IPC, CPC)
- No acts mentioned
- Acts with years

### TestSectionExtraction
- Section numbers
- Abbreviated references
- Constitution articles
- Subsections

**Run these tests:**
```bash
pytest tests/test_scr_metadata_extractor.py -v
```


## Normalizer Tests (test_normalizer.py)

### TestJudgeNormalization
- Honor titles removal
- Case standardization
- Parenthetical info removal
- Judge list normalization

### TestActNormalization
- IPC canonicalization
- CPC canonicalization
- Constitution normalization
- Unknown act handling

### TestDeduplication
- Judge deduplication
- Act deduplication
- Section deduplication
- Preserve order

**Run these tests:**
```bash
pytest tests/test_normalizer.py -v
```


## Integration Tests (test_integration.py)

### TestExtractionPipeline
- Full workflow: split → extract → normalize
- Case count preservation
- Minimal data handling

### TestCaseFlowDataIntegrity
- Case name preservation
- Judge information preservation
- Legal references preservation

### TestErrorRecovery
- Continuation on single case error
- Normalization of invalid data

### TestOutputGeneration
- JSON validity
- Schema validation
- Required fields presence

**Run these tests:**
```bash
pytest tests/test_integration.py -v
```


# ==================== FIXTURES ====================

## Provided Fixtures (conftest.py)

All fixtures are in `tests/conftest.py`:

### temp_workspace
```python
@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing."""
```
Creates a temporary directory structure for isolated testing.

Usage:
```python
def test_something(temp_workspace):
    # temp_workspace is a Path object pointing to temp dir
    assert (temp_workspace / "data").exists()
```

### sample_case_text
```python
@pytest.fixture
def sample_case_text():
    """Provide sample SCR case text for testing."""
```
Provides realistic sample case text with case name, judges, acts, sections.

### sample_multi_case_text
Provides text with multiple cases for splitting tests.

### schema_valid_case
Provides a valid case dictionary matching the output schema.

### schema_invalid_case
Provides an invalid case dictionary for negative testing.

### sample_case_data_for_normalization
Provides case data with duplicates and formatting issues for normalization tests.


# ==================== WRITING NEW TESTS ====================

## Test Template

```python
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.your_module import YourClass


class TestYourFeature:
    """Test description."""
    
    def setup_method(self):
        """Setup before each test."""
        self.instance = YourClass()
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.instance.method()
        assert result is not None
    
    def test_with_fixture(self, sample_case_text):
        """Test using a fixture."""
        result = self.instance.process(sample_case_text)
        assert len(result) > 0
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            self.instance.process_invalid_data()
```

## Best Practices

1. **One assertion per test method** (or related assertions)
2. **Use descriptive names** that explain what's being tested
3. **Use fixtures** for common setup
4. **Test both success and failure cases**
5. **Use parametrize for similar tests**
   ```python
   @pytest.mark.parametrize("input,expected", [
       ("abc", 3),
       ("hello", 5),
   ])
   def test_length(input, expected):
       assert len(input) == expected
   ```


# ==================== CONTINUOUS INTEGRATION ====================

## GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest --cov=src
      - uses: codecov/codecov-action@v2
```


# ==================== TROUBLESHOOTING TESTS ====================

## Common Issues

### ImportError: No module named 'src'
**Solution:** Run pytest from the project root
```bash
cd /path/to/scr_pipeline
pytest
```

### ModuleNotFoundError in tests
**Solution:** Ensure conftest.py adds parent to path
```python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Fixture not found
**Solution:** Ensure fixture is in conftest.py or imported
```python
from tests.conftest import fixture_name
```

### Temporary files not cleaned up
**Solution:** Use tmp_path fixture (automatic cleanup)
```python
def test_something(tmp_path):  # Automatic cleanup
    pass
```

### Tests are slow
**Solution:** Run specific tests or use pytest-xdist for parallel execution
```bash
pip install pytest-xdist
pytest -n auto
```


# ==================== QUALITY GATES ====================

## Minimum Coverage Requirements

- **Overall**: 70% coverage
- **Core modules**: 80% coverage
  - scr_case_splitter.py
  - scr_metadata_extractor.py
  - normalizer.py

## Check Coverage

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=70
```

## Coverage Report Locations

- **Terminal**: Direct output from pytest
- **HTML**: `htmlcov/index.html` (generated with --cov-report=html)
- **XML**: `coverage.xml` (for CI/CD tools)


# ==================== RUNNING TESTS IN CI/CD ====================

Add to your CI/CD pipeline:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=src --cov-report=term-missing --cov-report=xml tests/

# Check coverage threshold
pytest --cov=src --cov-fail-under=70 tests/

# Generate HTML report
pytest --cov=src --cov-report=html tests/
```
