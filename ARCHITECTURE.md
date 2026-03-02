"""
SCR PIPELINE - COMPLETE SYSTEM ARCHITECTURE

A production-grade Supreme Court Reports PDF extraction and processing system.

This document provides a comprehensive overview of the entire system,
including the newly added acquisition module.
"""

# ==================== SYSTEM OVERVIEW ====================

"""
The SCR Pipeline is a complete system for acquiring and processing
Supreme Court Reports (SCR) PDFs.

COMPONENTS:

1. ACQUISITION (NEW)
   - Download SCR PDFs from official sources
   - Validate and place in data/raw_pdfs/
   
2. EXTRACTION (EXISTING)
   - Extract text from PDFs
   - Split into individual cases
   - Extract metadata (judges, acts, sections)
   - Normalize and clean
   - Generate JSON output

WORKFLOW:

   Official Sources
        ↓
   [Acquisition Module] ← NEW
        ↓
   data/raw_pdfs/<YEAR>/
        ↓
   [Extraction Pipeline]
        ↓
   data/output/scr_<YEAR>.json
"""

# ==================== FULL SYSTEM ARCHITECTURE ====================

"""
scr_pipeline/
│
├── config/
│   ├── settings.py       # Configuration (paths, options, timeouts)
│   └── constants.py      # Fixed values (schema, patterns)
│
├── src/
│   │
│   ├── acquisition/      (NEW MODULE - PDF ACQUISITION)
│   │   ├── scr_pdf_fetcher.py       # Download with retry
│   │   ├── scr_pdf_validator.py     # Validate files
│   │   ├── run_acquisition.py       # CLI & orchestration
│   │   └── source_config.py         # Source registry
│   │
│   ├── automation/       (EXISTING - PDF DISCOVERY)
│   │   └── scr_pdf_discovery.py     # Manual seeding, future automation
│   │
│   ├── extraction/       (EXISTING - CORE EXTRACTION)
│   │   ├── pdf_text_extractor.py    # PDF → text
│   │   ├── scr_case_splitter.py     # text → cases
│   │   └── scr_metadata_extractor.py # cases → metadata
│   │
│   ├── cleaning/         (EXISTING - DATA CLEANING)
│   │   └── normalizer.py            # Normalize & deduplicate
│   │
│   ├── pipeline/         (EXISTING - ORCHESTRATION)
│   │   └── run_scr_pipeline.py      # Main pipeline
│   │
│   └── utils.py          (SHARED - LOGGING & HELPERS)
│
├── data/
│   ├── raw_pdfs/         ← PDF acquisition target
│   │   └── <YEAR>/
│   ├── extracted_text/   ← Extraction intermediate
│   │   └── <YEAR>/
│   └── output/           ← Final JSON output
│       └── scr_<YEAR>.json
│
├── logs/
│   ├── pipeline.log
│   ├── failures.log
│   ├── execution_log_<YEAR>.json        (Extraction)
│   └── acquisition_log_<YEAR>.json      (Acquisition)
│
├── README.md                    # Main documentation
├── QUICK_START.md              # Quick start guide
├── ACQUISITION.md              # Acquisition module guide
├── ACQUISITION_SETUP.md        # Implementation patterns
├── ACQUISITION_SUMMARY.md      # Summary & status
├── requirements.txt            # Dependencies
└── ARCHITECTURE.md            # This file
"""

# ==================== ACQUISITION MODULE (NEW) ====================

"""
PURPOSE:
- Download SCR PDFs from official sources
- Validate and place in correct directories
- Enable independent PDF acquisition

KEY COMPONENTS:

1. scr_pdf_fetcher.py
   - PDFSourceProvider: Registry of official sources
   - SCRPDFFetcher: Download logic with retry
   - Features:
     * Configurable sources
     * Retry with exponential backoff
     * Timeout handling
     * File size validation

2. scr_pdf_validator.py
   - PDFValidator: Complete file validation
   - Checks:
     * File exists and readable
     * Correct extension
     * File size within bounds
     * PDF magic number (header)
     * pdfplumber can read it

3. run_acquisition.py
   - AcquisitionPipeline: Main orchestrator
   - Phases:
     * Phase 0: Setup
     * Phase 1: Discover sources
     * Phase 2: Download & validate
   - CLI with options:
     * --year: Required year
     * --dry-run: Simulate only
     * --force-redownload: Re-download existing
     * --show-sources: List registered sources

4. source_config.py
   - SourceRegistry: Examples for registering sources
   - Patterns for:
     * Hardcoded URLs
     * CSV configuration
     * Web scraping
     * API integration
     * Browser automation

USAGE:

   python -m src.acquisition.run_acquisition --year 2010
   
Downloads PDFs to:
   data/raw_pdfs/2010/
"""

