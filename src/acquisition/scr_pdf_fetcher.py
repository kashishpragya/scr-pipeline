"""
ACQUISITION - SCR PDF Fetcher

Download SCR PDFs from official sources

Key Principles:
- Use only official sources
- Defensive error handling
- Clear logging of every step
- No inference or guessing
- Idempotent (skip existing files)
"""

import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time

from config.settings import (
    RAW_PDFs_DIR,
    PDF_DOWNLOAD_TIMEOUT,
    PDF_DOWNLOAD_RETRIES,
    CLEANUP_FAILED_DOWNLOADS,
    MAX_PDF_FILE_SIZE,
    MIN_PDF_FILE_SIZE,
)
from src.utils import (
    pipeline_logger,
    failures_logger,
    get_year_directory,
    compute_file_checksum,
)


class SCRPDFFetcher:
    """Download SCR PDFs from official sources."""

    def __init__(self):
        """Initialize fetcher."""
        self.fetch_stats = {
            "total_pdfs_attempted": 0,
            "successfully_downloaded": 0,
            "skipped_existing": 0,
            "failed_downloads": 0,
            "validation_failures": 0,
            "download_time": None,
        }

        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

    def check_pdf_exists(self, pdf_path: Path) -> bool:
        """
        Check if a PDF already exists and is valid.

        Args:
            pdf_path: Path to check

        Returns:
            True if file exists and is valid
        """
        if not pdf_path.exists():
            return False

        try:
            size = pdf_path.stat().st_size

            # Check file size bounds
            if size < MIN_PDF_FILE_SIZE or size > MAX_PDF_FILE_SIZE:
                pipeline_logger.warning(
                    f"Existing file {pdf_path.name} has suspicious size: {size} bytes"
                )
                return False

            # Check PDF magic number
            with open(pdf_path, "rb") as f:
                header = f.read(4)
                if header != b"%PDF":
                    pipeline_logger.warning(
                        f"Existing file {pdf_path.name} is not a valid PDF (bad header)"
                    )
                    return False

            return True

        except Exception as e:
            pipeline_logger.warning(f"Error checking existing file {pdf_path.name}: {e}")
            return False

    def download_pdf(
        self,
        url: str,
        pdf_path: Path,
        retries: int = PDF_DOWNLOAD_RETRIES,
    ) -> Tuple[bool, Optional[str]]:
        """
        Download a single PDF from a URL.

        Args:
            url: URL to download from
            pdf_path: Path to save to
            retries: Number of retry attempts

        Returns:
            Tuple of (success, error_message)
        """
        pipeline_logger.debug(f"Downloading: {url}")

        attempt = 0
        last_error = None

        while attempt < retries:
            attempt += 1

            try:
                # Make HTTP request
                response = requests.get(
                    url,
                    timeout=PDF_DOWNLOAD_TIMEOUT,
                    headers={"User-Agent": self.user_agent},
                    stream=True,
                )

                # Check response status
                if response.status_code != 200:
                    last_error = f"HTTP {response.status_code}"
                    pipeline_logger.warning(
                        f"Download failed (attempt {attempt}/{retries}): {last_error}"
                    )
                    if attempt < retries:
                        time.sleep(2**attempt)  # Exponential backoff
                    continue

                # Check content type (basic validation)
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                    last_error = "Invalid content type (not a PDF)"
                    pipeline_logger.warning(f"Download failed: {last_error}")
                    if attempt < retries:
                        time.sleep(2**attempt)
                    continue

                # Check content length
                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        size = int(content_length)
                        if size < MIN_PDF_FILE_SIZE:
                            last_error = f"File too small: {size} bytes"
                            pipeline_logger.warning(f"Download rejected: {last_error}")
                            if attempt < retries:
                                time.sleep(2**attempt)
                            continue
                        if size > MAX_PDF_FILE_SIZE:
                            last_error = f"File too large: {size} bytes"
                            pipeline_logger.warning(f"Download rejected: {last_error}")
                            return False, last_error
                    except ValueError:
                        pass  # Content-length not parseable, continue

                # Write to temporary file first
                temp_path = pdf_path.with_suffix(pdf_path.suffix + ".tmp")
                downloaded_size = 0

                with open(temp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                # Validate downloaded file
                if downloaded_size < MIN_PDF_FILE_SIZE:
                    last_error = f"Downloaded file too small: {downloaded_size} bytes"
                    pipeline_logger.warning(f"Download validation failed: {last_error}")

                    if CLEANUP_FAILED_DOWNLOADS:
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass

                    if attempt < retries:
                        time.sleep(2**attempt)
                    continue

                if downloaded_size > MAX_PDF_FILE_SIZE:
                    last_error = f"Downloaded file too large: {downloaded_size} bytes"

                    if CLEANUP_FAILED_DOWNLOADS:
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass

                    return False, last_error

                # Verify PDF header
                try:
                    with open(temp_path, "rb") as f:
                        header = f.read(4)
                        if header != b"%PDF":
                            last_error = "Invalid PDF header"
                            pipeline_logger.warning(f"PDF validation failed: {last_error}")

                            if CLEANUP_FAILED_DOWNLOADS:
                                try:
                                    temp_path.unlink()
                                except Exception:
                                    pass

                            if attempt < retries:
                                time.sleep(2**attempt)
                            continue
                except Exception as e:
                    last_error = f"Error validating PDF: {e}"

                    if CLEANUP_FAILED_DOWNLOADS:
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass

                    if attempt < retries:
                        time.sleep(2**attempt)
                    continue

                # Move from temp to final location
                try:
                    temp_path.rename(pdf_path)
                    pipeline_logger.info(
                        f"Successfully downloaded: {pdf_path.name} ({downloaded_size} bytes)"
                    )
                    return True, None

                except Exception as e:
                    last_error = f"Error moving file: {e}"

                    if CLEANUP_FAILED_DOWNLOADS:
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass

                    if attempt < retries:
                        time.sleep(2**attempt)
                    continue

            except requests.Timeout:
                last_error = "Request timeout"
                pipeline_logger.warning(f"Download timeout (attempt {attempt}/{retries})")
                if attempt < retries:
                    time.sleep(2**attempt)

            except requests.ConnectionError as e:
                last_error = f"Connection error: {e}"
                pipeline_logger.warning(f"Connection error (attempt {attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(2**attempt)

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                pipeline_logger.warning(f"Download error (attempt {attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(2**attempt)

        return False, last_error

    def fetch_pdf(
        self,
        url: str,
        pdf_name: str,
        year: int,
        force_redownload: bool = False,
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Fetch a single PDF.

        Args:
            url: URL to download from
            pdf_name: Name to save as
            year: Year for directory organization
            force_redownload: Re-download even if exists

        Returns:
            Tuple of (success, saved_path, error_message)
        """
        self.fetch_stats["total_pdfs_attempted"] += 1

        # Ensure PDF name has proper extension
        if not pdf_name.lower().endswith(".pdf"):
            pdf_name = pdf_name + ".pdf"

        # Create target directory
        year_dir = get_year_directory(RAW_PDFs_DIR, year)
        pdf_path = year_dir / pdf_name

        # Check if file already exists
        if not force_redownload:
            if self.check_pdf_exists(pdf_path):
                pipeline_logger.debug(f"Skipping existing file: {pdf_name}")
                self.fetch_stats["skipped_existing"] += 1
                return True, pdf_path, None

        # Download the PDF
        success, error = self.download_pdf(url, pdf_path)

        if not success:
            self.fetch_stats["failed_downloads"] += 1
            failures_logger.error(f"Failed to download {pdf_name} from {url}: {error}")
            return False, None, error

        self.fetch_stats["successfully_downloaded"] += 1
        return True, pdf_path, None

    def get_fetch_stats(self) -> Dict:
        """Get fetch statistics."""
        return self.fetch_stats.copy()


class PDFSourceProvider:
    """
    Provides PDF URLs from official sources.

    This class is extensible and conservative:
    - Only includes sources that are explicitly verified
    - Does not guess or infer URLs
    - Logs which sources are being used
    """

    # Official sources for SCR PDFs
    # Format: {year: [list of URLs]}
    # To be populated by implementing specific source integrations
    KNOWN_SOURCES = {}

    @classmethod
    def register_source(cls, year: int, urls: List[str]):
        """
        Register URLs for a specific year.

        Args:
            year: Year
            urls: List of valid PDF URLs
        """
        if year not in cls.KNOWN_SOURCES:
            cls.KNOWN_SOURCES[year] = []

        cls.KNOWN_SOURCES[year].extend(urls)
        pipeline_logger.debug(f"Registered {len(urls)} sources for year {year}")

    @classmethod
    def get_sources_for_year(cls, year: int) -> List[str]:
        """
        Get known sources for a year.

        Args:
            year: Year

        Returns:
            List of URLs
        """
        return cls.KNOWN_SOURCES.get(year, [])

    @classmethod
    def clear_sources(cls):
        """Clear all registered sources (for testing)."""
        cls.KNOWN_SOURCES.clear()


def get_fetcher() -> SCRPDFFetcher:
    """Get a PDF fetcher instance."""
    return SCRPDFFetcher()


if __name__ == "__main__":
    # Test: Show available sources
    import json

    pipeline_logger.info("Known PDF sources:")
    for year, urls in PDFSourceProvider.KNOWN_SOURCES.items():
        pipeline_logger.info(f"  Year {year}: {len(urls)} source(s)")
        for url in urls:
            pipeline_logger.info(f"    - {url}")

    if not PDFSourceProvider.KNOWN_SOURCES:
        pipeline_logger.info("No sources registered. Use register_source() to add sources.")
