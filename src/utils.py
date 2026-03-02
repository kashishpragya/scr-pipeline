"""
UTILS: SCR Pipeline - Logging, helpers, and utilities
"""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.settings import (
    PIPELINE_LOG_FILE,
    FAILURES_LOG_FILE,
    LOGGING_LEVEL,
    LOG_FILE_MAX_SIZE,
    LOG_BACKUP_COUNT,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
)
from config.constants import REQUIRED_KEYS, SCHEMA_TYPES


# ==================== LOGGING SETUP ====================


def setup_logger(name: str, log_file: Path, level: str = LOGGING_LEVEL) -> logging.Logger:
    """
    Create and configure a logger with both file and console handlers.

    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler with rotation
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_FILE_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(getattr(logging, level))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Create loggers
pipeline_logger = setup_logger("scr_pipeline", PIPELINE_LOG_FILE)
failures_logger = setup_logger("scr_failures", FAILURES_LOG_FILE)


# ==================== VALIDATION HELPERS ====================


def validate_case_schema(case: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate a case dictionary against the required schema.

    Args:
        case: Case dictionary to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check all required keys exist
    for key in REQUIRED_KEYS:
        if key not in case:
            errors.append(f"Missing required key: {key}")

    # Check no extra keys
    extra_keys = set(case.keys()) - REQUIRED_KEYS
    if extra_keys:
        errors.append(f"Extra keys not allowed: {extra_keys}")

    # Check data types
    for key, expected_type in SCHEMA_TYPES.items():
        if key in case:
            if not isinstance(case[key], expected_type):
                errors.append(
                    f"Field '{key}' should be {expected_type.__name__}, "
                    f"got {type(case[key]).__name__}"
                )

    return len(errors) == 0, errors


def validate_case_strict(case: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Strict validation: ensure all required fields are either filled or properly empty.

    Args:
        case: Case dictionary to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    schema_valid, schema_errors = validate_case_schema(case)

    if not schema_valid:
        return False, schema_errors

    # Additional strict checks
    errors = []

    # String fields must not be None
    string_fields = ["court", "case_number", "petition_type", "petition_format", "case_name"]
    for field in string_fields:
        if case.get(field) is None:
            errors.append(f"Field '{field}' must be empty string, not None")

    # Array fields must not be None
    array_fields = [
        "judges",
        "petitioner",
        "respondent",
        "acts_referred",
        "sections_referred",
        "subject_categories",
    ]
    for field in array_fields:
        if case.get(field) is None:
            errors.append(f"Field '{field}' must be empty list, not None")

    return len(errors) == 0, errors


# ==================== FILE HELPERS ====================


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists and return path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_year_directory(base_dir: Path, year: int) -> Path:
    """Get year-specific subdirectory, creating if needed."""
    year_dir = base_dir / str(year)
    return ensure_directory(year_dir)


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from filename."""
    unsafe_chars = r'<>:"/\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, "_")
    return filename


# ==================== JSON HELPERS ====================


def save_json(data: Any, file_path: Path, pretty: bool = True, indent: int = 2) -> bool:
    """
    Save data to JSON file.

    Args:
        data: Data to save
        file_path: Path to save to
        pretty: Pretty-print JSON
        indent: Indentation level

    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory(file_path.parent)
        with open(file_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)
        return True
    except Exception as e:
        failures_logger.error(f"Failed to save JSON to {file_path}: {e}")
        return False


def load_json(file_path: Path) -> Optional[Any]:
    """
    Load data from JSON file.

    Args:
        file_path: Path to load from

    Returns:
        Loaded data or None if failed
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        failures_logger.error(f"Failed to load JSON from {file_path}: {e}")
        return None


# ==================== TEXT PROCESSING HELPERS ====================


def clean_whitespace(text: str) -> str:
    """Remove extra whitespace and normalize line breaks."""
    # Remove excess whitespace
    text = " ".join(text.split())
    return text


def extract_lines(text: str, strip: bool = True) -> List[str]:
    """
    Extract lines from text, optionally stripping each line.

    Args:
        text: Text to process
        strip: Whether to strip leading/trailing whitespace

    Returns:
        List of lines
    """
    lines = text.split("\n")
    if strip:
        lines = [line.strip() for line in lines]
    return [line for line in lines if line]  # Remove empty lines


def normalize_spacing(text: str) -> str:
    """Normalize internal spacing while preserving structure."""
    # Replace multiple spaces with single space
    text = " ".join(text.split())
    return text


