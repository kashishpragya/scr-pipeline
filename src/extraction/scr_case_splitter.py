"""
EXTRACTION - SCR Case Splitter

Phase 3: Split SCR volume text into individual cases

Key Principle: SCR PDFs contain multiple cases per volume.
Use conservative anchors to split:
- Case title in CAPS
- "v." or "vs." separators
- Judge brackets (CORAM, Bench)
- Do NOT merge cases
- Log ambiguous splits
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from config.constants import CASE_SPLIT_MARKERS, MIN_CASE_TEXT_LENGTH
from config.settings import EXTRACTED_TEXT_DIR, RAW_PDFs_DIR
from src.utils import (
    pipeline_logger,
    failures_logger,
    extract_lines,
    is_all_caps,
    get_year_directory,
    remove_page_markers,
)


@dataclass
class CaseBlock:
    """Represents a single extracted case block."""

    start_line: int
    end_line: int
    text: str
    confidence: str  # "high", "medium", "low"
    markers_found: List[str]
    notes: List[str]


class SCRCaseSplitter:
    """Split SCR volume text into individual cases."""

    def __init__(self):
        """Initialize splitter."""
        self.split_stats = {
            "total_volumes": 0,
            "total_cases": 0,
            "ambiguous_splits": 0,
            "failed_volumes": 0,
        }

        # Compile regex patterns for efficiency
        self.coram_pattern = re.compile(
            r"\[.*?[Cc]oram.*?\]|\([Cc]oram:.*?\)|[Bb]ench:.*?[:\[]", re.IGNORECASE
        )
        self.vs_pattern = re.compile(r"\s+v\.?\s+|\s+vs\.?\s+", re.IGNORECASE)

    def detect_case_boundary(self, lines: List[str], line_idx: int) -> Tuple[bool, Dict]:
        """
        Detect if a line is likely a case boundary.

        Markers:
        - Line is all CAPS (case title)
        - Contains "v." or "vs."
        - Contains CORAM/Bench information

        Args:
            lines: All lines of text
            line_idx: Current line index

        Returns:
            Tuple of (is_boundary, markers_dict)
        """
        line = lines[line_idx].strip()

        if not line:
            return False, {}

        markers = {
            "all_caps": False,
            "vs_pattern": False,
            "coram": False,
            "combined": False,
        }

        # Check if line is all caps (case title indicator)
        if is_all_caps(line) and len(line) > 10:
            markers["all_caps"] = True

        # Check for "v." or "vs." (case separator)
        if self.vs_pattern.search(line):
            markers["vs_pattern"] = True

        # Check for CORAM/Bench (judge marker)
        if self.coram_pattern.search(line):
            markers["coram"] = True

        # Combined marker: all_caps + vs = strong indicator
        if markers["all_caps"] and markers["vs_pattern"]:
            markers["combined"] = True

        # A line is a boundary if it has at least one marker
        is_boundary = any(
            [
                markers["all_caps"],
                markers["vs_pattern"],
                markers["coram"],
            ]
        )

        return is_boundary, markers

    def split_volume_text(self, text: str, volume_name: str = "") -> List[CaseBlock]:
        """
        Split volume text into case blocks using conservative anchors.

        Args:
            text: Full volume text
            volume_name: Name of volume (for logging)

        Returns:
            List of CaseBlock objects
        """
        lines = extract_lines(text, strip=False)  # Keep line structure

        if not lines:
            failures_logger.error(f"No lines extracted from {volume_name}")
            return []

        # Clean and analyze lines
        lines = [line.rstrip() for line in lines]

        cases = []
        current_case_start = 0
        current_markers = []

        for line_idx, line in enumerate(lines):
            is_boundary, markers = self.detect_case_boundary(lines, line_idx)

            if is_boundary:
                # If we have a previous case, save it
                if line_idx > current_case_start:
                    case_text = "\n".join(lines[current_case_start:line_idx])

                    if len(case_text.strip()) >= MIN_CASE_TEXT_LENGTH:
                        case = CaseBlock(
                            start_line=current_case_start,
                            end_line=line_idx,
                            text=case_text,
                            confidence="medium" if current_markers else "low",
                            markers_found=current_markers,
                            notes=[],
                        )
                        cases.append(case)

                # Start new case
                current_case_start = line_idx
                current_markers = [k for k, v in markers.items() if v]
            else:
                # Accumulate current case markers
                _, markers = self.detect_case_boundary(lines, line_idx)
                for k, v in markers.items():
                    if v and k not in current_markers:
                        current_markers.append(k)

        # Don't forget the last case
        if current_case_start < len(lines):
            case_text = "\n".join(lines[current_case_start:])

            if len(case_text.strip()) >= MIN_CASE_TEXT_LENGTH:
                case = CaseBlock(
                    start_line=current_case_start,
                    end_line=len(lines),
                    text=case_text,
                    confidence="medium" if current_markers else "low",
                    markers_found=current_markers,
                    notes=["final_case"],
                )
                cases.append(case)

        # Log splitting results
        if len(cases) == 1:
            pipeline_logger.debug(f"{volume_name}: Single case detected (entire volume)")
        elif len(cases) > 1:
            pipeline_logger.info(f"{volume_name}: Split into {len(cases)} cases")
        else:
            pipeline_logger.warning(f"{volume_name}: No cases extracted")

        # Check for ambiguous splits
        low_confidence = [c for c in cases if c.confidence == "low"]
        if low_confidence:
            pipeline_logger.warning(
                f"{volume_name}: {len(low_confidence)} cases with LOW confidence"
            )
            for i, case in enumerate(low_confidence, 1):
                failures_logger.warning(
                    f"{volume_name}: Low confidence case {i}: {case.text[:100]}"
                )

        return cases

    def process_extracted_text_file(
        self,
        text_path: Path,
        year: int,
    ) -> List[CaseBlock]:
        """
        Process an extracted text file and split into cases.

        Args:
            text_path: Path to extracted text file
            year: Year for context

        Returns:
            List of CaseBlock objects
        """
        try:
            with open(text_path, "r", encoding="utf-8") as f:
                text = f.read()

            # Remove page markers and noise
            text = remove_page_markers(text)

            cases = self.split_volume_text(text, text_path.name)

            self.split_stats["total_volumes"] += 1
            self.split_stats["total_cases"] += len(cases)

            return cases

        except Exception as e:
            failures_logger.error(f"Failed to process {text_path}: {e}")
            self.split_stats["failed_volumes"] += 1
            return []

    def process_year_extracted_text(self, year: int) -> Dict[str, List[CaseBlock]]:
        """
        Process all extracted text files for a year.

        Args:
            year: Year to process

        Returns:
            Dict mapping filename to list of CaseBlocks
        """
        year_dir = get_year_directory(EXTRACTED_TEXT_DIR, year)

        if not year_dir.exists():
            pipeline_logger.error(f"Extracted text directory not found: {year_dir}")
            return {}

        # Find all text files
        text_files = list(year_dir.glob("*.txt"))

        if not text_files:
            pipeline_logger.warning(f"No extracted text files found in {year_dir}")
            return {}

        pipeline_logger.info(f"Processing {len(text_files)} text files from {year}")

        results = {}

        for text_path in text_files:
            cases = self.process_extracted_text_file(text_path, year)
            if cases:
                results[text_path.name] = cases

        return results

    def get_split_stats(self) -> Dict:
        """Get splitting statistics."""
        return self.split_stats.copy()


def split_cases_for_year(year: int):
    """
    Main entry point: Split all cases for a year.

    Args:
        year: Year to process
    """
    from src.utils import log_phase_start, log_phase_end

    log_phase_start(3, "SCR Case Splitting")

    splitter = SCRCaseSplitter()
    results = splitter.process_year_extracted_text(year)

    stats = splitter.get_split_stats()

    summary = f"Split {stats['total_volumes']} volumes into {stats['total_cases']} cases"
    if stats["ambiguous_splits"] > 0:
        summary += f", {stats['ambiguous_splits']} ambiguous"

    log_phase_end(3, "SCR Case Splitting", summary)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Split SCR volume text into cases")
    parser.add_argument("--year", type=int, required=True, help="Year to process")
    parser.add_argument(
        "--volume",
        type=str,
        help="Specific volume filename (optional, process all if not specified)",
    )

    args = parser.parse_args()

    if args.volume:
        # Process single volume
        year_dir = get_year_directory(EXTRACTED_TEXT_DIR, args.year)
        text_path = year_dir / args.volume

        splitter = SCRCaseSplitter()
        cases = splitter.process_extracted_text_file(text_path, args.year)

        pipeline_logger.info(f"Split {args.volume} into {len(cases)} cases")

        for i, case in enumerate(cases, 1):
            pipeline_logger.debug(
                f"Case {i}: {case.confidence} confidence, "
                f"{len(case.text)} chars, markers: {case.markers_found}"
            )
    else:
        # Process all volumes for year
        split_cases_for_year(args.year)