# ==================== EXTRACTION PIPELINE (EXISTING) ====================

"""
PURPOSE:
- Extract metadata from SCR PDFs
- Produce schema-compliant JSON

CORE PHILOSOPHY:
- PDF-first, authoritative
- Zero hallucination
- Conservative extraction
- Prefer missing over wrong

PHASES:

Phase 0: Environment & Setup
   - Initialize directories
   - Configure logging
   
Phase 1: PDF Discovery
   - List available PDFs
   - Validate files
   - Log metadata
   
Phase 2: Text Extraction
   - PDF → raw text
   - Page-by-page
   - Handle scanned pages
   
Phase 3: Case Splitting
   - Split volume into cases
   - Use conservative anchors:
     * Case title in CAPS
     * "v." or "vs." separator
     * Judge brackets
   
Phase 4: Metadata Extraction
   - Extract ONLY explicit data:
     * case_name: from title
     * judges: from CORAM/Bench brackets
     * acts_referred: if explicitly named
     * sections_referred: if explicitly cited
   - Leave EMPTY if not present:
     * case_number
     * petition_type
     * parties
     * subject_categories
   
Phase 5: Cleaning & Normalization
   - Normalize judge names
   - Canonicalize Act names
   - Normalize Section format
   - Deduplicate conservatively
   
Phase 6: JSON Output
   - Validate schema compliance
   - Generate: data/output/scr_<YEAR>.json
   - Log statistics

USAGE:

   python -m src.pipeline.run_scr_pipeline --year 2010
   
Outputs:
   data/output/scr_2010.json
"""

# ==================== INTEGRATION ====================

"""
The two modules are INDEPENDENT but INTEGRATED:

ACQUISITION → EXTRACTION:

1. Acquisition downloads PDFs:
   python -m src.acquisition.run_acquisition --year 2010
   
   Creates:
   data/raw_pdfs/2010/scr_vol_1.pdf
   data/raw_pdfs/2010/scr_vol_2.pdf
   ...

2. Extraction finds and processes them:
   python -m src.pipeline.run_scr_pipeline --year 2010
   
   Outputs:
   data/output/scr_2010.json

SEPARATION OF CONCERNS:

Acquisition:
   Input:  Official PDF URLs
   Output: Files in data/raw_pdfs/
   Role:   Download & validate

Extraction:
   Input:  Files in data/raw_pdfs/
   Output: JSON in data/output/
   Role:   Parse & extract metadata

INDEPENDENCE:

- Extraction works without acquisition
  (users can manually place PDFs)
- Acquisition works without extraction
  (only downloads, doesn't parse)
- Each can be used or replaced independently
"""

# ==================== DATA FLOW ====================

"""
Complete end-to-end flow:

Official Sources
    ↓
[acquisition/run_acquisition.py]
    ├─ discovery: List available PDFs
    ├─ download: Fetch from URLs
    └─ validation: Verify files
    ↓
data/raw_pdfs/2010/
    ├─ scr_vol_1.pdf
    ├─ scr_vol_2.pdf
    └─ ...
    ↓
[pipeline/run_scr_pipeline.py]
    ├─ Phase 2: PDF text extraction
    │   ↓
    │   data/extracted_text/2010/
    │   ├─ scr_vol_1.txt
    │   ├─ scr_vol_2.txt
    │   └─ ...
    │
    ├─ Phase 3: Case splitting
    │   ↓
    │   [in-memory case blocks]
    │
    ├─ Phase 4: Metadata extraction
    │   ↓
    │   [extracted cases]
    │
    ├─ Phase 5: Normalization
    │   ↓
    │   [cleaned cases]
    │
    └─ Phase 6: JSON output
        ↓
        data/output/scr_2010.json
"""

# ==================== CONFIGURATION ====================

"""
All configuration in one place:
   config/settings.py

ACQUISITION SETTINGS:
   PDF_DOWNLOAD_TIMEOUT = 300
   PDF_DOWNLOAD_RETRIES = 3
   MAX_PDF_FILE_SIZE = 500 * 1024 * 1024
   MIN_PDF_FILE_SIZE = 10 * 1024
   CLEANUP_FAILED_DOWNLOADS = True
   VERIFY_PDF_INTEGRITY = True

EXTRACTION SETTINGS:
   STRICT_EXTRACTION = True
   NORMALIZE_JUDGES = True
   NORMALIZE_ACTS = True
   NORMALIZE_SECTIONS = True

OUTPUT SETTINGS:
   OUTPUT_FORMAT = "json"
   PRETTY_JSON = True
   JSON_INDENT = 2

See config/constants.py for:
   - Output schema (strict)
   - Extraction patterns
   - Canonicalization rules
   - Logging configuration
"""