def is_all_caps(text: str) -> bool:
    """Check if text is in all capitals (ignoring numbers and punctuation)."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return all(c.isupper() for c in letters)


def remove_page_markers(text: str) -> str:
    """Remove common page markers, footnotes, etc."""
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        # Skip common page markers
        if line.strip() in ["", "---", "==="]:
            continue
        # Skip page numbers
        if line.strip().isdigit():
            continue
        cleaned.append(line)

    return "\n".join(cleaned)


# ==================== CASE PROCESSING HELPERS ====================


def deduplicate_list(items: List[str], preserve_order: bool = True) -> List[str]:
    """
    Deduplicate a list of items.

    Args:
        items: List to deduplicate
        preserve_order: Whether to preserve original order

    Returns:
        Deduplicated list
    """
    if preserve_order:
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    else:
        return list(set(items))


def normalize_list_items(items: List[str]) -> List[str]:
    """Normalize and clean items in a list."""
    normalized = []
    for item in items:
        # Strip and normalize spacing
        item = item.strip()
        item = normalize_spacing(item)

        if item:  # Only add non-empty items
            normalized.append(item)

    return deduplicate_list(normalized)


# ==================== PROGRESS TRACKING ====================


def log_phase_start(phase_num: int, phase_name: str):
    """Log the start of a pipeline phase."""
    pipeline_logger.info(f"{'='*60}")
    pipeline_logger.info(f"PHASE {phase_num}: {phase_name}")
    pipeline_logger.info(f"{'='*60}")


def log_phase_end(phase_num: int, phase_name: str, summary: str = ""):
    """Log the end of a pipeline phase."""
    msg = f"PHASE {phase_num} COMPLETE: {phase_name}"
    if summary:
        msg += f" - {summary}"
    pipeline_logger.info(msg)


def log_extraction_stats(total_pdfs: int, successful: int, failed: int, total_cases: int):
    """Log extraction statistics."""
    pipeline_logger.info(f"Total PDFs processed: {total_pdfs}")
    pipeline_logger.info(f"Successful extractions: {successful}")
    pipeline_logger.info(f"Failed PDFs: {failed}")
    pipeline_logger.info(f"Total cases extracted: {total_cases}")


# ==================== PARAMETER VALIDATION ====================


def validate_year(
    year: int, min_year: int = 1950, max_year: int = 2100
) -> tuple[bool, Optional[str]]:
    """
    Validate year parameter.

    Args:
        year: Year to validate
        min_year: Minimum allowed year
        max_year: Maximum allowed year

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(year, int):
        return False, f"Year must be an integer, got {type(year).__name__}"

    if year < min_year:
        return False, f"Year {year} is before minimum allowed year {min_year}"

    if year > max_year:
        return False, f"Year {year} is after maximum allowed year {max_year}"

    if year < 1950:
        return False, "Year must be 1950 or later (no Supreme Court Reports before 1950)"

    return True, None


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(url, str):
        return False, f"URL must be a string, got {type(url).__name__}"

    url = url.strip()

    if not url:
        return False, "URL cannot be empty"

    # Check for basic URL pattern
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "URL must start with http:// or https://"

    # Check for spaces (usually invalid in URLs)
    if " " in url:
        return False, "URL contains spaces (invalid)"

    # Check for PDF extension recommendation
    if not url.lower().endswith(".pdf"):
        # Warn but don't fail - some URLs might be redirects
        pipeline_logger.warning(f"URL does not end with .pdf: {url}")

    return True, None


# ==================== CHECKPOINTING SYSTEM ====================


def create_checkpoint(year: int, phase_num: int, phase_data: Dict[str, Any]) -> bool:
    """
    Create a checkpoint after completing a phase.

    Args:
        year: Year being processed
        phase_num: Phase number (0-6)
        phase_data: Data to checkpoint

    Returns:
        True if successful, False otherwise
    """
    from config.settings import LOGS_DIR

    try:
        checkpoint_dir = LOGS_DIR / "checkpoints"
        ensure_directory(checkpoint_dir)

        checkpoint_file = checkpoint_dir / f"checkpoint_phase_{phase_num}_{year}.json"

        checkpoint = {
            "year": year,
            "phase": phase_num,
            "timestamp": datetime.now().isoformat(),
            "data": phase_data,
        }

        save_json(checkpoint, checkpoint_file, pretty=True)
        pipeline_logger.debug(f"Created checkpoint: {checkpoint_file}")

        return True

    except Exception as e:
        failures_logger.error(f"Failed to create checkpoint for phase {phase_num}: {e}")
        return False


def load_checkpoint(year: int, phase_num: int) -> Optional[Dict]:
    """
    Load a checkpoint from a previous phase.

    Args:
        year: Year being processed
        phase_num: Phase number to load

    Returns:
        Checkpoint data or None if not found
    """
    from config.settings import LOGS_DIR

    try:
        checkpoint_file = LOGS_DIR / "checkpoints" / f"checkpoint_phase_{phase_num}_{year}.json"

        if not checkpoint_file.exists():
            return None

        checkpoint = load_json(checkpoint_file)

        if checkpoint and checkpoint.get("phase") == phase_num:
            pipeline_logger.debug(f"Loaded checkpoint for phase {phase_num}")
            return checkpoint.get("data")

        return None

    except Exception as e:
        failures_logger.error(f"Failed to load checkpoint for phase {phase_num}: {e}")
        return None


def can_skip_phase(year: int, phase_num: int) -> bool:
    """
    Check if a phase can be skipped (checkpoint exists).

    Args:
        year: Year being processed
        phase_num: Phase number

    Returns:
        True if phase can be skipped
    """
    checkpoint = load_checkpoint(year, phase_num)
    return checkpoint is not None


# ==================== CHECKSUM HELPERS ====================

import hashlib


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """
    Compute file checksum for idempotency tracking.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5, etc.)

    Returns:
        Checksum string or None if failed
    """
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        failures_logger.error(f"Failed to compute checksum for {file_path}: {e}")
        return None
