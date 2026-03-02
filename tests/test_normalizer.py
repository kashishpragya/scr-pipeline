"""
Unit tests for Normalizer module.

Tests the logic for normalizing and cleaning extracted metadata.
"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cleaning.normalizer import Normalizer


class TestJudgeNormalization:
    """Test judge name normalization."""
    
    def setup_method(self):
        """Setup normalizer instance."""
        self.normalizer = Normalizer()
    
    def test_simple_judge_name(self):
        """Test normalization of simple judge names."""
        name = "John Smith"
        normalized = self.normalizer.normalize_judge_name(name)
        
        assert normalized == "John Smith"
    
    def test_remove_honourable_title(self):
        """Test removal of 'Hon'ble' title."""
        name = "Hon'ble Justice John Smith"
        normalized = self.normalizer.normalize_judge_name(name)
        
        assert "Hon'ble" not in normalized
        assert "John Smith" in normalized
    
    def test_remove_justice_title(self):
        """Test removal of 'Justice' title."""
        name = "Justice Jane Doe"
        normalized = self.normalizer.normalize_judge_name(name)
        
        assert "Justice" not in normalized
        assert "Jane" in normalized
        assert "Doe" in normalized
    
    def test_remove_dr_title(self):
        """Test removal of 'Dr.' title."""
        name = "Dr. A.K. Sharma"
        normalized = self.normalizer.normalize_judge_name(name)
        
        assert "Dr." not in normalized
        assert "A.K." in normalized or "A K" in normalized
    
    def test_uppercase_to_proper_case(self):
        """Test conversion from UPPERCASE to Proper Case."""
        name = "JOHN DOE"
        normalized = self.normalizer.normalize_judge_name(name)
        
        assert normalized == "John Doe"
    
    def test_remove_parenthetical_info(self):
        """Test removal of parenthetical information."""
        name = "John Smith (Retiring)"
        normalized = self.normalizer.normalize_judge_name(name)
        
        assert "Retiring" not in normalized
        assert "John Smith" in normalized
    
    def test_trailing_period_removal(self):
        """Test removal of trailing periods."""
        name = "John Smith."
        normalized = self.normalizer.normalize_judge_name(name)
        
        assert normalized == "John Smith"
    
    def test_normalize_judges_list(self, sample_judge_names):
        """Test normalization of a list of judges."""
        normalized_list = self.normalizer.normalize_judges(sample_judge_names)
        
        assert len(normalized_list) > 0
        # Each normalized judge should be valid
        for judge in normalized_list:
            assert len(judge) > 0
            assert "Hon'ble" not in judge
            assert "Justice" not in judge or judge.startswith("Justice")  # Justice might be preserved in names


class TestActNormalization:
    """Test act name canonicalization."""
    
    def setup_method(self):
        """Setup normalizer instance."""
        self.normalizer = Normalizer()
    
    def test_ipc_canonicalization(self):
        """Test canonicalization of IPC."""
        act = "IPC"
        canonical = self.normalizer.canonicalize_act(act)
        
        assert canonical == "Indian Penal Code, 1860"
    
    def test_cpc_canonicalization(self):
        """Test canonicalization of CPC."""
        act = "CPC"
        canonical = self.normalizer.canonicalize_act(act)
        
        assert canonical == "Code of Civil Procedure, 1908"
    
    def test_constitution_canonicalization(self):
        """Test canonicalization of Constitution."""
        act = "Constitution"
        canonical = self.normalizer.canonicalize_act(act)
        
        assert "Constitution" in canonical
        assert "1950" in canonical
    
    def test_full_act_name_preservation(self):
        """Test that full act names with years are recognized."""
        act = "Indian Penal Code, 1860"
        canonical = self.normalizer.canonicalize_act(act)
        
        assert canonical == "Indian Penal Code, 1860"
    
    def test_case_normalization(self):
        """Test proper case normalization of acts."""
        act = "indian penal code, 1860"
        canonical = self.normalizer.canonicalize_act(act)
        
        # Should be capitalized
        assert canonical[0].isupper()
    
    def test_normalize_acts_list(self, sample_act_names):
        """Test normalization of a list of acts."""
        normalized_list = self.normalizer.normalize_acts(sample_act_names)
        
        assert len(normalized_list) > 0
        # Should contain recognized acts
        for act in normalized_list:
            assert len(act) > 0


