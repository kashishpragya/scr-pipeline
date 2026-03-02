# SCR Pipeline: Supreme Court Reports Extraction

## Overview

A production-grade, PDF-first automation pipeline for extracting authoritative Supreme Court Reports (SCR) data directly from official SCR PDFs. This system prioritizes accuracy, transparency, and intentional conservatism—never inferring or hallucinating legal metadata.

**This project is independent and self-contained.** It does not depend on Indian Kanoon, SCI pipelines, or any previous extraction systems.

## Core Principles

### 🔒 Non-Negotiable

1. **PDF-First, Authoritative**
   - SCR PDFs are the only source of truth
   - HTML is used only for navigation and automation, never as source data
   - Do not infer anything not explicitly present in PDF text

2. **Prefer Missing Over Wrong**
   - If a field is not explicitly present, leave it empty
   - Do NOT guess case numbers, petition types, parties, or subjects
   - Empty values are valid and correct

3. **Conservative Extraction**
   - Judges: ONLY from explicit CORAM-style bracketed names
   - Acts: ONLY if explicitly named ("Act, YYYY")
   - Sections: ONLY if explicitly cited ("Section X")
   - Never synthesize metadata or rely on legal intuition

4. **Zero Hallucination**
   - Extract only what is textually present in the PDF
   - No inference, no educated guesses, no "reasonable assumptions"
   - Log ambiguous cases; skip them rather than guess

5. **Automation-Ready Design**
   - Supports manual seeding now
   - Designed for assisted automation later
   - Idempotent re-runs without duplication
   - Clear logging for automation hooks

## Output Schema (STRICT)

Every extracted case MUST conform exactly to this schema:

```json
{
  "court": "Supreme Court of India",
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

**Important:**
- No extra keys allowed
- Empty values (`""` for strings, `[]` for arrays) are correct if data is absent
- Each case is a separate JSON object in the output file (JSONL format or array)

## Pipeline Architecture

### Phase 0: Environment & Setup
- Initialize folders and logging
- Load configuration
- Validate input PDFs

### Phase 1: Assisted SCR PDF Discovery
- Support manual PDF placement into `data/raw_pdfs/<year>/`
- Design automation hooks for future browser/click workflows
- Log discovery metadata only
- Do not assume bulk access

### Phase 2: PDF Text Extraction
- Use `pdfplumber` for robust text extraction
- Detect and handle scanned pages (OCR fallback if available)
- Extract text page-wise and save to `data/extracted_text/<year>/<volume>.txt`
- Log unreadable PDFs and page-level failures

### Phase 3: SCR Case Splitting (CRITICAL)
- **Problem:** SCR PDFs contain multiple cases per volume
- **Solution:** Split volume text into individual case blocks
- **Conservative Anchors:**
  - Case title in CAPS (e.g., "ABC v. XYZ")
  - Presence of "v." or "vs."
  - Judge brackets (e.g., "[Bench: Hon'ble Justice Name]" or "(Coram: ...)")
- **Critical Rules:**
  - Do NOT merge cases across page boundaries without explicit evidence
  - Log ambiguous splits
  - When in doubt, split into separate cases

### Phase 4: Metadata Extraction (STRICT)
Extract ONLY if explicit:
- `case_name`: Title as written in case header
- `judges`: From CORAM/Bench bracketed information only
- `acts_referred`: Only if explicitly cited by name and year
- `sections_referred`: Only if explicitly numbered (e.g., "Section 5", "Art. 226")

**DO NOT extract:**
- `case_number`: Leave empty if not explicitly written
- `petition_type`: Leave empty; inference is forbidden
- `parties`: Leave arrays empty if not atomic/clear
- `subject_categories`: Leave empty; do not infer

### Phase 5: Cleaning & Normalization
- Normalize judge names (handle "Hon'ble", titles, nicknames)
- Canonicalize Act names (e.g., "Indian Penal Code" → "IPC")
- Normalize Section format ("Section 5" vs "Sec. 5" → standardized)
- Deduplicate conservatively (only exact matches)
- Remove editorial noise (page headers, footnote markers)

### Phase 6: Final JSON Output
- Produce one JSON file per year: `data/output/scr_<year>.json`
- Ensure schema compliance
- Log total cases extracted
- Idempotent re-runs (skip already-processed PDFs)

## Folder Structure

```
scr_pipeline/
├── config/
│   ├── settings.py           # Configuration and paths
│   └── constants.py          # Schema and constants
│
├── data/
│   ├── raw_pdfs/
│   │   └── <year>/           # Place PDFs here manually
│   │       └── <scr_volume>.pdf
│   │
│   ├── extracted_text/
│   │   └── <year>/           # Intermediate text files
│   │       └── <scr_volume>.txt
│   │
│   └── output/
│       └── scr_<year>.json   # Final output
│
├── logs/
│   ├── pipeline.log          # Main pipeline logs
│   └── failures.log          # Extraction failures
│
├── src/
│   ├── automation/
│   │   └── scr_pdf_discovery.py    # PDF discovery and automation hooks
│   │
│   ├── extraction/
│   │   ├── pdf_text_extractor.py   # PDF text extraction
│   │   ├── scr_case_splitter.py    # Case splitting logic
│   │   └── scr_metadata_extractor.py # Metadata extraction
│   │
│   ├── cleaning/
│   │   └── normalizer.py    # Normalization and cleaning
│   │
│   ├── pipeline/
│   │   └── run_scr_pipeline.py  # Main orchestration
│   │
│   └── utils.py             # Logging, helpers
│
├── requirements.txt
└── README.md
```

## Setup & Installation

### Prerequisites
- Python 3.9+
- pip or conda

### Installation

```bash
cd scr_pipeline
pip install -r requirements.txt
```

### Configuration
Edit [config/settings.py](config/settings.py) to customize:
- PDF input directories
- Output paths
- Logging levels
- OCR enablement (if using tesseract)
- Download settings (timeout, retries, file size bounds)

## Acquisition & Usage

### Step 1: Acquire PDFs (New!)

The pipeline now includes an acquisition module to download PDFs from official sources.

See [ACQUISITION.md](ACQUISITION.md) for complete details.

**Quick start:**

```bash
# Register PDF sources for your year
python -c "
from src.acquisition.scr_pdf_fetcher import PDFSourceProvider
PDFSourceProvider.register_source(2010, [
    'https://your-official-scr-source.gov.in/volume_1.pdf',
    'https://your-official-scr-source.gov.in/volume_2.pdf',
])
"