# ==================== USAGE GUIDE ====================

"""
QUICK START:

1. Install dependencies:
   pip install -r requirements.txt

2. Register PDF sources:
   python -c "from src.acquisition.scr_pdf_fetcher import PDFSourceProvider; \
              PDFSourceProvider.register_source(2010, ['https://...'])"

3. Acquire PDFs:
   python -m src.acquisition.run_acquisition --year 2010

4. Extract metadata:
   python -m src.pipeline.run_scr_pipeline --year 2010

5. Check output:
   cat data/output/scr_2010.json

COMMAND OPTIONS:

Acquisition:
   --year YEAR              Year to acquire
   --dry-run               Simulate only
   --force-redownload      Re-download existing
   --show-sources          List sources

Extraction:
   --year YEAR              Year to process
"""

# ==================== LOGGING & MONITORING ====================

"""
LOGS LOCATION:
   logs/pipeline.log         Main log (all operations)
   logs/failures.log         Error log
   logs/acquisition_log_<YEAR>.json    Acquisition report
   logs/execution_log_<YEAR>.json      Extraction report

MONITORING:

Check for errors:
   grep ERROR logs/failures.log

Check acquisition progress:
   tail -f logs/pipeline.log

View statistics:
   cat logs/acquisition_log_2010.json | python -m json.tool

Verify extraction:
   wc -l data/output/scr_2010.json
"""

# ==================== DESIGN PRINCIPLES ====================

"""
1. CONSERVATIVE
   - Only download from verified sources
   - Extract only explicit data
   - Fail loudly on errors
   - Prefer missing over wrong

2. DEFENSIVE
   - Retry with backoff
   - Validate everything
   - Clean up failures
   - Log extensively

3. AUDITABLE
   - Every step logged
   - Execution reports
   - Checksum tracking
   - Clear error messages

4. MODULAR
   - Separate concerns
   - Independent modules
   - Clear interfaces
   - Pluggable components

5. PRODUCTION-READY
   - Comprehensive error handling
   - Idempotent operations
   - No data loss
   - Audit trail
"""

# ==================== SUCCESS CRITERIA ====================

"""
The system is successful if:

✓ PDFs are downloaded to correct location
✓ All files validated successfully
✓ Extraction produces valid JSON
✓ All required fields populated
✓ No hallucinated data
✓ Logs show clear progress
✓ Error handling works
✓ Can re-run without issues
✓ Audit trail is complete
✓ Code is maintainable
"""

# ==================== EXTENDING THE SYSTEM ====================

"""
The system is designed for extension:

1. ADD NEW PDF SOURCES
   - Use PDFSourceProvider.register_source()
   - Support multiple patterns (URLs, CSV, API, scraping)

2. ENHANCE ACQUISITION
   - Browser automation for JavaScript-heavy sites
   - Incremental updates (only new volumes)
   - Mirror support (fallback sources)
   - Batch downloading

3. IMPROVE EXTRACTION
   - Better case splitting heuristics
   - Additional metadata extraction
   - Cross-volume deduplication
   - Relationship detection

4. INTEGRATE WITH EXTERNAL SYSTEMS
   - Database storage
   - REST API for queries
   - Web interface
   - Elasticsearch indexing

5. ADD AUTOMATION
   - Scheduled downloads
   - Batch processing
   - Notification system
   - Health monitoring
"""

# ==================== KEY FILES ====================

"""
CRITICAL FILES (do not modify lightly):

config/constants.py
   - Output schema (STRICT)
   - Extraction patterns
   - Canonicalization rules
   
src/extraction/scr_metadata_extractor.py
   - Core extraction logic
   - Defines what gets extracted
   - Conservative rules

src/cleaning/normalizer.py
   - Normalization logic
   - Canonicalization
   - Deduplication

CONFIGURATION FILES:

config/settings.py
   - All paths and options
   - Timeouts and limits
   - Feature flags

ENTRY POINTS:

src/acquisition/run_acquisition.py
   python -m src.acquisition.run_acquisition --year YEAR

src/pipeline/run_scr_pipeline.py
   python -m src.pipeline.run_scr_pipeline --year YEAR
"""

if __name__ == "__main__":
    print(__doc__)
