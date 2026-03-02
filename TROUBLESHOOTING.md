"""
TROUBLESHOOTING - SCR Pipeline Common Issues & Solutions

Complete guide to diagnosing and fixing common problems.
"""

# ==================== GENERAL TROUBLESHOOTING ====================

## Issue: Pipeline Won't Start

### Error: "No PDFs found to extract"

**Cause:** No PDF files in `data/raw_pdfs/YYYY/`

**Solution:**
```bash
# Check if directory exists
ls -la data/raw_pdfs/2010/

# Create if missing
mkdir -p data/raw_pdfs/2010

# Add PDF files
cp your_pdf.pdf data/raw_pdfs/2010/
```

**Verify:**
```bash
# Should show your PDFs
ls data/raw_pdfs/2010/*.pdf
```

---

### Error: "Invalid year: Year 1949 is before minimum allowed year 1950"

**Cause:** Year parameter below 1950

**Solution:**
```bash
# Use year 1950 or later
python -m src.pipeline.run_scr_pipeline --year 2010
```

---

## Issue: PDF Extraction Errors

### Error: "Failed to extract X from PDF"

**Cause:** PDF might be corrupted or encrypted

**Solution:**
1. Verify file with external tool:
   ```bash
   pdfinfo your_file.pdf
   ```

2. Try opening in PDF reader
3. If corrupted, use another copy
4. Check file size is reasonable (> 1MB typically)

---

### Error: "Permission denied" on PDF file

**Cause:** File permissions issue

**Solution:**
```bash
# On Linux/macOS
chmod 644 data/raw_pdfs/2010/*.pdf

# Verify
ls -l data/raw_pdfs/2010/
```

---

### Warning: "PDF extraction produced no text"

**Cause:** PDF is scanned (image-based), not text-based

**Options:**
1. **Enable OCR** (if installed):
   ```python
   # In config/settings.py
   ENABLE_OCR = True
   ```

   Install tesseract:
   - Ubuntu: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki

2. **Skip this PDF** and use different source

---

## Issue: Case Splitting Problems

### Error: "No cases found in extracted text"

**Cause:** Text lacks clear case markers (CAPS titles, "v." pattern, CORAM brackets)

**Solution:**
1. Check extracted text file:
   ```bash
   head -20 data/extracted_text/2010/volume_1.txt
   ```

2. Verify it has case markers:
   - All-caps case titles: `ABC v. XYZ`
   - CORAM section: `[Coram: Justice X]`
   - vs. pattern: `Party vs. Other Party`

3. If missing, PDF might have formatting issues

---

### Warning: "Ambiguous case boundary detected"

**Cause:** Text has unclear case split points

**Solution:** Check logs for details:
```bash
tail logs/failures.log
```

This is non-fatal; pipeline continues with conservative splitting.

---

## Issue: Metadata Extraction

### Problem: "Judges not extracted"

**Cause:** No explicit judge information in text

This is **normal**. System extracts only explicit metadata.

**Verify:**
```bash
grep -i "coram\|bench\|justice" data/extracted_text/2010/volume_1.txt
```

If not found, judges won't be extracted.

---

### Problem: "Acts not recognized"

**Cause:** Act names not in standard format

**Examples of recognized:**
- "Indian Penal Code, 1860"
- "Code of Civil Procedure, 1908"
- "Constitution of India, 1950"
- "IPC", "CPC", "CrPC"

**Not recognized:**
- "penal code" (lowercase)
- "IPC 1860" (missing comma)
- "Indian Penal Code" (missing year)

---

## Issue: Output Problems

### Error: "Failed to save JSON output"

**Cause:** Output directory or permissions issue

**Solution:**
```bash
# Create output directory
mkdir -p data/output

# Check permissions
chmod 755 data/output

# Verify
ls -la data/output/
```

---

### Error: "Output file is empty"

**Cause:** No valid cases extracted

**Check:**
1. Were PDFs found?
   ```bash
   ls data/raw_pdfs/2010/
   ```

2. Was text extracted?
   ```bash
   ls data/extracted_text/2010/
   ```

3. Were cases split?
   ```bash
   wc -l data/extracted_text/2010/*.txt
   ```

4. Check log file:
   ```bash
   tail logs/pipeline.log
   ```

---

## Issue: Logging & Debugging

### Error: "LogFileHandler creation failed"

**Cause:** Logs directory doesn't exist

**Solution:**
```bash
mkdir -p logs
chmod 755 logs
```

---

### How to Debug: Enable Verbose Logging

**Solution:** Set logging level in `config/settings.py`:
```python
LOGGING_LEVEL = "DEBUG"  # More verbose
```

Then check logs:
```bash
tail -f logs/pipeline.log
```

---

### How to Find Specific Errors

**Find all errors:**
```bash
grep ERROR logs/pipeline.log | tail -20
```

**Find PDF-specific errors:**
```bash
grep -i "pdf\|extraction" logs/failures.log | tail -20
```

**Find case-specific errors:**
```bash
grep "phase.*4\|metadata" logs/failures.log
```

---

## Issue: Performance Problems

### Problem: "Pipeline is very slow"

**Cause:** Processing large volumes

**Solutions:**
1. Process one year at a time:
   ```bash
   python -m src.pipeline.run_scr_pipeline --year 2010
   # Wait to complete
   python -m src.pipeline.run_scr_pipeline --year 2011
   ```

2. Check disk space:
   ```bash
   df -h
   ```

3. Monitor system resources:
   ```bash
   top -p $(pgrep -f run_scr_pipeline)
   ```

---

### Problem: "Out of memory error"

**Cause:** Very large PDFs or volumes

