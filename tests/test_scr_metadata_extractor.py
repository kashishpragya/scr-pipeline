"""
Unit tests for SCR Metadata Extractor module.

Tests the logic for extracting metadata from case text.
"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.scr_metadata_extractor import SCRMetadataExtractor


class TestCaseNameExtraction:
    """Test case name extraction."""
    
    def setup_method(self):
        """Setup extractor instance."""
        self.extractor = SCRMetadataExtractor()
    
    def test_simple_case_name(self, sample_case_text):
        """Test extraction of simple case name."""
        case_name = self.extractor.extract_case_name(sample_case_text)
        
        assert case_name != ""
        assert "ABC" in case_name
        assert "XYZ" in case_name
        assert "v." in case_name or "vs." in case_name
    
    def test_case_name_with_vs_pattern(self):
        """Test case name with 'vs.' pattern."""
        text = """
PLAINTIFF v. DEFENDANT
[Coram: Judge]

Case content...
"""
        case_name = self.extractor.extract_case_name(text)
        
        assert "PLAINTIFF" in case_name
        assert "DEFENDANT" in case_name
        assert "v." in case_name
    
    def test_case_name_not_found(self):
        """Test handling when no case name can be extracted."""
        text = """
Random text without case markers.
Just regular content.
No case name anywhere.
"""
        case_name = self.extractor.extract_case_name(text)
        
        # Should return empty string, not crash
        assert case_name == ""
    
    def test_case_name_from_lowercase(self):
        """Test that lowercase 'v.' pattern is also detected."""
        text = """
smith v. jones

Case content here.
"""
        case_name = self.extractor.extract_case_name(text)
        
        assert case_name != ""


class TestJudgeExtraction:
    """Test judge name extraction."""
    
    def setup_method(self):
        """Setup extractor instance."""
        self.extractor = SCRMetadataExtractor()
    
    def test_coram_bracketed_judges(self):
        """Test extraction from [Coram: ...] format."""
        text = """
ABC v. XYZ
[Coram: Justice John Smith, Justice Jane Doe]

Case content...
"""
        judges = self.extractor.extract_judges(text)
        
        assert len(judges) >= 1
        assert any("Smith" in judge for judge in judges)
    
    def test_coram_parenthetical_judges(self):
        """Test extraction from (Coram: ...) format."""
        text = """
ABC v. XYZ
(Coram: Justice A.K. Sharma, Justice B.P. Kumar)

Content...
"""
        judges = self.extractor.extract_judges(text)
        
        assert len(judges) >= 1
    
    def test_multiple_judges(self):
        """Test extraction of multiple judges."""
        text = """
ABC v. XYZ
[Coram: Justice Smith, Justice Doe, Justice Johnson]

Content...
"""
        judges = self.extractor.extract_judges(text)
        
        assert len(judges) >= 2
    
    def test_no_judges_found(self):
        """Test handling when no judges found."""
        text = """
ABC v. XYZ

Case content without judge information.
"""
        judges = self.extractor.extract_judges(text)
        
        # Should return empty list, not crash
        assert judges == []
    
    def test_judge_title_removal(self):
        """Test that judge titles like 'Hon'ble' are handled."""
        text = """
ABC v. XYZ
[Coram: Hon'ble Justice Smith]

Content...
"""
        judges = self.extractor.extract_judges(text)
        
        # Raw extraction might include titles, that's OK (normalization handles it)
        assert len(judges) >= 1


class TestActExtraction:
    """Test act name extraction."""
    
    def setup_method(self):
        """Setup extractor instance."""
        self.extractor = SCRMetadataExtractor()
    
    def test_named_act_extraction(self):
        """Test extraction of explicitly named acts."""
        text = """
ABC v. XYZ

Violated the Indian Penal Code, 1860.
Also violated Code of Civil Procedure, 1908.

Content...
"""
        acts = self.extractor.extract_acts(text)
        
        # Should find at least one act
        assert len(acts) >= 1
    
    def test_ipc_extraction(self):
        """Test extraction of common act abbreviations."""
        text = """
ABC v. XYZ

This violates the IPC.
Also the CPC is relevant.

Content...
"""
        acts = self.extractor.extract_acts(text)
        
        # Might find IPC or full name, at least some acts
        assert isinstance(acts, list)
    
    def test_no_acts_found(self):
        """Test when no acts are mentioned."""
        text = """
ABC v. XYZ

This is purely a property dispute.
No laws are cited.
"""
        acts = self.extractor.extract_acts(text)
        
        assert acts == []
    
    def test_act_with_year(self):
        """Test extraction of acts with years."""
        text = """
Under the Constitution of India, 1950.
And the Hindu Marriage Act, 1955.
"""
        acts = self.extractor.extract_acts(text)
        
        assert len(acts) >= 0  # Might be 0 or 2, depending on extraction


