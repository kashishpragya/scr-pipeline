# SCR PDF Acquisition Module

**Independent module for downloading Supreme Court Reports PDFs from official sources.**

This module is separate from extraction and handles ONLY:
- Discovery of official PDF sources
- Safe downloading with validation
- Placing files in `data/raw_pdfs/<YEAR>/`

## Purpose

The SCR extraction pipeline expects PDFs to be available locally. This acquisition module handles obtaining them from official sources.

**Key Principle:** No data inference, no assumptions. Only download and validate PDFs.

## Architecture

```
src/acquisition/
├── __init__.py
├── scr_pdf_fetcher.py      # Download PDFs with retry logic
├── scr_pdf_validator.py    # Validate downloaded files
├── run_acquisition.py      # CLI and orchestration
└── source_config.py        # Source registration and discovery
```

## Usage

### Basic Acquisition

```bash
# Acquire PDFs for year 2010
python -m src.acquisition.run_acquisition --year 2010
```

### Options

```bash
# Dry run (simulate without downloading)
python -m src.acquisition.run_acquisition --year 2010 --dry-run

# Force re-download even if PDFs exist
python -m src.acquisition.run_acquisition --year 2010 --force-redownload

# Show registered sources
python -m src.acquisition.run_acquisition --show-sources
```

## Workflow

### Phase 0: Setup
- Initialize target directory: `data/raw_pdfs/<YEAR>/`
- Verify logging is configured

### Phase 1: Discover Sources
- Get registered PDF URLs for the year
- Log number of sources found

### Phase 2: Download & Validate
- Download each PDF with retry logic
- Validate file integrity (size, magic number, readable)
- Skip existing files (idempotent)
- Log success/failure for each file

## Configuration

### Download Settings

Edit [config/settings.py](../config/settings.py):

```python
# Timeout for individual downloads (seconds)
PDF_DOWNLOAD_TIMEOUT = 300

# Number of retry attempts
PDF_DOWNLOAD_RETRIES = 3

# File size bounds
MAX_PDF_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MIN_PDF_FILE_SIZE = 10 * 1024  # 10 KB

# Clean up partial downloads on failure
CLEANUP_FAILED_DOWNLOADS = True
```

### Registering Sources

#### Option 1: Programmatic Registration

```python
from src.acquisition.scr_pdf_fetcher import PDFSourceProvider

# Register URLs for a year
urls = [
    "https://official-source.gov.in/scr_2010_vol_1.pdf",
    "https://official-source.gov.in/scr_2010_vol_2.pdf",
]

PDFSourceProvider.register_source(2010, urls)
```

#### Option 2: Configuration File

(To be implemented based on your source discovery mechanism)

#### Option 3: Source Discovery

Implement discovery in `source_config.py`:

```python
def register_official_sources():
    """Discover and register official sources."""
    
    for year in range(2010, 2024):
        # Query official database or API
        urls = discover_scr_pdfs_for_year(year)
        
        # Register sources
        PDFSourceProvider.register_source(year, urls)
```

## Validation

Each downloaded PDF is validated:

1. **File Exists** - File is actually created
2. **Extension** - Must have `.pdf` extension
3. **File Size** - Within configured bounds
4. **PDF Magic Number** - Header must be `%PDF`
5. **Readable** - Can be opened and read by pdfplumber

Failed files are logged and skipped.

## Idempotency

- If a PDF already exists, it's skipped (not re-downloaded)
- Existing files are validated (checksums computed)
- Re-run safely without duplication
- Use `--force-redownload` to override

## Logging

### Main Log

`logs/pipeline.log`:
- Each phase start/end
- Download progress
- Validation results
- Overall statistics

### Failure Log

`logs/failures.log`:
- HTTP errors
- Validation failures
- Download timeouts
- File corruption

### Execution Log

`logs/acquisition_log_<YEAR>.json`:
- Structured execution report
- Statistics for each phase
- Timing information
- Error details

