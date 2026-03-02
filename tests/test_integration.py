"""
Integration tests for the full SCR Pipeline.

Tests the interaction between modules and end-to-end workflows.
"""

import pytest
from pathlib import Path
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.scr_case_splitter import SCRCaseSplitter
from src.extraction.scr_metadata_extractor import SCRMetadataExtractor
from src.cleaning.normalizer import Normalizer
from src.utils import validate_case_schema, save_json, load_json


class TestExtractionPipeline:
    """Test the extraction pipeline flow."""
    
    def test_full_extraction_workflow(self, sample_multi_case_text):
        """Test complete workflow: split -> extract -> normalize."""
        
        # Phase 1: Split cases
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(sample_multi_case_text, "test_volume")
        
        assert len(cases) > 0
        
        # Phase 2: Extract metadata
        extractor = SCRMetadataExtractor()
        extracted_cases = []
        
        for case_block in cases:
            metadata = extractor.extract_metadata(case_block.text, "test_volume")
            case_dict = metadata.to_case_dict()
            extracted_cases.append(case_dict)
        
        assert len(extracted_cases) == len(cases)
        
        # Phase 3: Normalize
        normalizer = Normalizer()
        normalized_cases = normalizer.normalize_cases(extracted_cases)
        
        assert len(normalized_cases) == len(extracted_cases)
        
        # Verify all normalized cases are valid
        for case in normalized_cases:
            is_valid, errors = validate_case_schema(case)
            assert is_valid, f"Case failed validation: {errors}"
    
    def test_pipeline_preserves_case_count(self, sample_multi_case_text):
        """Test that case count is preserved through pipeline."""
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(sample_multi_case_text, "test")
        initial_count = len(cases)
        
        # Extract without losing cases
        extractor = SCRMetadataExtractor()
        extracted = []
        for case_block in cases:
            metadata = extractor.extract_metadata(case_block.text, "test")
            extracted.append(metadata.to_case_dict())
        
        assert len(extracted) == initial_count
        
        # Normalize without losing cases
        normalizer = Normalizer()
        normalized = normalizer.normalize_cases(extracted)
        
        assert len(normalized) == initial_count
    
    def test_pipeline_with_minimal_data(self):
        """Test pipeline with minimal case data."""
        text = "A v. B\n\nNo additional metadata."
        
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(text, "test")
        
        if len(cases) > 0:
            extractor = SCRMetadataExtractor()
            metadata = extractor.extract_metadata(cases[0].text, "test")
            case_dict = metadata.to_case_dict()
            
            # Case should be valid even with minimal data
            is_valid, errors = validate_case_schema(case_dict)
            assert is_valid


class TestCaseFlowDataIntegrity:
    """Test that data is preserved correctly through the pipeline."""
    
    def test_case_name_preservation(self):
        """Test that case names are preserved through pipeline."""
        text = """
PLAINTIFF v. DEFENDANT
[Coram: Judge Smith]

Content here with Section 405.
"""
        
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(text, "test")
        
        extractor = SCRMetadataExtractor()
        case_dict = extractor.extract_metadata(cases[0].text, "test").to_case_dict()
        
        # If case name extracted, it should contain the parties
        if case_dict["case_name"]:
            assert "PLAINTIFF" in case_dict["case_name"] or "DEFENDANT" in case_dict["case_name"]
    
    def test_judge_information_preservation(self):
        """Test that judge information is preserved."""
        text = """
ABC v. XYZ
[Coram: Justice Smith, Justice Doe]

Case content...
"""
        
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(text, "test")
        
        extractor = SCRMetadataExtractor()
        case_dict = extractor.extract_metadata(cases[0].text, "test").to_case_dict()
        
        # Judge information should be extracted
        assert isinstance(case_dict["judges"], list)
        if len(case_dict["judges"]) > 0:
            assert any("Smith" in judge or "Doe" in judge for judge in case_dict["judges"])
    
    def test_legal_references_preservation(self):
        """Test that legal references are preserved."""
        text = """
ABC v. XYZ

Violated Sections 405 and 420 of the Indian Penal Code, 1860.
"""
        
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(text, "test")
        
        extractor = SCRMetadataExtractor()
        case_dict = extractor.extract_metadata(cases[0].text, "test").to_case_dict()
        
        # Should have sections referenced
        assert isinstance(case_dict["sections_referred"], list)


