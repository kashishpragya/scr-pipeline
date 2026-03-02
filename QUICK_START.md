"""
SCR Pipeline - Quick Start Guide & Development Notes

This file provides practical guidance for using the SCR extraction pipeline.
"""

# ==================== QUICK START ====================

"""
STEP 1: Install Dependencies
-----------------------------
cd scr_pipeline
pip install -r requirements.txt

STEP 2: Place SCR PDFs
---------------------
Create the directory structure and add PDFs:
data/raw_pdfs/2023/SCR_Volume_101.pdf
data/raw_pdfs/2023/SCR_Volume_102.pdf

STEP 3: Run Full Pipeline
-------------------------
python src/pipeline/run_scr_pipeline.py --year 2023

STEP 4: Check Output
-------------------
Output will be saved to: data/output/scr_2023.json
Logs will be in: logs/pipeline.log

Individual phase scripts can also be run independently:

python src/automation/scr_pdf_discovery.py --year 2023
python src/extraction/pdf_text_extractor.py --year 2023
python src/extraction/scr_case_splitter.py --year 2023
python src/extraction/scr_metadata_extractor.py --year 2023
python src/cleaning/normalizer.py --year 2023
"""

# ==================== PROJECT DESIGN PRINCIPLES ====================

"""
STRICT CONSERVATISM IN METADATA EXTRACTION

Fields NEVER Extracted (Left Empty):
- case_number: Only if explicitly written in PDF header
- petition_type: Never inferred from case name
- petitioner/respondent: Only if atomic and explicitly clear
- subject_categories: Never inferred from content

Rationale:
- Downstream systems (deduplication, merging, etc.) can enrich this data
- Better to have missing data than hallucinated data
- Legal systems require accuracy over completeness

Fields ALWAYS Extracted (If Present):
- case_name: From case header
- judges: From explicit CORAM/Bench brackets
- acts_referred: Only if explicitly named
- sections_referred: Only if explicitly cited

This design allows the system to:
1. Remain honest and auditable
2. Support future merge/deduplication layers
3. Never make legal assumptions
4. Be extended without breaking existing data
"""

# ==================== FILE FLOW THROUGH PIPELINE ====================

"""
Raw PDFs
   ↓ (Phase 2)
Extracted Text (.txt files)
   ↓ (Phase 3)
Case Blocks (in-memory)
   ↓ (Phase 4)
Extracted Metadata (case dicts)
   ↓ (Phase 5)
Normalized Metadata (cleaned case dicts)
   ↓ (Phase 6)
Final JSON Output (data/output/scr_YYYY.json)

Each intermediate stage:
- Can be inspected for debugging
- Produces logs for auditing
- Supports future improvements (OCR, automation, etc.)
"""

# ==================== DEVELOPMENT NOTES ====================

"""
CODE ARCHITECTURE:

1. config/
   - settings.py: Runtime configuration (paths, options)
   - constants.py: Fixed values (schema, patterns, canonicalization rules)
   
2. src/
   - utils.py: Shared utilities (logging, validation, file handling)
   - automation/: Discovery and future automation hooks
   - extraction/: PDF extraction, case splitting, metadata extraction
   - cleaning/: Normalization and deduplication
   - pipeline/: Main orchestration
   
3. data/
   - raw_pdfs/: Input (organized by year)
   - extracted_text/: Intermediate text files
   - output/: Final JSON output
   
4. logs/
   - pipeline.log: Main execution log
   - failures.log: Extraction failures and warnings
   - execution_log_YYYY.json: Per-year execution statistics

DESIGN PATTERNS:

1. Phase Independence
   - Each phase can run independently
   - Intermediate files enable debugging
   - Clear logging for each phase

2. Strict Validation
   - Schema validation before output
   - Conservative field extraction
   - Empty fields preferred over wrong data

3. Error Handling
   - Never crash on single bad PDF
   - Log failures clearly
   - Continue processing remaining items

4. Idempotency
   - Re-runs produce same results
   - Checksums track processed files
   - No duplicate output
"""

# ==================== TESTING & VALIDATION ====================

