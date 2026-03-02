"""
CONSTANTS: SCR Pipeline - Fixed values, schema, and legal templates
"""

# OUTPUT SCHEMA (STRICT - DO NOT CHANGE)
SCR_CASE_SCHEMA = {
    "court": "Supreme Court of India",
    "case_number": "",
    "petition_type": "",
    "petition_format": "",
    "judges": [],
    "petitioner": [],
    "respondent": [],
    "case_name": "",
    "acts_referred": [],
    "sections_referred": [],
    "subject_categories": [],
}

# Keys that are required (but can be empty)
REQUIRED_KEYS = set(SCR_CASE_SCHEMA.keys())

# Mapping of what data types each field should have
SCHEMA_TYPES = {
    "court": str,
    "case_number": str,
    "petition_type": str,
    "petition_format": str,
    "judges": list,
    "petitioner": list,
    "respondent": list,
    "case_name": str,
    "acts_referred": list,
    "sections_referred": list,
    "subject_categories": list,
}

# ==================== EXTRACTION CONSTANTS ====================

# Patterns for conservative case splitting
CASE_SPLIT_MARKERS = {
    "coram_patterns": [
        r"\[.*?[Cc]oram.*?\]",  # [Coram: Justice X, Justice Y]
        r"\([Cc]oram:.*?\)",    # (Coram: Justice X, Justice Y)
        r"[Bb]ench:.*?[:\[]",   # Bench: Justice X, Justice Y
    ],
    "case_title_pattern": r"^[A-Z\s\.\-]*\s+v\.?\s+[A-Z\s\.\-]+$",  # ABC v. XYZ
    "separator_patterns": [
        r"^={3,}",  # === separator
        r"^-{3,}",  # --- separator
    ],
}

# Judge name cleaning patterns
JUDGE_TITLE_PREFIXES = [
    "Hon'ble",
    "Honourable",
    "Mr.",
    "Dr.",
    "The",
    "justice",
    "judge",
]

# Act name canonicalization
ACT_SYNONYMS = {
    "IPC": "Indian Penal Code, 1860",
    "Indian Penal Code": "Indian Penal Code, 1860",
    "CPC": "Code of Civil Procedure, 1908",
    "Code of Civil Procedure": "Code of Civil Procedure, 1908",
    "CrPC": "Code of Criminal Procedure, 1973",
    "Code of Criminal Procedure": "Code of Criminal Procedure, 1973",
    "Constitution": "Constitution of India, 1950",
    "Indian Constitution": "Constitution of India, 1950",
    "Hindu Marriage Act": "Hindu Marriage Act, 1955",
    "HMA": "Hindu Marriage Act, 1955",
    "Succession Act": "Indian Succession Act, 1925",
}

# Sections format patterns
SECTION_PATTERNS = [
    r"[Ss]ection\s+(\d+[A-Za-z]*)",      # Section 123, Section 123A
    r"[Ss]ec\.\s+(\d+[A-Za-z]*)",        # Sec. 123
    r"[Ss]s\.\s+(\d+[A-Za-z]*)",         # Ss. 123
    r"[Aa]rticle\s+(\d+)",                # Article 226
    r"[Aa]rt\.\s+(\d+)",                  # Art. 226
]

# ==================== LOGGING CONSTANTS ====================

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

# ==================== PDF PROCESSING CONSTANTS ====================

# PDF extraction settings
PDF_EXTRACTION_TIMEOUT = 300  # seconds per PDF
MIN_TEXT_LENGTH_PER_PAGE = 10  # minimum characters to consider valid extraction

# Scanned page detection thresholds
SCANNED_PAGE_THRESHOLD = 0.3  # % of whitespace above this = likely scanned

# ==================== FILE HANDLING CONSTANTS ====================

# Supported PDF formats
SUPPORTED_PDF_EXTENSIONS = [".pdf", ".PDF"]

# Intermediate file extensions
TEXT_EXTRACT_EXTENSION = ".txt"
JSON_OUTPUT_EXTENSION = ".json"

# ==================== CASE SPLITTING CONSTANTS ====================

# Conservative split: minimum text length per extracted case
MIN_CASE_TEXT_LENGTH = 50  # characters

# Maximum pages that should be part of single case (to detect splits)
EXPECTED_CASE_MAX_PAGES = 100

# ==================== IDEMPOTENCY CONSTANTS ====================

# Used for tracking processed files
METADATA_FILE_EXTENSION = ".meta"
CHECKSUM_ALGORITHM = "sha256"