# Download PDFs
python -m src.acquisition.run_acquisition --year 2010

# Verify downloads
ls -lh data/raw_pdfs/2010/
```

### Step 2: Run Extraction Pipeline

Place SCR PDFs or use the acquisition module (above), then extract:

### Run Full Pipeline
```bash
python -m src.pipeline.run_scr_pipeline --year 2010
```

### Run Individual Phases

**Acquisition (download PDFs):**
```bash
python -m src.acquisition.run_acquisition --year 2010
python -m src.acquisition.run_acquisition --year 2010 --dry-run
python -m src.acquisition.run_acquisition --show-sources
```

## Output Format

The pipeline produces:
- **Intermediate Files:** Text extracts in `data/extracted_text/`
- **Final Output:** JSON in `data/output/scr_<year>.json`

Example output structure:
```json
{
  "court": "Supreme Court of India",
  "case_number": "",
  "petition_type": "",
  "petition_format": "",
  "judges": ["Justice A. K. Goel", "Justice U. U. Lalit"],
  "petitioner": [],
  "respondent": [],
  "case_name": "ABC v. THE STATE OF XYZ",
  "acts_referred": ["Indian Penal Code, 1860"],
  "sections_referred": ["Section 498A"],
  "subject_categories": []
}
```

## What Is NOT Extracted (Intentionally)

To maintain honesty and avoid hallucination:

- **Case Numbers:** Leave empty unless explicitly written in PDF header
- **Petition Types:** Leave empty; inferred from case name is forbidden
- **Party Names:** Leave empty if not atomic/clearly separated
- **Subject Categories:** Leave empty; inferred from content is forbidden
- **Court Bench Composition:** Include only explicit CORAM information

This conservatism is a feature, not a limitation. Downstream systems can enrich this data.

## Logging

All operations are logged to:
- `logs/pipeline.log` — Main execution log
- `logs/failures.log` — Extraction failures and ambiguous cases

**Log Levels:**
- `INFO` — Phase completion, PDF discovery
- `WARNING` — Ambiguous splits, missing expected fields
- `ERROR` — PDF corruption, unreadable sections
- `DEBUG` — Detailed extraction steps

## Error Handling & Safety

- **Never crashes on one bad PDF** — Logs failure and continues
- **Never fabricates data** — Empty fields are better than wrong data
- **Re-runnable without duplication** — Checksum tracking for idempotency
- **Fails gracefully** — Detailed error logs for investigation

## Future Automation Hooks

The pipeline is designed to support future automation:

1. **Browser Automation:** `scr_pdf_discovery.py` can integrate Selenium/Playwright for navigating SCR website
2. **Assisted Click Workflows:** Hooks for manual intervention on ambiguous cases
3. **OCR Fallback:** Conditional tesseract integration for scanned pages
4. **Batch Processing:** Designed for processing thousands of PDFs with clear progress tracking

## Development Notes

- **Code Style:** Clean, modular Python. Comment why, not just what.
- **Independence:** This project does NOT use Indian Kanoon or any external legal databases
- **Legal Grade:** Treat as legal-quality system, not a web scraper
- **Testing:** Each phase should produce intermediate artifacts for validation

## Success Criteria

✅ Extracts clean, honest metadata from SCR PDFs  
✅ Produces schema-correct JSON  
✅ Can later be enriched by a separate merge/deduplication system  
✅ Never hallucinates or infers missing data  
✅ Idempotent re-runs without duplication  

## Contact & Support

For issues or questions about extraction logic, refer to:
- Phase-specific logs in `logs/` directory
- Intermediate files in `data/extracted_text/` for debugging
- This README for schema and design decisions

---

**Version:** 1.0  
**Last Updated:** 2026-02-01  
**Status:** Production-Ready
