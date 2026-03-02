# SCI PDF ACQUISITION PIPELINE - QUICK START GUIDE

## Overview

This guide provides step-by-step instructions to run the semi-automated PDF discovery and acquisition pipeline for Supreme Court of India judgements (2021-2026).

## Before You Start

### Prerequisites
- ✅ Python 3.9+ (verify with `python --version`)
- ✅ Chrome browser installed (Selenium will use it)
- ✅ Network connection (for downloading PDFs)
- ✅ Write access to workspace directory
- ✅ Dependencies installed (`pip install -r requirements.txt`)

### Dependencies Check
Run this to verify all dependencies are installed:
```bash
python -c "import selenium; import requests; from webdriver_manager.chrome import ChromeDriverManager; print('✓ All dependencies OK')"
```

## Running the Pipeline

### Option 1: Simple (Recommended)

```bash
# Navigate to workspace
cd c:\Users\imkas\Desktop\legal-lens-Copy\scr_pipeline

# Run pipeline
python -m src.acquisition.run_sci_2021_2026_pipeline
```

That's it! The pipeline will:
1. Process years 2021-2026 automatically
2. Generate 30-day date batches for each year
3. Launch browser for each batch
4. Prompt for manual CAPTCHA solving when needed
5. Download PDFs and organize by year
6. Print comprehensive summary

### Option 2: With Logging to File

```bash
python -m src.acquisition.run_sci_2021_2026_pipeline > pipeline_output.log 2>&1
```

This saves all output to `pipeline_output.log` for later review.

## Understanding the Workflow

### What Happens Automatically

1. **Year Loop**: Pipeline processes each year (2021, 2022, ..., 2026)
2. **Date Batching**: Each year is split into 30-day windows
   - 2021: (01-01-2021, 30-01-2021), (31-01-2021, 01-03-2021), ...
3. **Browser Automation**: For each 30-day batch:
   - Launches Chrome
   - Opens SCI judgement date page
   - Fills in date range
   - **PAUSES for manual CAPTCHA**
   - Clicks search automatically
   - Extracts PDF links

### What You Need to Do

**Only one thing**: Solve the CAPTCHA when prompted

1. You'll see this message:
   ```
   ══════════════════════════════════════════════════════════════════════════════
   ⚠️  MANUAL CAPTCHA SOLUTION REQUIRED
   ══════════════════════════════════════════════════════════════════════════════
   
   ACTION REQUIRED:
     1. Look at the Chrome browser
     2. Solve the CAPTCHA if present
     3. Return to this terminal
     4. Press ENTER to continue
   ```

2. Look at the Chrome browser window
3. Solve the CAPTCHA (drag slider, click squares, etc.)
4. Return to terminal
5. Press **ENTER** to continue
6. Pipeline automatically searches and downloads PDFs

### What Gets Downloaded

PDFs are saved to: `data/raw_pdfs/<YEAR>/`

Example structure:
```
data/raw_pdfs/
├── 2021/
│   ├── pdf_00001.pdf
│   ├── pdf_00002.pdf
│   └── ... (198+ more files)
├── 2022/
│   ├── pdf_00001.pdf
│   └── ...
└── 2026/
    └── ...
```

## Progress Indicators

As the pipeline runs, you'll see:

- `✓` = Success (file downloaded, page loaded, etc.)
- `✗` = Error (but pipeline continues)
- `[1/13]` = "Batch 1 of 13" - shows progress
- `====` header lines = Major milestone

Example:
```
[Batch 1/13]
══════════════════════════════════════════════════════════════════════════════
SEARCHING DATE RANGE: 01-01-2021 → 30-01-2021
══════════════════════════════════════════════════════════════════════════════
Opening official SCI judgement date page...
✓ Page loaded, date fields found
✓ Set from_date = 01-01-2021
✓ Set to_date = 30-01-2021

⚠️  MANUAL CAPTCHA SOLUTION REQUIRED
[Wait for user to press ENTER after solving CAPTCHA]
✓ User confirmed CAPTCHA solved
✓ Results table loaded
✓ Extracted 15 unique PDF links

DOWNLOADING 15 PDFs FOR YEAR 2021
✓ Directory ready: data/raw_pdfs/2021
[1/15] Downloading...
✓ Downloaded: pdf_00001.pdf (524,288 bytes)
[2/15] Downloading...
```

## Expected Duration

| Year  | Batches | Est. Time |
|-------|---------|-----------|
| Each  | ~13     | 30+ min   |
| **Total** | **~78** | **6-10 hours** |

