# Quick Reference: What's Actually Happening

## Direct Answers (TL;DR)

| Question | Answer | Evidence |
|----------|--------|----------|
| **Is the pipeline scraping live SCI data?** | **NO** | ❌ `source_config.py` line 34-36: All PDF URLs commented out |
| **Is Selenium being executed?** | **NO** | ❌ `SCIJudgementDateClient` exists but never imported/called |
| **Are real PDF downloads happening?** | **NO** | ✅ `src/acquisition/run_acquisition.py` line 98: Exits with "No PDF sources registered" |
| **Are tests using real PDFs?** | **NO** | ✅ `tests/conftest.py` line 30: Hard-coded sample text fixture |
| **Are network calls made during pytest?** | **NO** | ✅ No `requests` or `selenium` imported in any test file |
| **Is CAPTCHA handling automated?** | **NO** | ❌ `sci_judgement_date_client.py` line 59: `input("After solving CAPTCHA press ENTER...")` |

---

## What Actually Runs When

### `pytest` (77 passing tests)
```
conftest.py fixtures (hard-coded text strings)
    ↓
test files import modules (no network)
    ↓
Tests run on in-memory fixture data
    ↓
✅ RESULT: Tests pass, zero network activity
```

### `python -m src.acquisition.run_acquisition --year 2010`
```
main() → AcquisitionPipeline(2010)
    ↓
phase_1_discover_sources()
    → PDFSourceProvider.get_sources_for_year(2010)
    → Returns: [] (empty, URLs commented out)
    
if not sources:  ← TRUE (empty list)
    → Log error: "No PDF sources registered"
    → Return False
    
❌ RESULT: Exits immediately, zero network activity
```

### `python -m src.pipeline.run_scr_pipeline --year 2010`
```
from src.extraction.pdf_text_extractor import PDFTextExtractor
                                        ↑ DOES NOT EXIST

❌ RESULT: ImportError at module load time
Cannot execute this module
```

### Manual `SCIJudgementDateClient()` (if called)
```
__init__():
    → webdriver.Chrome() ← Launches browser

open_page():
    → self.driver.get("https://www.sci.gov.in/judgements-judgement-date/")
    → NETWORK CALL #1

fill_dates():
    → JavaScript execution in browser

click_search():
    → print("⚠️ Solve CAPTCHA manually in browser.")
    → input("After solving CAPTCHA press ENTER...")
    → BLOCKS waiting for human input
    → After input, makes network call for search
    → NETWORK CALL #2

⚠️ RESULT: Manual intervention required, not automated
Not integrated into main pipeline
```

---

## Module Map: What Uses What

### Tests (conftest.py + test_*.py)
```
conftest.py (fixtures only)
├── sample_case_text → hard-coded string
├── sample_multi_case_text → hard-coded string
├── schema_valid_case → hard-coded dict
└── [6 other fixtures] → all hard-coded

test_integration.py, test_normalizer.py, etc.
├── Uses: SCRCaseSplitter (pure text logic)
├── Uses: SCRMetadataExtractor (regex patterns)
├── Uses: Normalizer (data cleaning)
└── ✅ ZERO network calls

NOT imported by tests:
├── ❌ AcquisitionPipeline
├── ❌ SCRPDFFetcher
├── ❌ PDFValidator
├── ❌ SCIJudgementDateClient
├── ❌ requests library
└── ❌ selenium library
```

### run_acquisition.py Entry Point
```
run_acquisition.py:
├── Imports: PDFSourceProvider
├── Imports: PDFValidator
├── Imports: AcquisitionPipeline
├── On execution:
│   ├── Phase 0: mkdir (no network)
│   ├── Phase 1: get_sources() → []
│   │   ├── Checks: PDFSourceProvider.KNOWN_SOURCES[2010]
│   │   ├── Source: source_config.py register_all_known_sources()
│   │   ├── Result: Empty (URLs commented)
│   │   └── Exit: No sources, return False
│   └── Never reaches Phase 2 (download)
└── ✅ ZERO network calls
```

### source_config.py (Configuration)
```
register_all_known_sources():
├── sources_2010 = [
│   ├── # "https://main.sci.gov.in/..." ← COMMENTED OUT
│   └── # "https://main.sci.gov.in/..." ← COMMENTED OUT
├── if sources_2010:  ← FALSE (empty list)
│   └── PDFSourceProvider.register_source(2010, sources_2010)
│       ↑ NOT EXECUTED
└── Result: KNOWN_SOURCES[2010] = []
```

### scr_pdf_fetcher.py (IF sources existed)
```
download_pdf():
├── NOT CALLED (sources empty)
├── But IF called, would:
└── requests.get(url)  ← NETWORK CALL HERE
    ├── Validates response
    ├── Writes to disk
    └── Validates PDF format
```

### sci_judgement_date_client.py (Unused)
```
SCIJudgementDateClient():
├── Instantiation: webdriver.Chrome() ← Launches browser
├── open_page(): requests to https://www.sci.gov.in/...  ← NETWORK
├── click_search(): 
│   ├── Manual input() for CAPTCHA
│   └── Network request after CAPTCHA solved
└── ⚠️ NOT USED ANYWHERE IN PIPELINE
```

