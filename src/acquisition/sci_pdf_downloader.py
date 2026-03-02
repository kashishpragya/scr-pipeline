"""
ACQUISITION - SCI PDF Downloader

Downloads PDF files from discovered URLs with validation and deduplication.
Saves PDFs to data/raw_pdfs/<YEAR>/ organized by year.

Usage:
    downloader = SCIPDFDownloader()
    results = downloader.download_multiple(pdf_links, year=2021)
    print(results.summary())
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import requests
from datetime import datetime

from src.utils import pipeline_logger


class DownloadResult:
    """Track download results for reporting."""

    def __init__(self):
        self.total_urls: int = 0
        self.unique_urls: int = 0
        self.successful_downloads: int = 0
        self.failed_downloads: int = 0
        self.skipped_existing: int = 0
        self.failed_urls: List[str] = []
        self.downloaded_files: List[str] = []

    def summary(self) -> str:
        """Return formatted summary of download results."""
        return (
            f"\n{'=' * 70}\n"
            f"DOWNLOAD SUMMARY\n"
            f"{'=' * 70}\n"
            f"  Total URLs processed:     {self.total_urls}\n"
            f"  Unique URLs:              {self.unique_urls}\n"
            f"  Successfully downloaded:  {self.successful_downloads}\n"
            f"  Skipped (existing):       {self.skipped_existing}\n"
            f"  Failed downloads:         {self.failed_downloads}\n"
            f"{'=' * 70}"
        )


class SCIPDFDownloader:
    """
    Downloads PDFs from SCI judgement URLs with validation and metadata.

    Features:
    - Downloads with stream support for large files
    - PDF header validation (magic number check)
    - Deduplication of URLs
    - Safe filename generation
    - Automatic directory creation
    - Comprehensive logging
    """

    # PDF magic number (first 4 bytes)
    PDF_MAGIC_NUMBER = b"%PDF"

    def __init__(self, timeout: int = 30, verify_ssl: bool = True):
        """
        Initialize downloader.

        Args:
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        pipeline_logger.info("SCIPDFDownloader initialized")

    def _validate_pdf_header(self, file_path: str) -> bool:
        """
        Validate that downloaded file is a valid PDF.

        Args:
            file_path: Path to file to validate

        Returns:
            True if file has PDF magic number, False otherwise
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                is_valid = header == self.PDF_MAGIC_NUMBER
                if not is_valid:
                    pipeline_logger.warning(
                        f"Invalid PDF header in {file_path}: {header[:4]}"
                    )
                return is_valid
        except Exception as e:
            pipeline_logger.error(f"Error validating PDF header: {e}")
            return False

    def _generate_safe_filename(self, url: str, index: int) -> str:
        """
        Generate safe filename from URL or index.

        Args:
            url: Source URL
            index: Sequence number for filename

        Returns:
            Safe filename (e.g., "pdf_00001.pdf")
        """
        # Extract filename from URL if possible
        try:
            parsed_url = url.split("/")[-1]
            if parsed_url and len(parsed_url) > 3:
                # Remove query parameters and invalid characters
                filename = parsed_url.split("?")[0]
                # Keep only alphanumeric, dash, underscore, dot
                filename = "".join(
                    c if c.isalnum() or c in ".-_" else "_" for c in filename
                )
                if filename.lower().endswith(".pdf"):
                    return filename[:100]  # Limit length
        except Exception:
            pass

        # Fallback: use index-based naming
        return f"pdf_{index:05d}.pdf"

    def download_pdf(
        self, url: str, save_path: str, safe_filename: bool = True
    ) -> Optional[str]:
        """
        Download single PDF from URL with validation.

        Args:
            url: PDF URL to download
            save_path: Directory to save PDF
            safe_filename: Whether to generate safe filename (default: True)

        Returns:
            Path to downloaded file if successful, None otherwise
        """
        if not url or not isinstance(url, str):
            pipeline_logger.error(f"Invalid URL: {url}")
            return None

        try:
            pipeline_logger.debug(f"Downloading: {url[:80]}...")

            # Make request with streaming
            response = requests.get(
                url,
                timeout=self.timeout,
                verify=self.verify_ssl,
                allow_redirects=True,
                stream=True,
            )

            # Check HTTP status
            if response.status_code != 200:
                pipeline_logger.warning(
                    f"HTTP {response.status_code} for {url[:80]}"
                )
                return None

            # Check content type (if available)
            content_type = response.headers.get("content-type", "").lower()
            if content_type and "pdf" not in content_type and "application" not in content_type:
                pipeline_logger.warning(
                    f"Non-PDF content type '{content_type}' for {url[:80]}"
                )
                return None

            # Generate filename
            if safe_filename:
                filename = self._generate_safe_filename(url, 0)
            else:
                filename = url.split("/")[-1].split("?")[0] or "document.pdf"

            file_path = os.path.join(save_path, filename)

            # Check if file already exists (skip)
            if os.path.exists(file_path):
                pipeline_logger.info(f"File already exists: {filename}")
                return file_path  # Return path but note skipped in caller

            # Write file
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Validate PDF header
            if not self._validate_pdf_header(file_path):
                pipeline_logger.warning(f"Invalid PDF downloaded: {filename}")
                os.remove(file_path)
                return None

            file_size = os.path.getsize(file_path)
            pipeline_logger.info(
                f"✓ Downloaded: {filename} ({file_size:,} bytes)"
            )
            return file_path

        except requests.exceptions.Timeout:
            pipeline_logger.error(f"Timeout downloading: {url[:80]}")
            return None
        except requests.exceptions.ConnectionError:
            pipeline_logger.error(f"Connection error: {url[:80]}")
            return None
        except Exception as e:
            pipeline_logger.error(f"Error downloading {url[:80]}: {e}")
            return None

    def download_multiple(
        self, pdf_links: List[str], year: int = None
    ) -> DownloadResult:
        """
        Download multiple PDFs with deduplication and logging.

        Features:
        - Deduplicates URLs
        - Creates year-based directories
        - Validates each PDF
        - Tracks results
        - Continues on errors (no silent failures)

        Args:
            pdf_links: List of PDF URLs to download
            year: Year for directory organization (default: current year)

        Returns:
            DownloadResult with detailed statistics
        """
        result = DownloadResult()

        if not pdf_links:
            pipeline_logger.warning("No PDF links to download")
            return result

        if year is None:
            year = datetime.now().year

        # Deduplicate URLs
        unique_links = []
        seen = set()
        for link in pdf_links:
            if link and link not in seen:
                unique_links.append(link)
                seen.add(link)

        result.total_urls = len(pdf_links)
        result.unique_urls = len(unique_links)

        pipeline_logger.info("=" * 70)
        pipeline_logger.info(f"DOWNLOADING {len(unique_links)} PDFs FOR YEAR {year}")
        pipeline_logger.info(f"(from {len(pdf_links)} total URLs)")
        pipeline_logger.info("=" * 70)

        # Create directory
        save_dir = Path("data") / "raw_pdfs" / str(year)
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
            pipeline_logger.info(f"✓ Directory ready: {save_dir}")
        except Exception as e:
            pipeline_logger.error(f"Failed to create directory {save_dir}: {e}")
            return result

        # Download each PDF
        for i, url in enumerate(unique_links, 1):
            # Generate safe filename for this iteration
            filename = self._generate_safe_filename(url, i)
            file_path = os.path.join(save_dir, filename)

            # Check if already exists
            if os.path.exists(file_path):
                pipeline_logger.info(f"[{i}/{len(unique_links)}] Skipping (exists): {filename}")
                result.skipped_existing += 1
                result.downloaded_files.append(file_path)
                continue

            # Download
            pipeline_logger.info(f"[{i}/{len(unique_links)}] Downloading...")
            downloaded = self.download_pdf(url, str(save_dir))

            if downloaded:
                result.successful_downloads += 1
                result.downloaded_files.append(downloaded)
            else:
                result.failed_downloads += 1
                result.failed_urls.append(url)
                pipeline_logger.error(f"  Failed: {url[:80]}")
                # Continue on error (no exceptions raised)

        # Log results
        pipeline_logger.info(result.summary())

        return result