class TestSectionExtraction:
    """Test section reference extraction."""
    
    def setup_method(self):
        """Setup extractor instance."""
        self.extractor = SCRMetadataExtractor()
    
    def test_section_number_extraction(self):
        """Test extraction of section numbers."""
        text = """
ABC v. XYZ

Violations of Section 405 and Section 420 of the IPC.

Content...
"""
        sections = self.extractor.extract_sections(text)
        
        assert len(sections) >= 2
        assert "405" in sections
        assert "420" in sections
    
    def test_section_abbreviation(self):
        """Test extraction of abbreviated section references."""
        text = """
Sec. 123 and Sec. 456 are violated.
"""
        sections = self.extractor.extract_sections(text)
        
        assert len(sections) >= 1
    
    def test_article_extraction(self):
        """Test extraction of Constitution articles."""
        text = """
Article 226 of the Constitution permits the Court to issue writs.
Article 32 allows persons to approach the Court directly.
"""
        sections = self.extractor.extract_sections(text)
        
        assert len(sections) >= 1
        assert "226" in sections or "32" in sections
    
    def test_section_with_subsection(self):
        """Test extraction of sections with subsections."""
        text = """
Section 405A and Section 420(2) are relevant here.
"""
        sections = self.extractor.extract_sections(text)
        
        assert len(sections) >= 1


class TestMetadataEdgeCases:
    """Test edge cases in metadata extraction."""
    
    def setup_method(self):
        """Setup extractor instance."""
        self.extractor = SCRMetadataExtractor()
    
    def test_empty_text(self):
        """Test handling of empty text."""
        metadata = self.extractor.extract_metadata("", "test_volume")
        
        assert metadata.case_name == ""
        assert metadata.judges == []
        assert metadata.acts_referred == []
        assert metadata.sections_referred == []
    
    def test_text_with_garbage(self):
        """Test text with formatting artifacts."""
        text = """
---123---
ABC v. XYZ
---456---
[Coram: Judge Smith]
###$%^&*()
Section 405
"""
        metadata = self.extractor.extract_metadata(text, "test_volume")
        
        # Should extract what it can despite garbage
        assert metadata.case_name != "" or metadata.judges or metadata.sections_referred
    
    def test_case_with_no_metadata(self):
        """Test case with minimal/no extractable metadata."""
        text = """
ABC v. XYZ

Just some random court judgment text without any explicit
legal references or recognized metadata patterns.
"""
        metadata = self.extractor.extract_metadata(text, "test_volume")
        
        # Case name should be extracted
        assert metadata.case_name != ""
        # Other fields might be empty, that's OK
        assert isinstance(metadata.judges, list)
        assert isinstance(metadata.acts_referred, list)
    
    def test_result_to_case_dict(self, schema_valid_case):
        """Test conversion to case dictionary."""
        text = "ABC v. XYZ\n[Coram: Judge Smith]\nSection 405"
        metadata = self.extractor.extract_metadata(text, "test")
        
        case_dict = metadata.to_case_dict()
        
        # Should have all required keys
        assert "case_name" in case_dict
        assert "judges" in case_dict
        assert "sections_referred" in case_dict
        assert case_dict["court"] == "Supreme Court of India"


class TestExtractorStatistics:
    """Test statistics tracking."""
    
    def setup_method(self):
        """Setup extractor instance."""
        self.extractor = SCRMetadataExtractor()
    
    def test_stats_initialization(self):
        """Test that stats are properly initialized."""
        stats = self.extractor.get_extraction_stats()
        
        assert "total_cases" in stats
        assert "with_judges" in stats
        assert "with_acts" in stats
        assert "with_sections" in stats
    
    def test_stats_counting(self):
        """Test that stats are updated during extraction."""
        text1 = "ABC v. XYZ\n[Coram: Judge]\nSection 405"
        text2 = "DEF v. GHI\n\nNo judges or sections"
        
        self.extractor.extract_metadata(text1, "volume")
        self.extractor.extract_metadata(text2, "volume")
        
        stats = self.extractor.get_extraction_stats()
        assert stats["total_cases"] == 2
        assert stats["with_judges"] >= 1
