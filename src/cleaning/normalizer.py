"""
CLEANING - Normalizer

Phase 5: Clean and normalize extracted metadata

Tasks:
- Normalize judge names (remove titles, standardize)
- Canonicalize Act names
- Normalize Section citations
- Deduplicate conservatively
- Remove editorial noise
"""

import re
from typing import List, Dict
from difflib import SequenceMatcher

from config.constants import (
    JUDGE_TITLE_PREFIXES,
    ACT_SYNONYMS,
)
from src.utils import (
    pipeline_logger,
    normalize_spacing,
    deduplicate_list,
    normalize_list_items,
)


class Normalizer:
    """Normalize and clean metadata."""

    def __init__(self):
        """Initialize normalizer."""
        self.normalization_stats = {
            "judges_normalized": 0,
            "acts_normalized": 0,
            "sections_normalized": 0,
            "duplicates_removed": 0,
        }

    # ==================== JUDGE NORMALIZATION ====================

    def normalize_judge_name(self, name: str) -> str:
        """
        Normalize judge name by removing titles and standardizing format.

        Rules:
        - Remove titles (Hon'ble, Justice, Dr., etc.)
        - Remove trailing periods
        - Normalize spacing
        - Capitalize properly

        Args:
            name: Raw judge name

        Returns:
            Normalized judge name
        """
        name = name.strip()

        if not name:
            return ""

        # Remove common prefixes
        for prefix in JUDGE_TITLE_PREFIXES:
            pattern = re.compile(f"^{re.escape(prefix)}\\s+", re.IGNORECASE)
            name = pattern.sub("", name)

        # Remove trailing periods
        name = re.sub(r"\.$", "", name)

        # Remove multiple spaces
        name = normalize_spacing(name)

        # Remove parenthetical info
        name = re.sub(r"\s*\([^)]+\)", "", name)

        # Capitalize properly: "JOHN DOE" -> "John Doe"
        if name and name.isupper():
            name = " ".join(word.capitalize() for word in name.split())

        return name

    def normalize_judges(self, judges: List[str]) -> List[str]:
        """
        Normalize a list of judge names.

        Args:
            judges: List of raw judge names

        Returns:
            List of normalized judge names
        """
        normalized = []

        for judge in judges:
            norm_judge = self.normalize_judge_name(judge)
            if norm_judge and norm_judge not in normalized:
                normalized.append(norm_judge)

        self.normalization_stats["judges_normalized"] += len(normalized)

        return normalized

    # ==================== ACT NORMALIZATION ====================

    def canonicalize_act(self, act: str) -> str:
        """
        Canonicalize act name to standard form.

        Rules:
        - Use standard Act name + year
        - Handle abbreviations (IPC, CPC, etc.)
        - Remove redundant info

        Args:
            act: Raw act name

        Returns:
            Canonical act name
        """
        act = act.strip()

        if not act:
            return ""

        # Check against known synonyms
        for key, canonical in ACT_SYNONYMS.items():
            if key.lower() in act.lower():
                return canonical

        # If not in synonyms, try to standardize manually
        # Extract year if present
        year_match = re.search(r"(19|20)\d{2}", act)
        year = year_match.group(0) if year_match else ""

        # Remove year from act name temporarily
        act_name = re.sub(r",?\s*(19|20)\d{2}", "", act)

        # Normalize spacing
        act_name = normalize_spacing(act_name)

        # Capitalize properly
        act_name = act_name.title()

        # Reconstruct with year
        if year:
            return f"{act_name}, {year}"
        else:
            return act_name

    def normalize_acts(self, acts: List[str]) -> List[str]:
        """
        Normalize a list of acts.

        Args:
            acts: List of raw act names

        Returns:
            List of normalized act names
        """
        normalized = []

        for act in acts:
            canon_act = self.canonicalize_act(act)
            if canon_act and canon_act not in normalized:
                normalized.append(canon_act)

        self.normalization_stats["acts_normalized"] += len(normalized)

        return normalized

    # ==================== SECTION NORMALIZATION ====================

    def normalize_section(self, section: str) -> str:
        """
        Normalize section citation to standard format.

        Rules:
        - Use "Section X" format
        - Handle subsections (e.g., 498A)
        - Remove extra spaces

        Args:
            section: Raw section citation

        Returns:
            Normalized section
        """
        section = section.strip()

        if not section:
            return ""

        # Extract just the numeric/alpha part
        match = re.match(r"(\d+[A-Za-z]*)", section)

        if match:
            section_num = match.group(1)
            return f"Section {section_num}"

        return section

    def normalize_sections(self, sections: List[str]) -> List[str]:
        """
        Normalize a list of sections.

        Args:
            sections: List of raw section citations

        Returns:
            List of normalized sections
        """
        normalized = []

        for section in sections:
            norm_section = self.normalize_section(section)
            if norm_section and norm_section not in normalized:
                normalized.append(norm_section)

        self.normalization_stats["sections_normalized"] += len(normalized)

        return normalized

    # ==================== DEDUPLICATION ====================

    def similarity_ratio(self, s1: str, s2: str) -> float:
        """
        Calculate similarity ratio between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

    def deduplicate_fuzzy(self, items: List[str], threshold: float = 0.95) -> List[str]:
        """
        Deduplicate items using fuzzy matching.

        Only removes items that are >95% similar (very conservative).

        Args:
            items: List of items
            threshold: Similarity threshold

        Returns:
            Deduplicated list
        """
        if not items:
            return []

        deduplicated = []
        removed_count = 0

        for item in items:
            # Check if already in list (fuzzy)
            found_duplicate = False

            for existing in deduplicated:
                if self.similarity_ratio(item, existing) >= threshold:
                    found_duplicate = True
                    removed_count += 1
                    break

            if not found_duplicate:
                deduplicated.append(item)

        if removed_count > 0:
            self.normalization_stats["duplicates_removed"] += removed_count

        return deduplicated

    # ==================== FULL NORMALIZATION ====================

    def normalize_case(self, case: Dict) -> Dict:
        """
        Normalize all metadata in a case dictionary.

        Args:
            case: Case dictionary from extractor

        Returns:
            Normalized case dictionary
        """
        normalized = case.copy()

        # Normalize judges
        if case.get("judges"):
            normalized["judges"] = self.normalize_judges(case["judges"])
            normalized["judges"] = self.deduplicate_fuzzy(normalized["judges"])

        # Normalize acts
        if case.get("acts_referred"):
            normalized["acts_referred"] = self.normalize_acts(case["acts_referred"])
            normalized["acts_referred"] = self.deduplicate_fuzzy(normalized["acts_referred"])

        # Normalize sections
        if case.get("sections_referred"):
            normalized["sections_referred"] = self.normalize_sections(case["sections_referred"])
            normalized["sections_referred"] = self.deduplicate_fuzzy(
                normalized["sections_referred"]
            )

        # Normalize case name (trim, remove extra spaces)
        if case.get("case_name"):
            normalized["case_name"] = normalize_spacing(case["case_name"])

        return normalized

    def normalize_cases(self, cases: List[Dict]) -> List[Dict]:
        """
        Normalize a list of cases.

        Args:
            cases: List of case dictionaries

        Returns:
            List of normalized case dictionaries
        """
        normalized_cases = []

        for case in cases:
            normalized = self.normalize_case(case)
            normalized_cases.append(normalized)

        return normalized_cases

    def get_normalization_stats(self) -> Dict:
        """Get normalization statistics."""
        return self.normalization_stats.copy()


def normalize_extracted_cases(cases: List[Dict]) -> List[Dict]:
    """
    Main entry point: Normalize all extracted cases.

    Args:
        cases: List of case dictionaries from extractor

    Returns:
        List of normalized case dictionaries
    """
    from src.utils import log_phase_start, log_phase_end

    log_phase_start(5, "Data Cleaning & Normalization")

    normalizer = Normalizer()
    normalized = normalizer.normalize_cases(cases)

    stats = normalizer.get_normalization_stats()

    summary = (
        f"Normalized {len(normalized)} cases: "
        f"{stats['judges_normalized']} judges, "
        f"{stats['acts_normalized']} acts, "
        f"{stats['sections_normalized']} sections"
    )

    log_phase_end(5, "Data Cleaning & Normalization", summary)

    return normalized


if __name__ == "__main__":
    # Test normalization
    test_case = {
        "court": "Supreme Court of India",
        "case_number": "",
        "petition_type": "",
        "petition_format": "",
        "judges": [
            "Hon'ble Justice A. K. Goel",
            "Justice A. K. Goel",  # Duplicate
            "Justice U. U. Lalit",
        ],
        "petitioner": [],
        "respondent": [],
        "case_name": "RAJESH KUMAR   v.   THE STATE OF MAHARASHTRA",
        "acts_referred": [
            "Indian Penal Code, 1860",
            "IPC",  # Duplicate/synonym
        ],
        "sections_referred": [
            "Section 498A",
            "498A",  # Variant form
        ],
        "subject_categories": [],
    }

    normalizer = Normalizer()
    normalized = normalizer.normalize_case(test_case)

    print("Original judges:", test_case["judges"])
    print("Normalized judges:", normalized["judges"])
    print()
    print("Original acts:", test_case["acts_referred"])
    print("Normalized acts:", normalized["acts_referred"])
    print()
    print("Original sections:", test_case["sections_referred"])
    print("Normalized sections:", normalized["sections_referred"])
    print()
    print("Original case name:", test_case["case_name"])
    print("Normalized case name:", normalized["case_name"])