"""
Testing the Pipeline:

1. Unit Testing Individual Phases:
   
   python -c "
   from src.extraction.scr_metadata_extractor import SCRMetadataExtractor
   
   test_text = '''RAJESH KUMAR v. STATE OF MAHARASHTRA
   [Coram: Justice A. K. Goel]
   Under Indian Penal Code, 1860
   Section 498A cited
   '''
   
   extractor = SCRMetadataExtractor()
   metadata = extractor.extract_metadata(test_text)
   print('Case Name:', metadata.case_name)
   print('Judges:', metadata.judges)
   print('Acts:', metadata.acts_referred)
   print('Sections:', metadata.sections_referred)
   "

2. Integration Testing:
   - Place sample PDFs in data/raw_pdfs/2024/
   - Run full pipeline: python src/pipeline/run_scr_pipeline.py --year 2024
   - Verify output in data/output/scr_2024.json
   - Check logs in logs/

3. Validation Checks:
   - All cases have required schema keys
   - No extra keys in output
   - String fields are strings (not None)
   - Array fields are arrays (not None)
   - No hallucinated data
"""

# ==================== EXTENDING THE PIPELINE ====================

"""
Future Extensions:

1. Browser Automation
   - Implement scr_pdf_discovery.py AutomationHooks.hook_browser_automation()
   - Use Selenium/Playwright to download PDFs from official SCR database
   
2. OCR for Scanned Pages
   - Implement OCR fallback in pdf_text_extractor.py
   - Use pytesseract or cloud APIs
   - Configure in settings.py (ENABLE_OCR)
   
3. Assisted Validation
   - Implement AutomationHooks.hook_assisted_validation()
   - Ask user to confirm ambiguous case splits
   - Interactive field correction UI
   
4. Deduplication & Merging
   - Implement separate merge service
   - Find duplicate cases across volumes/years
   - Build case relationship graph
   - Use checksums for efficiency

5. Database Storage
   - Instead of JSON output, write to PostgreSQL
   - Support incremental updates
   - Enable full-text search
   - Query by judge, act, section, etc.

6. Web API
   - Expose extracted data via REST API
   - Support queries by case name, judge, act, etc.
   - Authentication and rate limiting
   - Export to multiple formats (JSON, CSV, etc.)
"""

# ==================== TROUBLESHOOTING ====================

"""
Common Issues:

1. "No PDFs found" Error
   - Check: data/raw_pdfs/YYYY/ directory exists
   - Check: PDFs are placed correctly with .pdf extension
   - Verify PDF file integrity: file (filename.pdf)
   
2. "No text extracted" Error
   - PDF may be scanned (image-based)
   - Enable OCR: Set EXTRACT_FROM_SCANNED = True in settings.py
   - Check logs for details
   
3. "No case name found" Warning
   - Case title not in explicit format
   - Check extraction pattern in scr_metadata_extractor.py
   - Case name will be empty (correct behavior, not a failure)
   
4. Low Confidence Case Splits
   - Cases without explicit markers (Coram, v., etc.)
   - Check failures.log for details
   - Manually verify split results if needed
   
5. Incorrect Judge Names
   - Check normalizer.py JUDGE_TITLE_PREFIXES
   - Add new prefixes if judges have unexpected titles
   
6. Missing Acts/Sections
   - May not be explicitly cited in text
   - Check extraction patterns in metadata_extractor.py
   - Add new patterns if needed

Debugging:
- Set LOGGING_LEVEL = "DEBUG" in settings.py
- Check logs/pipeline.log for detailed execution
- Check logs/failures.log for specific failures
- Inspect intermediate files in data/extracted_text/
"""

# ==================== LEGAL GRADE EXPECTATIONS ====================

"""
This system is designed to:

1. HONOR SOURCE MATERIAL
   - Only extract what is explicitly in the PDF
   - Never infer or hallucinate legal information
   - Preserve original case names and citations
   
2. SUPPORT LEGAL WORKFLOWS
   - Produce audit trail (logs, checksums, metadata)
   - Enable review and correction
   - Support incremental improvements
   - Handle edge cases gracefully
   
3. ENABLE DOWNSTREAM SYSTEMS
   - Provide clean, structured data
   - Support merging and deduplication
   - Enable enrichment with external data
   - Maintain data provenance
   
4. MAINTAIN INTEGRITY
   - No data hallucination
   - Conservative field extraction
   - Clear logging of limitations
   - Fail openly rather than silently
"""

if __name__ == "__main__":
    print(__doc__)