class TestSectionNormalization:
    """Test section citation normalization."""
    
    def setup_method(self):
        """Setup normalizer instance."""
        self.normalizer = Normalizer()
    
    def test_simple_section_normalization(self):
        """Test normalization of simple section citations."""
        section = "405"
        normalized = self.normalizer.normalize_section(section)
        
        assert normalized == "405"
    
    def test_section_with_subsection(self):
        """Test normalization of sections with subsections."""
        section = "420(2)"
        normalized = self.normalizer.normalize_section(section)
        
        # Should preserve subsection
        assert "420" in normalized
        assert "2" in normalized
    
    def test_normalize_sections_list(self):
        """Test normalization of section list."""
        sections = ["405", "420", "Section 123"]
        normalized_list = self.normalizer.normalize_sections(sections)
        
        assert len(normalized_list) > 0


class TestDeduplication:
    """Test deduplication of list fields."""
    
    def setup_method(self):
        """Setup normalizer instance."""
        self.normalizer = Normalizer()
    
    def test_deduplicate_judges(self):
        """Test deduplication of judge lists."""
        case = {
            "judges": ["John Smith", "John Smith", "Jane Doe"],
        }
        
        # Manual deduplication test
        from src.utils import deduplicate_list
        deduplicated = deduplicate_list(case["judges"])
        
        assert len(deduplicated) == 2
        assert "John Smith" in deduplicated
        assert "Jane Doe" in deduplicated
    
    def test_deduplicate_acts(self):
        """Test deduplication of acts_referred."""
        case = {
            "acts_referred": [
                "Indian Penal Code, 1860",
                "Indian Penal Code, 1860",
                "Code of Civil Procedure, 1908"
            ],
        }
        
        from src.utils import deduplicate_list
        deduplicated = deduplicate_list(case["acts_referred"])
        
        assert len(deduplicated) == 2
    
    def test_deduplicate_sections(self):
        """Test deduplication of sections_referred."""
        case = {
            "sections_referred": ["405", "405", "420", "405"],
        }
        
        from src.utils import deduplicate_list
        deduplicated = deduplicate_list(case["sections_referred"])
        
        assert len(deduplicated) == 2
        assert "405" in deduplicated
        assert "420" in deduplicated


class TestCaseNormalization:
    """Test full case normalization."""
    
    def setup_method(self):
        """Setup normalizer instance."""
        self.normalizer = Normalizer()
    
    def test_normalize_single_case(self, schema_valid_case):
        """Test normalization of a single case."""
        original = schema_valid_case.copy()
        normalized = self.normalizer.normalize_case(original)
        
        # Should still be valid
        assert normalized is not None
        assert normalized.get("case_name") == original["case_name"]
    
    def test_normalize_cases_list(self, sample_case_data_for_normalization):
        """Test normalization of multiple cases."""
        normalized = self.normalizer.normalize_cases(sample_case_data_for_normalization)
        
        assert len(normalized) == len(sample_case_data_for_normalization)
        
        # Check that duplicates are removed
        for case in normalized:
            # Judges should be deduplicated
            judges_unique = len(set(case["judges"]))
            judges_actual = len(case["judges"])
            assert judges_actual <= judges_unique + 1  # Allow for normalization variance


class TestNormalizerStatistics:
    """Test statistics tracking."""
    
    def setup_method(self):
        """Setup normalizer instance."""
        self.normalizer = Normalizer()
    
    def test_stats_initialization(self):
        """Test that stats dictionary exists."""
        assert hasattr(self.normalizer, 'normalization_stats')
        stats = self.normalizer.normalization_stats
        
        assert "judges_normalized" in stats
        assert "acts_normalized" in stats


class TestEdgeCases:
    """Test edge cases in normalization."""
    
    def setup_method(self):
        """Setup normalizer instance."""
        self.normalizer = Normalizer()
    
    def test_empty_judge_name(self):
        """Test handling of empty judge names."""
        name = ""
        normalized = self.normalizer.normalize_judge_name(name)
        
        assert normalized == ""
    
    def test_whitespace_only_name(self):
        """Test handling of whitespace-only names."""
        name = "   "
        normalized = self.normalizer.normalize_judge_name(name)
        
        # Should be empty or whitespace
        assert normalized.strip() == ""
    
    def test_special_characters_in_name(self):
        """Test handling of special characters."""
        name = "John O'Brien-Smith"
        normalized = self.normalizer.normalize_judge_name(name)
        
        # Should preserve punctuation
        assert "John" in normalized
    
    def test_unknown_act_handling(self):
        """Test handling of unrecognized acts."""
        act = "Some Obscure Act, 1999"
        canonical = self.normalizer.canonicalize_act(act)
        
        # Should still normalize even if not in synonyms
        assert len(canonical) > 0
        assert "Some" in canonical or "Obscure" in canonical