**Solutions:**
1. Process PDFs individually using phase scripts
2. Increase system memory
3. Process fewer PDFs at once

---

## Issue: Acquisition Module

### Error: "No PDF sources registered for year 2010"

**Cause:** Sources not yet implemented

**Solution:** Register sources in `src/acquisition/source_config.py`:
```python
PDFSourceProvider.register_source(2010, [
    "https://official.gov.in/scr/2010/vol1.pdf",
    "https://official.gov.in/scr/2010/vol2.pdf",
])
```

---

### Error: "Invalid URL: URL does not end with .pdf"

**Solution:** Ensure URLs point directly to PDF files:
```
✓ https://example.gov.in/scr_vol_1.pdf
✗ https://example.gov.in/downloads?file=scr_vol_1
```

---

### Error: "Download timeout" / "Connection error"

**Solution:**
1. Check network connection:
   ```bash
   ping official.gov.in
   ```

2. Retry with dry-run first:
   ```bash
   python -m src.acquisition.run_acquisition --year 2010 --dry-run
   ```

3. Check if URL is accessible:
   ```bash
   curl -I "https://official.gov.in/scr/2010/vol1.pdf"
   ```

---

## Issue: Schema Validation

### Error: "Case NNN validation failed: Extra keys not allowed"

**Cause:** Case dictionary has extra fields

**Solution:** Check case generation in metadata extractor. Only these keys allowed:
```json
{
  "court": "",
  "case_number": "",
  "petition_type": "",
  "petition_format": "",
  "judges": [],
  "petitioner": [],
  "respondent": [],
  "case_name": "",
  "acts_referred": [],
  "sections_referred": [],
  "subject_categories": []
}
```

---

### Error: "Case NNN validation failed: Missing required key"

**Cause:** Case dictionary missing a required field

**Solution:** Ensure all fields are present (can be empty):
```python
# ✓ Correct - all fields present
case = {
    "court": "Supreme Court of India",
    "case_number": "",  # Empty is OK
    "judges": [],
    # ... all other fields
}

# ✗ Wrong - missing "judges" field
case = {
    "court": "Supreme Court of India",
    "case_name": "ABC v. XYZ",
    # Missing other fields!
}
```

---

## Issue: Checkpoint Recovery

### How to Resume from Failed Phase

**Situation:** Pipeline failed at Phase 4, you fixed the issue, now want to resume

**Solution:** Just rerun the pipeline!
```bash
python -m src.pipeline.run_scr_pipeline --year 2010
```

**What happens:**
- Phase 0-3: Skipped (loaded from checkpoints)
- Phase 4+: Re-executed from failure point

**Checkpoints stored in:**
```
logs/checkpoints/checkpoint_phase_0_2010.json
logs/checkpoints/checkpoint_phase_1_2010.json
...
```

**To clear checkpoints:**
```bash
rm logs/checkpoints/checkpoint_phase_*_2010.json
```

Then rerun to start fresh.

---

## Issue: Data Quality

### Problem: "Case names not extracted correctly"

**Cause:** Case titles not in standard format

**Expected format:**
```
PARTY_1 v. PARTY_2
```

**Non-standard formats (not extracted):**
- `party 1 v. party 2` (lowercase)
- `PARTY 1 versus PARTY 2` (spelled out)
- `PARTY-1 vs PARTY-2` (with punctuation)

**Solution:** This is by design (conservative extraction). Consider post-processing if needed.

---

### Problem: "Judges named weirdly"

**Examples:**
- `Hon'ble Justice JOHN SMITH` → `John Smith` (after normalization)
- `Mr. Justice A.K. Sharma` → `A.K. Sharma` or `A K Sharma`
- `The Judge Smith` → `Judge Smith`

**Verification:**
```bash
grep -i "coram\|judges" data/output/scr_2010.json | head -5 | json_pp
```

---

## Issue: File Management

### Problem: "Disk space full"

**Check disk usage:**
```bash
du -sh data/
du -sh data/extracted_text/
du -sh data/output/
```

**Cleanup extracted text (keep PDFs and output):**
```bash
rm -rf data/extracted_text/2010/*.txt
```

Pipeline will re-extract as needed.

---

### Problem: "Cannot delete/modify files on Windows"

**Cause:** Files in use or permission issue

**Solution:**
1. Close any open file handles
2. Try with admin privileges
3. Restart Windows and try again

---

## Getting Help

### Collect Debug Information

When reporting issues, provide:
1. **Full error message** from logs
2. **Timestamp** of the error
3. **Year** being processed
4. **PDF name** if applicable
5. **System info:**
   ```bash
   python --version
   pip list | grep -E "pytest|pdfplumber|requests"
   ```

### Useful Commands for Debugging

```bash
# Full pipeline logs
cat logs/pipeline.log

# Failure-only logs
cat logs/failures.log

# Execution summary
cat logs/execution_summary_2010.json | python -m json.tool

# Check specific phase
grep "Phase 3\|Phase 4" logs/pipeline.log
```

---

## Quick Reference: Common Commands

```bash
# Run pipeline for year 2010
python -m src.pipeline.run_scr_pipeline --year 2010

# Run acquisition
python -m src.acquisition.run_acquisition --year 2010 --dry-run

# View logs live
tail -f logs/pipeline.log

# Check output
python -c "import json; print(json.load(open('data/output/scr_2010.json'))[:1])"

# Count extracted cases
python -c "import json; cases = json.load(open('data/output/scr_2010.json')); print(f'Total: {len(cases)} cases')"

# Run tests
pytest tests/ -v

# Generate coverage
pytest --cov=src tests/
```
