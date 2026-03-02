"""
ACQUISITION - PDF Validator

Validate that downloaded PDFs are valid and usable by the extraction pipeline

Validation Checks:
- File exists and is readable
- File size within acceptable bounds
- Has valid PDF magic number
- Can be read by pdfplumber
- Not corrupted
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
import pdfplumber

from config.settings import MIN_PDF_FILE_SIZE, MAX_PDF_FILE_SIZE
from src.utils import (
    pipeline_logger,
    failures_logger,
    compute_file_checksum,
)


class PDFValidator:
    """Validate PDF files for the extraction pipeline."""

    def __init__(self):
        """Initialize validator."""
        self.validation_stats = {
            "total_validated": 0,
            "valid_pdfs": 0,
            "invalid_pdfs": 0,
            "validation_errors": {},
        }

    def validate_file_exists(self, pdf_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check if file exists and is readable.

        Args:
            pdf_path: Path to PDF

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pdf_path.exists():
            return False, "File does not exist"

        if not pdf_path.is_file():
            return False, "Path is not a file"

        try:
            # Try to open file to verify readability
            with open(pdf_path, "rb") as f:
                pass
            return True, None
        except PermissionError:
            return False, "Permission denied"
        except Exception as e:
            return False, f"Cannot read file: {e}"

    def validate_file_extension(self, pdf_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check file extension.

        Args:
            pdf_path: Path to PDF

        Returns:
            Tuple of (is_valid, error_message)
        """
        if pdf_path.suffix.lower() != ".pdf":
            return False, f"Invalid extension: {pdf_path.suffix}"

        return True, None

    def validate_file_size(self, pdf_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check file size is within bounds.

        Args:
            pdf_path: Path to PDF

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            size = pdf_path.stat().st_size

            if size == 0:
                return False, "File is empty (0 bytes)"

            if size < MIN_PDF_FILE_SIZE:
                return False, f"File too small ({size} bytes, minimum {MIN_PDF_FILE_SIZE})"

            if size > MAX_PDF_FILE_SIZE:
                return False, f"File too large ({size} bytes, maximum {MAX_PDF_FILE_SIZE})"

            return True, None

        except Exception as e:
            return False, f"Cannot read file size: {e}"

    def validate_pdf_magic(self, pdf_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check PDF magic number (file header).

        Args:
            pdf_path: Path to PDF

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(4)

                if len(header) < 4:
                    return False, "File too small to contain PDF header"

                if header != b"%PDF":
                    return False, f"Invalid PDF header: {header}"

            return True, None

        except Exception as e:
            return False, f"Error reading PDF header: {e}"

    def validate_pdf_readable(self, pdf_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Check if PDF can be read by pdfplumber.

        Args:
            pdf_path: Path to PDF

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Try to get page count
                num_pages = len(pdf.pages)

                if num_pages == 0:
                    return False, "PDF has no pages"

                # Try to extract text from first page
                first_page = pdf.pages[0]
                text = first_page.extract_text()

                # PDF is valid even if no text extracted (might be scanned)
                # Just verify it doesn't crash

            return True, None

        except pdfplumber.exceptions.PDFException as e:
            return False, f"PDF read error: {e}"
        except Exception as e:
            return False, f"Cannot read PDF with pdfplumber: {e}"

    def validate_pdf(self, pdf_path: Path) -> Tuple[bool, Dict]:
        """
        Validate a PDF file completely.

        Args:
            pdf_path: Path to PDF

        Returns:
            Tuple of (is_valid, validation_report)
        """
        self.validation_stats["total_validated"] += 1

        report = {
            "path": str(pdf_path),
            "filename": pdf_path.name,
            "is_valid": False,
            "checks": {},
            "errors": [],
        }

        # Check 1: File exists
        valid, error = self.validate_file_exists(pdf_path)
        report["checks"]["exists"] = valid
        if not valid:
            report["errors"].append(error)
            self.validation_stats["invalid_pdfs"] += 1
            return False, report

        # Check 2: Extension
        valid, error = self.validate_file_extension(pdf_path)
        report["checks"]["extension"] = valid
        if not valid:
            report["errors"].append(error)
            self.validation_stats["invalid_pdfs"] += 1
            return False, report

        # Check 3: File size
        valid, error = self.validate_file_size(pdf_path)
        report["checks"]["file_size"] = valid
        if not valid:
            report["errors"].append(error)
            self.validation_stats["invalid_pdfs"] += 1
            return False, report

        # Check 4: PDF magic number
        valid, error = self.validate_pdf_magic(pdf_path)
        report["checks"]["pdf_magic"] = valid
        if not valid:
            report["errors"].append(error)
            self.validation_stats["invalid_pdfs"] += 1
            return False, report

        # Check 5: PDF readable
        valid, error = self.validate_pdf_readable(pdf_path)
        report["checks"]["pdf_readable"] = valid
        if not valid:
            report["errors"].append(error)
            self.validation_stats["invalid_pdfs"] += 1
            return False, report

        # All checks passed
        report["is_valid"] = True
        self.validation_stats["valid_pdfs"] += 1

        # Compute checksum for tracking
        try:
            checksum = compute_file_checksum(pdf_path)
            report["checksum"] = checksum
        except Exception as e:
            pipeline_logger.debug(f"Could not compute checksum for {pdf_path.name}: {e}")

        return True, report

    def get_validation_stats(self) -> Dict:
        """Get validation statistics."""
        return self.validation_stats.copy()


def validate_pdf_file(pdf_path: Path) -> bool:
    """
    Quick validation check for a PDF file.

    Args:
        pdf_path: Path to PDF

    Returns:
        True if valid, False otherwise
    """
    validator = PDFValidator()
    is_valid, report = validator.validate_pdf(pdf_path)

    if not is_valid:
        for error in report["errors"]:
            failures_logger.error(f"PDF validation failed ({pdf_path.name}): {error}")

    return is_valid


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scr_pdf_validator.py <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    validator = PDFValidator()
    is_valid, report = validator.validate_pdf(pdf_path)

    import json

    print(json.dumps(report, indent=2))

    if is_valid:
        print("\n✓ PDF is valid")
        sys.exit(0)
    else:
        print("\n✗ PDF is invalid")
        sys.exit(1)
