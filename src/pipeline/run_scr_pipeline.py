"""
PIPELINE - Main Orchestrator

Coordinates all phases of the SCR extraction pipeline:

Phase 0: Environment & Setup
Phase 1: Assisted PDF Discovery
Phase 2: PDF Text Extraction
Phase 3: SCR Case Splitting
Phase 4: Metadata Extraction
Phase 5: Cleaning & Normalization
Phase 6: Final JSON Output
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from config.settings import (
    OUTPUT_DIR,
    RAW_PDFs_DIR,
    EXTRACTED_TEXT_DIR,
    LOGS_DIR,
    PRETTY_JSON,
    JSON_INDENT,
)
from config.constants import SCR_CASE_SCHEMA

from src.utils import (
    pipeline_logger,
    failures_logger,
    get_year_directory,
    save_json,
    load_json,
    log_phase_start,
    log_phase_end,
    validate_case_schema,
    validate_year,
    create_checkpoint,
    load_checkpoint,
    can_skip_phase,
)

from src.automation.scr_pdf_discovery import discover_pdfs_for_year
from src.extraction.pdf_text_extractor import extract_text_from_pdf
from src.extraction.scr_case_splitter import SCRCaseSplitter
from src.extraction.scr_metadata_extractor import SCRMetadataExtractor
from src.cleaning.normalizer import Normalizer


class SCRPipeline:
    """Main SCR extraction pipeline orchestrator."""

    def __init__(self, year: int):
        """
        Initialize pipeline.

        Args:
            year: Year to process

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
            "phases": {},
            "total_cases_extracted": 0,
            "final_output_path": None,
            "checkpoints_used": [],
            "errors_encountered": [],
        }

    def execute_phase(self, phase_num: int, phase_func, *args, **kwargs):
        """
        Execute a phase with error handling and checkpointing.

        Args:
            phase_num: Phase number
            phase_func: Phase function to execute
            *args: Arguments to pass to phase function
            **kwargs: Keyword arguments to pass to phase function

        Returns:
            Phase result or None if failed/skipped
        """
        try:
            # Check if phase can be skipped
            if can_skip_phase(self.year, phase_num):
                pipeline_logger.info(f"Phase {phase_num}: Loading from checkpoint...")
                checkpoint_data = load_checkpoint(self.year, phase_num)
                self.execution_log["checkpoints_used"].append(phase_num)
                return checkpoint_data

            # Execute phase
            result = phase_func(*args, **kwargs)

            # Create checkpoint after successful phase
            if result is not None:
                create_checkpoint(
                    self.year,
                    phase_num,
                    result if isinstance(result, dict) else {"status": "complete"},
                )

            return result

        except Exception as e:
            error_msg = f"Phase {phase_num} error: {str(e)}"
            pipeline_logger.error(error_msg)
            self.execution_log["errors_encountered"].append(
                {
                    "phase": phase_num,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            raise

    def phase_0_environment_setup(self):
        """Phase 0: Initialize environment and validate setup."""
        log_phase_start(0, "Environment & Setup")

        # Ensure all directories exist
        for dir_path in [
            get_year_directory(RAW_PDFs_DIR, self.year),
            get_year_directory(EXTRACTED_TEXT_DIR, self.year),
            OUTPUT_DIR,
            LOGS_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        pipeline_logger.info(
            f"Working directory for year {self.year}: {RAW_PDFs_DIR / str(self.year)}"
        )
        pipeline_logger.info(f"Output will be saved to: {OUTPUT_DIR / f'scr_{self.year}.json'}")

        self.execution_log["phases"]["phase_0"] = {
            "status": "complete",
            "directories_initialized": True,
        }

        log_phase_end(0, "Environment & Setup")

    def phase_1_pdf_discovery(self):
        """Phase 1: Discover and validate SCR PDFs."""
        log_phase_start(1, "Assisted SCR PDF Discovery")

        try:
            results = discover_pdfs_for_year(self.year)

            pdfs = results.get(self.year, [])
            valid_count = sum(1 for pdf in pdfs if pdf["is_valid"])

            self.execution_log["phases"]["phase_1"] = {
                "status": "complete",
                "pdfs_discovered": len(pdfs),
                "valid_pdfs": valid_count,
            }

            log_phase_end(1, "Assisted SCR PDF Discovery", f"Found {valid_count} valid PDFs")

        except Exception as e:
            failures_logger.error(f"Phase 1 failed: {e}")
            self.execution_log["phases"]["phase_1"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def phase_2_pdf_text_extraction(self) -> Dict[str, str]:
        """
        Phase 2: Extract text from PDFs.

        Returns:
            Dict mapping PDF filename to extracted text file path
        """
        log_phase_start(2, "PDF Text Extraction")

        extractor = PDFTextExtractor()

        try:
            year_pdf_dir = get_year_directory(RAW_PDFs_DIR, self.year)
            pdf_files = sorted(list(year_pdf_dir.glob("*.pdf")) + list(year_pdf_dir.glob("*.PDF")))

            if not pdf_files:
                pipeline_logger.warning(f"No PDFs found to extract")
                self.execution_log["phases"]["phase_2"] = {
                    "status": "complete",
                    "pdfs_processed": 0,
                    "pdfs_successful": 0,
                }
                return {}

            extracted_files = {}
            failed_pdfs = []

            for pdf_path in pdf_files:
                try:
                    result = extractor.process_pdf_file(pdf_path, self.year)
                    if result:
                        extracted_files[pdf_path.name] = str(result)
                except Exception as e:
                    error_msg = f"Failed to extract {pdf_path.name}: {str(e)}"
                    pipeline_logger.warning(error_msg)
                    failed_pdfs.append({"filename": pdf_path.name, "error": str(e)})

            stats = extractor.get_extraction_stats()

            self.execution_log["phases"]["phase_2"] = {
                "status": "complete",
                "pdfs_processed": stats["total_pdfs"],
                "pdfs_successful": stats["successful"],
                "pdfs_failed": stats["failed"],
                "total_pages": stats["total_pages"],
                "failed_pdfs": failed_pdfs[:10],  # Log first 10 failures
            }

            summary = f"Extracted {stats['successful']} PDFs, {stats['total_pages']} pages"
            log_phase_end(2, "PDF Text Extraction", summary)

            return extracted_files

        except Exception as e:
            failures_logger.error(f"Phase 2 failed: {e}")
            self.execution_log["phases"]["phase_2"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def phase_3_case_splitting(self, extracted_files: Dict[str, str]) -> Dict[str, List]:
        """
        Phase 3: Split extracted text into individual cases.

        Args:
            extracted_files: Dict from phase 2

        Returns:
            Dict mapping filename to list of CaseBlock objects
        """
        log_phase_start(3, "SCR Case Splitting")

        splitter = SCRCaseSplitter()

        try:
            year_text_dir = get_year_directory(EXTRACTED_TEXT_DIR, self.year)
            text_files = sorted(year_text_dir.glob("*.txt"))

            if not text_files:
                pipeline_logger.warning("No extracted text files found")
                self.execution_log["phases"]["phase_3"] = {
                    "status": "complete",
                    "volumes_processed": 0,
                    "cases_split": 0,
                }
                return {}

            all_cases = {}
            total_cases = 0
            failed_volumes = []

            for text_path in text_files:
                try:
                    cases = splitter.process_extracted_text_file(text_path, self.year)
                    if cases:
                        all_cases[text_path.name] = cases
                        total_cases += len(cases)
                except Exception as e:
                    error_msg = f"Failed to split {text_path.name}: {str(e)}"
                    pipeline_logger.warning(error_msg)
                    failed_volumes.append({"filename": text_path.name, "error": str(e)})

            stats = splitter.get_split_stats()

            self.execution_log["phases"]["phase_3"] = {
                "status": "complete",
                "volumes_processed": stats["total_volumes"],
                "cases_split": stats["total_cases"],
                "ambiguous_splits": stats.get("ambiguous_splits", 0),
                "failed_volumes": failed_volumes[:5],  # Log first 5 failures
            }

            summary = f"Split {stats['total_volumes']} volumes into {stats['total_cases']} cases"
            log_phase_end(3, "SCR Case Splitting", summary)

            return all_cases

        except Exception as e:
            failures_logger.error(f"Phase 3 failed: {e}")
            self.execution_log["phases"]["phase_3"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def phase_4_metadata_extraction(self, split_cases: Dict[str, List]) -> List[Dict]:
        """
        Phase 4: Extract metadata from cases.

        Args:
            split_cases: Dict from phase 3

        Returns:
            List of extracted case dictionaries
        """
        log_phase_start(4, "Metadata Extraction")

        extractor = SCRMetadataExtractor()

        try:
            all_cases = []
            failed_cases = []

            for volume_name, cases in split_cases.items():
                for case_idx, case in enumerate(cases):
                    try:
                        metadata = extractor.extract_metadata(case.text, volume_name)
                        case_dict = metadata.to_case_dict()
                        all_cases.append(case_dict)
                    except Exception as e:
                        error_detail = f"Volume: {volume_name}, Case: {case_idx}"
                        pipeline_logger.warning(
                            f"Failed to extract metadata for {error_detail}: {e}"
                        )
                        failed_cases.append(
                            {
                                "volume": volume_name,
                                "case_index": case_idx,
                                "error": str(e),
                            }
                        )
                        # Continue processing other cases
                        continue

            stats = extractor.get_extraction_stats()

            self.execution_log["phases"]["phase_4"] = {
                "status": "complete",
                "cases_processed": stats["total_cases"],
                "cases_extracted": len(all_cases),
                "cases_failed": len(failed_cases),
                "with_judges": stats["with_judges"],
                "with_acts": stats["with_acts"],
                "with_sections": stats["with_sections"],
                "failed_cases": failed_cases[:10],  # Log first 10 failures
            }

            summary = f"Extracted metadata from {len(all_cases)}/{stats['total_cases']} cases"
            if failed_cases:
                summary += f" ({len(failed_cases)} failures)"

            log_phase_end(4, "Metadata Extraction", summary)

            return all_cases

        except Exception as e:
            failures_logger.error(f"Phase 4 failed: {e}")
            self.execution_log["phases"]["phase_4"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def phase_5_normalization(self, extracted_cases: List[Dict]) -> List[Dict]:
        """
        Phase 5: Normalize and clean metadata.

        Args:
            extracted_cases: List from phase 4

        Returns:
            List of normalized case dictionaries
        """
        log_phase_start(5, "Data Cleaning & Normalization")

        normalizer = Normalizer()

        try:
            normalized_cases = normalizer.normalize_cases(extracted_cases)

            stats = normalizer.get_normalization_stats()

            self.execution_log["phases"]["phase_5"] = {
                "status": "complete",
                "cases_normalized": len(normalized_cases),
                "judges_normalized": stats["judges_normalized"],
                "acts_normalized": stats["acts_normalized"],
                "sections_normalized": stats["sections_normalized"],
            }

            summary = f"Normalized {len(normalized_cases)} cases"
            log_phase_end(5, "Data Cleaning & Normalization", summary)

            return normalized_cases

        except Exception as e:
            failures_logger.error(f"Phase 5 failed: {e}")
            self.execution_log["phases"]["phase_5"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def phase_6_json_output(self, normalized_cases: List[Dict]) -> Path:
        """
        Phase 6: Generate final JSON output with validation.

        Args:
            normalized_cases: List from phase 5

        Returns:
            Path to generated JSON file
        """
        log_phase_start(6, "Final JSON Output Generation")

        try:
            # Validate all cases and collect statistics
            invalid_cases = []
            case_stats = {
                "total_with_names": 0,
                "total_with_judges": 0,
                "total_with_acts": 0,
                "total_with_sections": 0,
            }

            for i, case in enumerate(normalized_cases):
                is_valid, errors = validate_case_schema(case)
                if not is_valid:
                    invalid_cases.append({"index": i, "errors": errors})
                    failures_logger.error(f"Case {i} validation failed: {errors}")
                else:
                    # Collect statistics on valid cases
                    if case.get("case_name"):
                        case_stats["total_with_names"] += 1
                    if case.get("judges"):
                        case_stats["total_with_judges"] += 1
                    if case.get("acts_referred"):
                        case_stats["total_with_acts"] += 1
                    if case.get("sections_referred"):
                        case_stats["total_with_sections"] += 1

            if invalid_cases:
                pipeline_logger.warning(f"{len(invalid_cases)} cases failed validation")

            # Save output
            output_filename = f"scr_{self.year}.json"
            output_path = OUTPUT_DIR / output_filename

            success = save_json(
                normalized_cases, output_path, pretty=PRETTY_JSON, indent=JSON_INDENT
            )

            if not success:
                raise Exception("Failed to save JSON output")

            # Verify file was written and is readable
            if not output_path.exists():
                raise Exception(f"Output file was not created: {output_path}")

            file_size = output_path.stat().st_size
            if file_size == 0:
                raise Exception("Output file is empty")

            # Create execution summary
            execution_summary = {
                "year": self.year,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "total_cases_extracted": len(normalized_cases),
                "invalid_cases": len(invalid_cases),
                "output_file": str(output_path),
                "output_file_size_bytes": file_size,
                "case_statistics": case_stats,
                "phases_completed": list(self.execution_log["phases"].keys()),
                "checkpoints_used": self.execution_log["checkpoints_used"],
                "errors_encountered": self.execution_log["errors_encountered"],
            }

            # Save summary
            summary_path = LOGS_DIR / f"execution_summary_{self.year}.json"
            save_json(execution_summary, summary_path, pretty=True)
            pipeline_logger.info(f"Saved execution summary to: {summary_path}")

            self.execution_log["phases"]["phase_6"] = {
                "status": "complete",
                "cases_output": len(normalized_cases),
                "output_file": str(output_path),
                "output_file_size": file_size,
                "invalid_cases": len(invalid_cases),
                "case_statistics": case_stats,
                "summary_file": str(summary_path),
            }

            self.execution_log["total_cases_extracted"] = len(normalized_cases)
            self.execution_log["final_output_path"] = str(output_path)

            summary = f"Wrote {len(normalized_cases)} valid cases to {output_filename} ({file_size} bytes)"
            log_phase_end(6, "Final JSON Output Generation", summary)

            return output_path

        except Exception as e:
            failures_logger.error(f"Phase 6 failed: {e}")
            self.execution_log["phases"]["phase_6"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def run_full_pipeline(self):
        """
        Run the complete pipeline for the year.

        Returns:
            Path to final output file
        """
        pipeline_logger.info("=" * 70)
        pipeline_logger.info(f"STARTING SCR PIPELINE FOR YEAR {self.year}")
        pipeline_logger.info("=" * 70)

        try:
            # Phase 0: Setup
            self.phase_0_environment_setup()

            # Phase 1: Discovery
            self.phase_1_pdf_discovery()

            # Phase 2: PDF Extraction
            extracted_files = self.phase_2_pdf_text_extraction()

            if not extracted_files:
                pipeline_logger.error("No PDFs were successfully extracted. Stopping pipeline.")
                return None

            # Phase 3: Case Splitting
            split_cases = self.phase_3_case_splitting(extracted_files)

            if not split_cases:
                pipeline_logger.error("No cases were split. Stopping pipeline.")
                return None

            # Phase 4: Metadata Extraction
            extracted_cases = self.phase_4_metadata_extraction(split_cases)

            if not extracted_cases:
                pipeline_logger.error("No metadata was extracted. Stopping pipeline.")
                return None

            # Phase 5: Normalization
            normalized_cases = self.phase_5_normalization(extracted_cases)

            # Phase 6: JSON Output
            output_path = self.phase_6_json_output(normalized_cases)

            # Log execution summary
            self.execution_log["end_time"] = datetime.now().isoformat()
            self.execution_log["status"] = "success"

            pipeline_logger.info("=" * 70)
            pipeline_logger.info(f"PIPELINE COMPLETED SUCCESSFULLY")
            pipeline_logger.info(
                f"Total cases extracted: {self.execution_log['total_cases_extracted']}"
            )
            pipeline_logger.info(f"Output file: {output_path}")
            if self.execution_log["checkpoints_used"]:
                pipeline_logger.info(f"Checkpoints used: {self.execution_log['checkpoints_used']}")
            pipeline_logger.info("=" * 70)

            # Save detailed execution log
            log_path = LOGS_DIR / f"execution_log_{self.year}.json"
            save_json(self.execution_log, log_path, pretty=True)
            pipeline_logger.debug(f"Saved execution log to: {log_path}")

            return output_path

        except Exception as e:
            self.execution_log["end_time"] = datetime.now().isoformat()
            self.execution_log["status"] = "failed"
            self.execution_log["error"] = str(e)

            pipeline_logger.error(f"PIPELINE FAILED: {e}")
            pipeline_logger.info("=" * 70)

            # Save detailed failed execution log
            log_path = LOGS_DIR / f"execution_log_{self.year}_failed.json"
            save_json(self.execution_log, log_path, pretty=True)
            pipeline_logger.debug(f"Saved failed execution log to: {log_path}")

            # Log recovery hints
            if self.execution_log["checkpoints_used"]:
                pipeline_logger.info(
                    f"Recovery: Checkpoints exist for phases: {self.execution_log['checkpoints_used']}"
                )
                pipeline_logger.info("Re-run the pipeline to recover from this point.")

            raise


def run_pipeline(year: int, phases: Optional[List[int]] = None):
    """
    Main entry point: Run the SCR extraction pipeline.

    Args:
        year: Year to process
        phases: Specific phases to run (if None, run all)
    """
    pipeline = SCRPipeline(year)

    if phases is None:
        # Run full pipeline
        output_path = pipeline.run_full_pipeline()
        if output_path:
            pipeline_logger.info(f"Successfully generated: {output_path}")
    else:
        # Run specific phases (not implemented in main entry, use phase scripts directly)
        pipeline_logger.info(
            "Run individual phase scripts directly: scr_pdf_discovery.py, pdf_text_extractor.py, etc."
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run SCR extraction pipeline")
    parser.add_argument("--year", type=int, required=True, help="Year to process")
    parser.add_argument(
        "--output-only",
        action="store_true",
        help="Skip extraction, just generate output from existing data",
    )

    args = parser.parse_args()

    try:
        run_pipeline(args.year)
    except ValueError as e:
        pipeline_logger.error(f"Invalid input: {e}")
        failures_logger.error(f"Pipeline initialization failed: {e}")
        exit(1)
    except Exception as e:
        failures_logger.error(f"Pipeline execution failed: {e}")
        exit(1)
