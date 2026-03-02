"""
Unit tests for SCR Case Splitter module.

Tests the logic for splitting SCR volume text into individual cases.
"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.scr_case_splitter import SCRCaseSplitter


class TestCaseBoundaryDetection:
    """Test case boundary detection logic."""
    
    def setup_method(self):
        """Setup splitter instance."""
        self.splitter = SCRCaseSplitter()
    
    def test_all_caps_detection(self):
        """Test detection of all-caps case titles."""
        lines = [
            "Some introduction text",
            "ABC v. XYZ",
            "More text here",
        ]
        
        is_boundary, markers = self.splitter.detect_case_boundary(lines, 1)
        
        assert is_boundary is True
        assert markers["all_caps"] is True
        assert markers["vs_pattern"] is True
    
    def test_coram_detection(self):
        """Test detection of CORAM/Bench information."""
        lines = [
            "Some text",
            "[Coram: Justice Smith]",
            "More text",
        ]
        
        is_boundary, markers = self.splitter.detect_case_boundary(lines, 1)
        
        assert is_boundary is True
        assert markers["coram"] is True
    
    def test_vs_pattern_detection(self):
        """Test detection of 'v.' or 'vs.' pattern."""
        lines = [
            "abc v. xyz",
            "def vs. ghi",
            "normal text",
        ]
        
        # Test lowercase v.
        is_boundary, markers = self.splitter.detect_case_boundary(lines, 0)
        assert markers["vs_pattern"] is True
        
        # Test vs.
        is_boundary, markers = self.splitter.detect_case_boundary(lines, 1)
        assert markers["vs_pattern"] is True
    
    def test_non_boundary_lines(self):
        """Test that regular text is not detected as boundary."""
        lines = [
            "This is just normal paragraph text",
            "without any case markers",
            "and should not be a boundary",
        ]
        
        is_boundary, markers = self.splitter.detect_case_boundary(lines, 0)
        assert is_boundary is False
    
    def test_empty_line_not_boundary(self):
        """Test that empty lines are not boundaries."""
        lines = [
            "Previous case",
            "",
            "Next case",
        ]
        
        is_boundary, markers = self.splitter.detect_case_boundary(lines, 1)
        assert is_boundary is False


class TestCaseSplitting:
    """Test case splitting functionality."""
    
    def setup_method(self):
        """Setup splitter instance."""
        self.splitter = SCRCaseSplitter()
    
    def test_single_case_extraction(self, sample_case_text):
        """Test extraction of a single case from text."""
        cases = self.splitter.split_volume_text(sample_case_text, "test_volume")
        
        assert len(cases) > 0
        assert cases[0].text is not None
        assert len(cases[0].text) > 0
    
    def test_multiple_cases_splitting(self, sample_multi_case_text):
        """Test splitting of text containing multiple cases."""
        cases = self.splitter.split_volume_text(sample_multi_case_text, "test_volume")
        
        assert len(cases) >= 2  # Should find at least 2-3 cases
        
        # Verify each case has text
        for case in cases:
            assert len(case.text.strip()) > 0
            assert case.markers_found is not None
    
    def test_case_confidence_levels(self, sample_case_text):
        """Test that cases have confidence levels assigned."""
        cases = self.splitter.split_volume_text(sample_case_text, "test_volume")
        
        for case in cases:
            assert case.confidence in ["high", "medium", "low"]
    
    def test_minimum_case_length_enforcement(self):
        """Test that very short text fragments are rejected."""
        short_text = """
ABC v. XYZ
[Coram: Judge]

x
"""
        from config.constants import MIN_CASE_TEXT_LENGTH
        
        cases = self.splitter.split_volume_text(short_text, "test")
        
        # Cases shorter than MIN_CASE_TEXT_LENGTH should be filtered
        for case in cases:
            assert len(case.text.strip()) >= MIN_CASE_TEXT_LENGTH
    
    def test_ambiguous_splits_tracking(self):
        """Test that ambiguous splits are tracked."""
        stats_before = self.splitter.split_stats["ambiguous_splits"]
        
        # Process text with ambiguous boundaries
        text = """
ABC v. XYZ
Some text...

More text that might be next case?
Still the first case?
"""
        self.splitter.split_volume_text(text, "test")
        
        # Stats should be tracked (may or may not increase depending on content)
        stats = self.splitter.get_split_stats()
        assert "ambiguous_splits" in stats


class TestSplitterStatistics:
    """Test statistics tracking."""
    
    def setup_method(self):
        """Setup splitter instance."""
        self.splitter = SCRCaseSplitter()
    
    def test_stats_initialization(self):
        """Test that stats are properly initialized."""
        stats = self.splitter.get_split_stats()
        
        assert "total_volumes" in stats
        assert "total_cases" in stats
        assert "failed_volumes" in stats
        assert stats["total_volumes"] == 0
    
    def test_stats_update_on_split(self, sample_case_text):
        """Test that stats are updated after splitting."""
        self.splitter.split_volume_text(sample_case_text, "volume1")
        
        stats = self.splitter.get_split_stats()
        assert stats["total_cases"] >= 1


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Setup splitter instance."""
        self.splitter = SCRCaseSplitter()
    
    def test_empty_text(self):
        """Test handling of empty text."""
        cases = self.splitter.split_volume_text("", "empty_volume")
        
        # Should return empty list, not crash
        assert cases == []
    
    def test_text_with_no_case_markers(self):
        """Test text without clear case markers."""
        text = """
This is just regular legal text without any
clear case headers or judges listed anywhere.
It's basically unstructured content.
"""
        cases = self.splitter.split_volume_text(text, "unstructured")
        
        # Should not crash, might return empty or 1 case
        assert isinstance(cases, list)
    
    def test_text_with_mixed_case_patterns(self):
        """Test text with varying case header patterns."""
        text = """
CASE ONE v. OTHER
[Coram: Just Judge]

Some content here.

---

case two vs. other
Some more content.

CASE: THREE v. ANOTHER
Judge: Name
Content continues.
"""
        cases = self.splitter.split_volume_text(text, "mixed")
        
        # Should split multiple ways despite format variations
        assert len(cases) >= 2
    
    def test_very_long_case_text(self):
        """Test handling of very long case texts."""
        long_case = "ABC v. XYZ\n[Coram: Judge]\n" + ("x" * 10000)
        
        cases = self.splitter.split_volume_text(long_case, "long")
        
        assert len(cases) > 0
        assert len(cases[0].text) > 0
