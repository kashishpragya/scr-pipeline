"""
SETTINGS: SCR Pipeline - Configuration and paths
"""

from pathlib import Path

# ==================== PROJECT ROOT ====================
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# ==================== DATA DIRECTORIES ====================
DATA_DIR = PROJECT_ROOT / "data"

RAW_PDFs_DIR = DATA_DIR / "raw_pdfs"
EXTRACTED_TEXT_DIR = DATA_DIR / "extracted_text"
OUTPUT_DIR = DATA_DIR / "output"

# ==================== LOGS DIRECTORIES ====================
LOGS_DIR = PROJECT_ROOT / "logs"
PIPELINE_LOG_FILE = LOGS_DIR / "pipeline.log"
FAILURES_LOG_FILE = LOGS_DIR / "failures.log"

# ==================== SOURCE DIRECTORIES ====================
SRC_DIR = PROJECT_ROOT / "src"
AUTOMATION_DIR = SRC_DIR / "automation"
EXTRACTION_DIR = SRC_DIR / "extraction"
CLEANING_DIR = SRC_DIR / "cleaning"
PIPELINE_DIR = SRC_DIR / "pipeline"
ACQUISITION_DIR = SRC_DIR / "acquisition"

# ==================== LOGGING CONFIGURATION ====================

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGGING_LEVEL = "INFO"

# Log message format
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# Date format for log timestamps
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file max size (bytes) before rotation
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

# Number of backup log files to keep
LOG_BACKUP_COUNT = 5


# ==================== PDF EXTRACTION SETTINGS ====================

# PDF text extraction engine
# Options: "pdfplumber" (default, recommended)
PDF_EXTRACTION_ENGINE = "pdfplumber"

# Enable OCR for scanned pages (requires pytesseract and tesseract-ocr)
ENABLE_OCR = False
OCR_LANGUAGE = "eng"

# Extract text from scanned images in PDFs
EXTRACT_FROM_SCANNED = False

# ==================== CASE SPLITTING SETTINGS ====================

# Conservative splitting: require explicit markers
STRICT_SPLITTING = True

# Log ambiguous case boundaries
LOG_AMBIGUOUS_SPLITS = True

# ==================== METADATA EXTRACTION SETTINGS ====================

# Only extract fields that are explicitly present in text
STRICT_EXTRACTION = True

# Log missing expected fields (e.g., case_number)
LOG_MISSING_FIELDS = True

# ==================== NORMALIZATION SETTINGS ====================

# Normalize judge names (remove titles, standardize)
NORMALIZE_JUDGES = True

# Normalize Act names to canonical forms
NORMALIZE_ACTS = True

# Normalize Section citations to standard format
NORMALIZE_SECTIONS = True

# Deduplicate values in arrays
DEDUPLICATE_ARRAYS = True

# ==================== OUTPUT SETTINGS ====================

# Output format: "jsonl" (one object per line) or "json" (array)
OUTPUT_FORMAT = "json"

# Pretty-print JSON output
PRETTY_JSON = True

# Indent level for JSON output
JSON_INDENT = 2

# ==================== IDEMPOTENCY SETTINGS ====================

# Track processed files to avoid re-processing
ENABLE_IDEMPOTENCY = True

# Store checksums of processed PDFs
STORE_CHECKSUMS = True

# ==================== AUTOMATION HOOKS ====================

# Support manual PDF seeding
MANUAL_PDF_SEEDING = True

# Enable automation discovery hooks for future browser automation
ENABLE_DISCOVERY_HOOKS = True

# ==================== BATCH PROCESSING ====================

# Process PDFs in parallel (number of workers)
# 0 = sequential processing, > 0 = parallel with N workers
PARALLEL_WORKERS = 0

# ==================== VALIDATION ====================

# Validate output against schema
VALIDATE_OUTPUT = True

# Fail on schema validation errors
FAIL_ON_VALIDATION_ERROR = True

# ==================== PDF ACQUISITION SETTINGS ====================

# PDF download timeout (seconds)
PDF_DOWNLOAD_TIMEOUT = 300

# Retry failed downloads (number of attempts)
PDF_DOWNLOAD_RETRIES = 3

# Verify PDF file validity before accepting
VERIFY_PDF_INTEGRITY = True

# Delete partially downloaded files on failure
CLEANUP_FAILED_DOWNLOADS = True

# Maximum PDF file size (bytes) - prevent downloading huge files
MAX_PDF_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

# Minimum PDF file size (bytes) - likely corrupted if smaller
MIN_PDF_FILE_SIZE = 10 * 1024  # 10 KB

# ==================== INITIALIZE DIRECTORIES ====================

def initialize_directories():
    """Create all required directories if they don't exist."""
    directories = [
        LOGS_DIR,
        RAW_PDFs_DIR,
        EXTRACTED_TEXT_DIR,
        OUTPUT_DIR,
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)

# Create directories on module import
initialize_directories()