⚠️ **This is a long-running process!** You'll need to manually solve CAPTCHA ~78 times (once per batch). Consider running overnight or over multiple sessions.

## What to Expect at Completion

Final summary (example):
```
══════════════════════════════════════════════════════════════════════════════
FINAL PIPELINE SUMMARY
══════════════════════════════════════════════════════════════════════════════

EXECUTION METRICS:
  Start time:           2025-01-15 09:30:00
  End time:             2025-01-15 10:45:00
  Duration:             3900s (65.0m)

OUTPUT DIRECTORY:
  Location:             C:\...\data\raw_pdfs
  Total PDF files:      1250
  Total size:           3420.5 MB

RESULTS BY YEAR:
  2021:
    Batches:      13
    Links found:  245
    Downloaded:   198
  2022:
    Batches:      13
    Links found:  267
    Downloaded:   231
  ...

OVERALL TOTALS:
  Total links found:    1480
  Total downloaded:     1250

══════════════════════════════════════════════════════════════════════════════
PIPELINE EXECUTION COMPLETE
══════════════════════════════════════════════════════════════════════════════
```

## Troubleshooting

### Chrome Not Found
**Error**: `Failed to launch Chrome`
**Solution**: Install Chrome browser or check if it's in PATH

### Timeout Errors
**Error**: `Timeout downloading: https://...` or `Timeout loading page`
**Solution**: Normal - pipeline retries next URL. Network might be slow.

### CAPTCHA Not Appearing
**Error**: Script continues without prompting for CAPTCHA
**Solution**: This is OK - means there's no CAPTCHA for this batch. Pipeline continues automatically.

### Stop Pipeline Mid-Run
**To stop**: Press `Ctrl+C` in terminal

The pipeline will:
- Close the browser cleanly
- Print final summary of what was completed
- Exit gracefully

Note: You can resume by running again - it will skip files that already exist.

### Resume After Interruption

If the pipeline was interrupted:
```bash
# Just run it again - it will pick up where it left off
python -m src.acquisition.run_sci_2021_2026_pipeline
```

The pipeline automatically skips:
- Already downloaded PDFs (checks file exists)
- Date ranges already processed would need manual tracking

## Output Files

### Logs
- Structured logging to console
- Optional: redirect to file with `> output.log 2>&1`

### Downloaded PDFs
Located in: `data/raw_pdfs/<YEAR>/`

Each PDF:
- Has valid PDF header (b"%PDF")
- Ranges from ~50 KB to ~2 MB
- Named as `pdf_NNNNN.pdf` or extracted from URL

## Under the Hood

### Technologies Used
- **Selenium**: Browser automation (Chrome)
- **requests**: PDF downloads with streaming
- **datetime**: 30-day batch generation
- **pathlib**: Directory/file operations
- **Python logging**: Structured logging

### What The Pipeline Does NOT Do
- ❌ Does NOT extract text from PDFs
- ❌ Does NOT normalize/clean data
- ❌ Does NOT modify extraction layer
- ❌ Does NOT run pipeline orchestration
- ❌ Does NOT make changes to tests

It ONLY discovers and downloads PDFs to `data/raw_pdfs/<YEAR>/`

## Safety Features

The pipeline includes:
- ✅ PDF header validation (rejects corrupted files)
- ✅ Deduplication (removes duplicate URLs)
- ✅ Skip existing files (doesn't re-download)
- ✅ Comprehensive error logging
- ✅ Continues on errors (robust, doesn't crash)
- ✅ Graceful browser cleanup
- ✅ Network timeout handling (30s default)

## Integration Next Steps

Once PDFs are downloaded to `data/raw_pdfs/`:

1. **Text Extraction**: Run text extractor on PDFs
2. **Metadata Extraction**: Extract case metadata
3. **Data Cleaning**: Normalize text
4. **Pipeline Integration**: Integrate into main SCR pipeline

Currently, the acquisition pipeline is **INDEPENDENT** - it just discovers and downloads. Future steps can process these PDFs.

## Support

If issues occur:
1. Check logs (terminal output)
2. Verify Chrome is installed
3. Check network connection
4. Verify write permissions to `data/` directory
5. Try re-running (many errors are transient)

## Summary

```
Command:  python -m src.acquisition.run_sci_2021_2026_pipeline
Duration: 6-10 hours (manual CAPTCHA solving)
Output:   data/raw_pdfs/2021/ ... data/raw_pdfs/2026/
Status:   Estimated 1000-1500 PDFs for 6 years
```

Good luck! 🚀