## Integration with Extraction

Once PDFs are acquired, run the extraction pipeline:

```bash
# Acquisition (this module)
python -m src.acquisition.run_acquisition --year 2010

# Extraction (existing pipeline)
python -m src.pipeline.run_scr_pipeline --year 2010
```

Both commands work independently.

## Error Handling

### Network Errors
- Automatic retry with exponential backoff
- Timeout detection
- Connection error recovery

### Validation Errors
- Partial downloads are deleted
- Corrupted files are logged and skipped
- File size anomalies are caught

### Logging
- Every error is logged with context
- Failed downloads include reason
- No silent failures

## Extending Acquisition

### Adding a New Source

1. **Verify the source is official**
   - Check domain and SSL certificate
   - Confirm PDF availability
   - Test URL accessibility

2. **Register the source**
   ```python
   PDFSourceProvider.register_source(2010, [url])
   ```

3. **Test with dry-run**
   ```bash
   python -m src.acquisition.run_acquisition --year 2010 --dry-run
   ```

4. **Verify output**
   ```bash
   ls -lh data/raw_pdfs/2010/
   ```

### Browser Automation

For sources requiring JavaScript rendering:

```python
# Future enhancement using Selenium/Playwright
from selenium import webdriver

def discover_with_browser(year: int):
    driver = webdriver.Chrome()
    # Navigate to source
    # Interact with page
    # Extract PDF URLs
    # Close driver
```

### API Integration

For sources with REST APIs:

```python
def discover_from_api(year: int):
    response = requests.get(
        f"https://api.official.gov.in/scr/{year}",
        headers={"Authorization": "Bearer TOKEN"}
    )
    return [pdf['url'] for pdf in response.json()['volumes']]
```

## Design Principles

### Conservative
- Only download from verified sources
- Validate all files completely
- Fail loudly on errors
- Never assume data correctness

### Defensive
- Retry with exponential backoff
- Timeout all network operations
- Clean up partial downloads
- Log every step

### Auditable
- Detailed logging
- Checksums for verification
- Execution reports
- Clear error messages

### Separated
- No extraction logic here
- No metadata inference
- No text parsing
- Pure download/validate

## Troubleshooting

### No sources registered

```
Error: No PDF sources registered for year 2010
```

**Solution:** Register sources using `PDFSourceProvider.register_source()`

### Download fails with timeout

**Solution:** Increase timeout in settings.py:
```python
PDF_DOWNLOAD_TIMEOUT = 600  # 10 minutes
```

### PDF validation fails

Check `logs/failures.log` for details:
- File size out of bounds?
- Invalid PDF header?
- Corrupted download?

### Permission denied

**Solution:** Check directory permissions:
```bash
chmod 755 data/raw_pdfs/
```

## Future Enhancements

- [ ] Web scraping for PDF discovery
- [ ] Browser automation for complex sources
- [ ] API integration for official databases
- [ ] Incremental updates (only new volumes)
- [ ] Mirror support (fallback sources)
- [ ] Batch downloading with progress bar
- [ ] S3/Cloud storage integration
- [ ] Scheduled downloads

## Audit Trail

Every acquisition operation creates an execution log:

`logs/acquisition_log_<YEAR>.json`

Example:
```json
{
  "year": 2010,
  "start_time": "2026-02-01T10:30:00",
  "end_time": "2026-02-01T10:35:42",
  "status": "success",
  "total_pdfs_acquired": 45,
  "total_pdfs_skipped": 3,
  "total_pdfs_failed": 0,
  "phases": {
    "phase_0": {"status": "complete"},
    "phase_1": {"sources_discovered": 48},
    "phase_2": {"pdfs_acquired": 45}
  }
}
```

## Contact & Support

For acquisition-specific issues:
- Check `logs/acquisition_log_<YEAR>.json`
- Review `logs/failures.log` for detailed errors
- Verify sources are registered and accessible
- Run `--dry-run` to simulate without downloading
