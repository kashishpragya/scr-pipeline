"""
ACQUISITION - Main Entry Point

Command-line interface for PDF acquisition

Usage:
    python -m src.acquisition.run_acquisition --year 2010
    python -m src.acquisition.run_acquisition --year 2010 --dry-run
    python -m src.acquisition.run_acquisition --year 2010 --force-redownload
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from config.settings import RAW_PDFs_DIR
from src.utils import (
    pipeline_logger,
    failures_logger,
    log_phase_start,
    log_phase_end,
    get_year_directory,
    save_json,
    validate_year,
    validate_url,
)

from src.acquisition.scr_pdf_fetcher import (
    get_fetcher,
    PDFSourceProvider,
)
from src.acquisition.scr_pdf_validator import PDFValidator


class AcquisitionPipeline:
    """Orchestrate PDF acquisition for a given year."""

    def __init__(self, year: int):
        """
        Initialize acquisition pipeline.

        Args:
            year: Year to acquire PDFs for

        Raises:
            ValueError: If year is invalid
        """
        # Validate year parameter
        is_valid, error_msg = validate_year(year)
        if not is_valid:
            raise ValueError(f"Invalid year: {error_msg}")

        self.year = year
        self.execution_log = {
            "year": year,
            "start_time": datetime.now().isoformat(),
            "status": "not_started",
            "phases": {},
            "total_pdfs_attempted": 0,
            "total_pdfs_acquired": 0,
            "total_pdfs_skipped": 0,
            "total_pdfs_failed": 0,
        }

    def run_acquisition(
        self,
        dry_run: bool = False,
        force_redownload: bool = False,
    ) -> bool:
        """
        Run the complete acquisition pipeline.

        Args:
            dry_run: If True, do not download (just log what would happen)
            force_redownload: Re-download even if PDFs exist

        Returns:
            True if successful, False otherwise
        """
        pipeline_logger.info("=" * 70)
        pipeline_logger.info(f"STARTING PDF ACQUISITION FOR YEAR {self.year}")
        if dry_run:
            pipeline_logger.info("DRY RUN MODE - No files will be downloaded")
        pipeline_logger.info("=" * 70)

        try:
            # Phase 0: Setup
            self.phase_0_setup()

            # Phase 1: Discover sources
            sources = self.phase_1_discover_sources()

            if not sources:
                pipeline_logger.error(
                    f"No PDF sources registered for year {self.year}. "
                    "Cannot proceed with acquisition."
                )
                self.execution_log["status"] = "no_sources"
                return False

            # Phase 2: Download and validate PDFs
            success = self.phase_2_acquire_pdfs(
                sources,
                dry_run=dry_run,
                force_redownload=force_redownload,
            )

            if not success:
                pipeline_logger.error(f"Acquisition failed for year {self.year}")
                self.execution_log["status"] = "failed"
                return False

            # Log completion
            self.execution_log["end_time"] = datetime.now().isoformat()
            self.execution_log["status"] = "success"

            pipeline_logger.info("=" * 70)
            pipeline_logger.info(f"ACQUISITION COMPLETED SUCCESSFULLY")
            pipeline_logger.info(f"Year: {self.year}")
            pipeline_logger.info(f"PDFs acquired: {self.execution_log['total_pdfs_acquired']}")
            pipeline_logger.info(f"PDFs skipped: {self.execution_log['total_pdfs_skipped']}")
            pipeline_logger.info(f"PDFs failed: {self.execution_log['total_pdfs_failed']}")
            pipeline_logger.info("=" * 70)

            return True

        except Exception as e:
            pipeline_logger.error(f"ACQUISITION FAILED: {e}")
            self.execution_log["status"] = "error"
            self.execution_log["error"] = str(e)
            self.execution_log["end_time"] = datetime.now().isoformat()
            return False

        finally:
            # Save execution log
            self.save_execution_log()

    def phase_0_setup(self):
        """Phase 0: Initialize directories and logging."""
        log_phase_start(0, "Acquisition Setup")

        year_dir = get_year_directory(RAW_PDFs_DIR, self.year)

        pipeline_logger.info(f"Target directory: {year_dir}")
        pipeline_logger.info(f"Existing PDFs will be skipped to avoid re-downloading")

        self.execution_log["phases"]["phase_0"] = {
            "status": "complete",
            "target_directory": str(year_dir),
        }

        log_phase_end(0, "Acquisition Setup")

    def phase_1_discover_sources(self) -> List[str]:
        """
        Phase 1: Discover available PDF sources for the year.

        Returns:
            List of PDF URLs
        """
        log_phase_start(1, "PDF Source Discovery")

        # Get registered sources for this year
        sources = PDFSourceProvider.get_sources_for_year(self.year)

        if sources:
            pipeline_logger.info(f"Found {len(sources)} source(s) for year {self.year}")
            for i, url in enumerate(sources, 1):
                pipeline_logger.debug(f"  Source {i}: {url}")
        else:
            pipeline_logger.warning(f"No sources registered for year {self.year}")

        self.execution_log["phases"]["phase_1"] = {
            "status": "complete",
            "sources_discovered": len(sources),
        }

        log_phase_end(1, "PDF Source Discovery", f"Found {len(sources)} source(s)")

        return sources

    def phase_2_acquire_pdfs(
        self,
        sources: List[str],
        dry_run: bool = False,
        force_redownload: bool = False,
    ) -> bool:
        """
        Phase 2: Download and validate PDFs.

        Args:
            sources: List of PDF URLs
            dry_run: If True, do not download
            force_redownload: Re-download even if exists

        Returns:
            True if successful
        """
        log_phase_start(2, "PDF Download & Validation")

        if dry_run:
            pipeline_logger.info("DRY RUN: Simulating downloads...")

        fetcher = get_fetcher()
        validator = PDFValidator()

        acquired_count = 0
        skipped_count = 0
        failed_count = 0

        for i, url in enumerate(sources, 1):
            pipeline_logger.info(f"Processing source {i}/{len(sources)}")

            # Validate URL format
            is_valid_url, url_error = validate_url(url)
            if not is_valid_url:
                pipeline_logger.error(f"Invalid URL: {url_error}")
                failed_count += 1
                continue

            # Extract filename from URL
            pdf_name = self.extract_pdf_name_from_url(url)

            if not pdf_name:
                pipeline_logger.warning(f"Could not extract filename from URL: {url}")
                failed_count += 1
                continue

            if dry_run:
                pipeline_logger.info(f"  [DRY RUN] Would download: {pdf_name}")
                acquired_count += 1
            else:
                # Download the PDF
                success, pdf_path, error = fetcher.fetch_pdf(
                    url,
                    pdf_name,
                    self.year,
                    force_redownload=force_redownload,
                )

                if not success:
                    pipeline_logger.error(f"Failed to download {pdf_name}: {error}")
                    failed_count += 1
                    continue

                # Handle skipped (already exists)
                if pdf_path is None:
                    skipped_count += 1
                    continue

                # Validate the downloaded PDF
                is_valid, report = validator.validate_pdf(pdf_path)

                if not is_valid:
                    pipeline_logger.error(
                        f"Downloaded PDF {pdf_name} failed validation: {report['errors']}"
                    )
                    failed_count += 1
                    continue

                acquired_count += 1

        # Get statistics
        fetcher_stats = fetcher.get_fetch_stats()

        self.execution_log["total_pdfs_attempted"] = fetcher_stats["total_pdfs_attempted"]
        self.execution_log["total_pdfs_acquired"] = acquired_count
        self.execution_log["total_pdfs_skipped"] = skipped_count + fetcher_stats["skipped_existing"]
        self.execution_log["total_pdfs_failed"] = failed_count

        self.execution_log["phases"]["phase_2"] = {
            "status": "complete",
            "sources_attempted": len(sources),
            "pdfs_acquired": acquired_count,
            "pdfs_skipped": skipped_count + fetcher_stats["skipped_existing"],
            "pdfs_failed": failed_count,
            "dry_run": dry_run,
        }

        summary = (
            f"Acquired {acquired_count} PDFs, "
            f"skipped {skipped_count + fetcher_stats['skipped_existing']}, "
            f"failed {failed_count}"
        )

        log_phase_end(2, "PDF Download & Validation", summary)

        return True  # Phase completes successfully even if some downloads failed

    def extract_pdf_name_from_url(self, url: str) -> str:
        """
        Extract PDF filename from URL.

        Args:
            url: URL to extract from

        Returns:
            PDF filename
        """
        # Try to extract from URL path
        path_part = url.split("?")[0]  # Remove query parameters
        filename = path_part.split("/")[-1]  # Get last path segment

        # Ensure it has .pdf extension
        if not filename.lower().endswith(".pdf"):
            # Try to construct a reasonable filename
            # This is a fallback; ideally URLs should have proper filenames
            filename = None

        return filename

    def save_execution_log(self):
        """Save execution log to file."""
        try:
            from config.settings import LOGS_DIR

            log_file = LOGS_DIR / f"acquisition_log_{self.year}.json"
            save_json(self.execution_log, log_file, pretty=True)

            pipeline_logger.debug(f"Saved acquisition log to: {log_file}")

        except Exception as e:
            failures_logger.error(f"Failed to save execution log: {e}")


def main():
    """Main entry point for acquisition module."""
    parser = argparse.ArgumentParser(description="Acquire SCR PDFs for a specific year")

    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Year to acquire PDFs for (e.g., 2010)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate acquisition without downloading",
    )

    parser.add_argument(
        "--force-redownload",
        action="store_true",
        help="Re-download PDFs even if they already exist",
    )

    parser.add_argument(
        "--show-sources",
        action="store_true",
        help="Show registered PDF sources and exit",
    )

    args = parser.parse_args()

    # Show sources if requested
    if args.show_sources:
        pipeline_logger.info("=" * 70)
        pipeline_logger.info("REGISTERED PDF SOURCES")
        pipeline_logger.info("=" * 70)

        all_sources = PDFSourceProvider.KNOWN_SOURCES

        if not all_sources:
            pipeline_logger.info("No sources registered.")
        else:
            for year in sorted(all_sources.keys()):
                urls = all_sources[year]
                pipeline_logger.info(f"\nYear {year}: {len(urls)} source(s)")
                for url in urls:
                    pipeline_logger.info(f"  - {url}")

        return 0

    # Run acquisition
    pipeline = AcquisitionPipeline(args.year)

    success = pipeline.run_acquisition(
        dry_run=args.dry_run,
        force_redownload=args.force_redownload,
    )

    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as e:
        pipeline_logger.error(f"Invalid input parameter: {e}")
        sys.exit(1)
    except Exception as e:
        failures_logger.error(f"Acquisition failed: {e}")
        sys.exit(1)