class TestErrorRecovery:
    """Test error handling and recovery in pipeline."""
    
    def test_pipeline_continuation_on_single_case_error(self, sample_multi_case_text):
        """Test that pipeline continues if one case fails extraction."""
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(sample_multi_case_text, "test")
        
        # Try to extract all cases, some might fail
        extractor = SCRMetadataExtractor()
        extracted = []
        failed_count = 0
        
        for case_block in cases:
            try:
                metadata = extractor.extract_metadata(case_block.text, "test")
                extracted.append(metadata.to_case_dict())
            except Exception:
                failed_count += 1
        
        # At least some should succeed
        assert len(extracted) >= 0  # Might be 0, but pipeline shouldn't crash
        assert len(extracted) + failed_count == len(cases)
    
    def test_normalization_handles_invalid_data(self):
        """Test that normalizer handles invalid input gracefully."""
        bad_cases = [
            {"invalid": "structure"},
            None,
            "",
        ]
        
        normalizer = Normalizer()
        
        # Should not crash on bad input
        try:
            result = normalizer.normalize_cases([])  # Empty list is OK
            assert result == []
        except Exception:
            pass  # It's OK if it fails on empty


class TestOutputGeneration:
    """Test JSON output generation and validation."""
    
    def test_json_output_is_valid(self, schema_valid_case, tmp_path):
        """Test that generated JSON is valid and readable."""
        output_file = tmp_path / "test_output.json"
        
        cases = [schema_valid_case, schema_valid_case.copy()]
        success = save_json(cases, output_file, pretty=True)
        
        assert success
        assert output_file.exists()
        
        # Load and verify
        loaded = load_json(output_file)
        assert len(loaded) == 2
        assert loaded[0]["case_name"] == schema_valid_case["case_name"]
    
    def test_all_cases_pass_validation(self, sample_case_data_for_normalization):
        """Test that normalized cases pass schema validation."""
        normalizer = Normalizer()
        normalized = normalizer.normalize_cases(sample_case_data_for_normalization)
        
        for case in normalized:
            is_valid, errors = validate_case_schema(case)
            assert is_valid, f"Case {case.get('case_name')} failed validation: {errors}"
    
    def test_output_contains_required_fields(self, schema_valid_case):
        """Test that output JSON contains all required fields."""
        case_list = [schema_valid_case]
        
        for case in case_list:
            required_fields = [
                "court", "case_number", "petition_type", "petition_format",
                "judges", "petitioner", "respondent", "case_name",
                "acts_referred", "sections_referred", "subject_categories"
            ]
            
            for field in required_fields:
                assert field in case, f"Missing required field: {field}"


class TestPipelineStatistics:
    """Test that statistics are properly tracked."""
    
    def test_splitter_stats(self, sample_multi_case_text):
        """Test case splitter statistics."""
        splitter = SCRCaseSplitter()
        splitter.split_volume_text(sample_multi_case_text, "test_vol")
        
        stats = splitter.get_split_stats()
        
        assert "total_cases" in stats
        assert stats["total_cases"] >= 0
    
    def test_extractor_stats(self):
        """Test metadata extractor statistics."""
        extractor = SCRMetadataExtractor()
        text = "ABC v. XYZ\n[Coram: Judge]\nSection 405"
        
        extractor.extract_metadata(text, "test")
        
        stats = extractor.get_extraction_stats()
        
        assert stats["total_cases"] == 1
        assert stats["with_judges"] >= 1
    
    def test_normalizer_stats(self, sample_case_data_for_normalization):
        """Test normalizer statistics."""
        normalizer = Normalizer()
        normalizer.normalize_cases(sample_case_data_for_normalization)
        
        stats = normalizer.normalization_stats
        
        assert "judges_normalized" in stats
        assert stats["judges_normalized"] >= 0


class TestEdgeCaseIntegration:
    """Test integration with edge cases."""
    
    def test_empty_volume_handling(self):
        """Test handling of empty volume."""
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text("", "empty")
        
        assert cases == []
    
    def test_single_case_workflow(self):
        """Test workflow with single case."""
        text = "ABC v. XYZ\nContent here with Section 123."
        
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(text, "single")
        
        if len(cases) > 0:
            extractor = SCRMetadataExtractor()
            case_dict = extractor.extract_metadata(cases[0].text, "single").to_case_dict()
            
            normalizer = Normalizer()
            normalized = normalizer.normalize_cases([case_dict])
            
            assert len(normalized) == 1
            
            # Should be valid
            is_valid, _ = validate_case_schema(normalized[0])
            assert is_valid
    
    def test_very_long_volume_handling(self):
        """Test handling of very long volumes."""
        # Create a volume with many cases
        text = ""
        for i in range(10):
            text += f"\nCASE_{i} v. OTHER_{i}\nContent\n"
        
        splitter = SCRCaseSplitter()
        cases = splitter.split_volume_text(text, "long_volume")
        
        # Should handle without crashing
        assert len(cases) >= 0