---

## Where Network Calls Could Happen (But Don't)

```
IF sources_2010 had URLs:
    run_acquisition.py → phase_2_acquire_pdfs()
        → SCRPDFFetcher.fetch_pdf(url)
            → requests.get(url)  ← HERE
                → Download PDF
                    → Save to disk/raw_pdfs/2010/
                        → PDF would be on disk

THEN in run_scr_pipeline.py:
    → phase_2_pdf_text_extraction()
        → PDFTextExtractor().extract_text_from_pdf(pdf_path)
            → pdfplumber.open(pdf_path)  ← Read from disk (NO network)
                → Extract text from PDF
                    → phase_3_case_splitting()
                        → Metadata extraction
                        → Normalization
                        → JSON output
```

**Current Status**: ❌ Never reaches download step (sources empty)

---

## The Three Broken Paths

### Path 1: run_acquisition.py
```
Status: ❌ BROKEN - can't download anything
Reason: No sources registered
Error: "No PDF sources registered for year 2010"
Fix: Add URLs to sources_2010 in source_config.py
```

### Path 2: run_scr_pipeline.py
```
Status: ❌ BROKEN - can't even import
Reason: PDFTextExtractor class doesn't exist
Error: ImportError: cannot import name 'PDFTextExtractor'
Fix: Define class or change import
```

### Path 3: sci_judgement_date_client.py
```
Status: ⚠️ DISCONNECTED - exists but not used
Reason: Manual CAPTCHA intervention required
Limitation: Can't be automated
Current: Not integrated into main pipeline
```

---

## Data Sources for Each Scenario

| Scenario | Text Source | Mode | Network? | Automated? |
|----------|-------------|------|----------|-----------|
| **pytest** | conftest.py fixtures | Testing | ❌ No | ✅ Yes |
| **run_acquisition** | (Would be SCI website) | Scraping | ❌ No (fails before) | ⚠️ Manual CAPTCHA |
| **run_scr_pipeline** | (Would be PDFs) | Processing | ❌ No (fails at import) | ❌ No |
| **Manual browser** | SCI website | Scraping | ✅ Yes | ❌ No (manual CAPTCHA) |

---

## Actual Execution Flow (Simplest Path)

This is what ACTUALLY happens end-to-end:

```
User runs: pytest

Step 1: pytest loads conftest.py
        ↓ Defines fixtures (hard-coded strings)

Step 2: pytest discovers test_*.py files
        ↓ Imports test modules

Step 3: Tests run:
        sample_case_text (fixture) 
             ↓
        SCRCaseSplitter.split_volume_text(sample_case_text)
             ↓ (String pattern matching, NO I/O)
        SCRMetadataExtractor.extract_metadata(...)
             ↓ (Regex on string, NO I/O)
        Normalizer.normalize_cases(...)
             ↓ (Dict transformation, NO I/O)
        validate_case_schema(...)
             ↓ (Dict validation, NO I/O)

Step 4: Assertions pass/fail

Step 5: pytest reports:
        77 passed, 6 failed
        
Execution time: ~1-5 seconds
Network calls: ZERO
File I/O: Only to temp_workspace
Real PDFs used: ZERO
Selenium executed: NO
CAPTCHA encountered: NO
```

---

## The Missing Piece

To make the pipeline work end-to-end, you need:

### Option A: Use Real SCI Sources
```python
# In source_config.py, uncomment and populate:
sources_2010 = [
    "https://official.sci.gov.in/real/pdf/url/scr_vol_1.pdf",
    "https://official.sci.gov.in/real/pdf/url/scr_vol_2.pdf",
]
# Then would download via requests
```

### Option B: Place PDFs Manually
```bash
# Create directory
mkdir -p data/raw_pdfs/2010

# Place PDF files manually or via external download tool
cp ~/Downloads/scr_*.pdf data/raw_pdfs/2010/

# Then run pipeline
python -m src.pipeline.run_scr_pipeline --year 2010
```

### Option C: Use Browser Automation
```python
# Requires:
from src.acquisition.sci_judgement_date_client import SCIJudgementDateClient

client = SCIJudgementDateClient()
client.open_page()
client.fill_dates("01-01-2010", "31-12-2010")
client.click_search()  # ← Manual CAPTCHA input required
links = client.extract_pdf_links()

# Then register URLs and continue
for url in links:
    PDFSourceProvider.register_source(2010, url)
```

But none of these are currently implemented/connected.

---

## Summary

- ✅ Code is well-structured and well-tested
- ✅ Tests work with hard-coded fixtures (77/83 passing)
- ❌ Pipeline cannot run end-to-end (missing pieces)
- ❌ No data sources configured
- ❌ Code has import error (PDFTextExtractor)
- ⚠️ Browser automation not integrated
- ⚠️ CAPTCHA solving manual (can't automate)

**Network Activity During pytest**: ZERO ✅
**Network Activity During run_acquisition**: ZERO ✅ (fails before trying)
**Network Activity During run_scr_pipeline**: FAILS before reaching network logic ❌
