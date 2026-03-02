# Fix Remaining Linting Issues - Action Guide

**Status**: 43 remaining issues from Flake8
**Estimated Time**: 30-45 minutes to fix all
**Difficulty**: Low to Medium

---

## Issue Summary

| Category | Count | Effort | Priority |
|----------|-------|--------|----------|
| Unused imports (F401) | 10+ | 5 min | High |
| Missing f-string placeholders (F541) | 4 | 2 min | High |
| Operator spacing (E221) | 2 | 1 min | Low |
| Unused variables (F841) | 3 | 5 min | Medium |
| Import position (E402) | 1 | 2 min | Medium |
| Blank line whitespace (W293) | ~20 | 1 min | Low |
| Complexity (C901) | 3 | 4-6 hrs | Medium |
| Other (E226, E231) | 2 | 2 min | Low |

---

## ✅ EASY FIXES (7-10 minutes total)

### 1. Fix Missing F-String Placeholders (F541) - 4 instances

**Issue**: F-strings defined without any variable placeholders should be regular strings.

#### File: `src/acquisition/run_acquisition.py`

**Line 120**:
```python
# BEFORE:
f"PDF validation failed: {filename}"  # ← might be wrong
# or
f"PDF validation failed"  # ← definitely wrong

# AFTER:
"PDF validation failed"
```

**Line 147**:
```python
# BEFORE:
f"Checkpoint created for {year}"  # ← might be wrong
# or
f"Checkpoint created"  # ← definitely wrong

# AFTER:
"Checkpoint created"
```

#### File: `src/pipeline/run_scr_pipeline.py`

**Line 194**:
```python
# BEFORE:
f"Phase 2 extraction complete"

# AFTER:
"Phase 2 extraction complete"
```

**Line 568**:
```python
# BEFORE:
f"Pipeline execution complete"

# AFTER:
"Pipeline execution complete"
```

**How to fix**: Read the lines and check if any variables are used in the f-string. If not, remove the `f` prefix.

---

### 2. Remove Unused Imports (F401) - 10+ instances

#### File: `src/acquisition/run_acquisition.py`

**Lines 14-15**: Remove these imports
```python
# DELETE:
from pathlib import Path
from typing import Dict
```

✓ **Check**: Search for usage of `Path` and `Dict` - if not used, delete.

#### File: `src/acquisition/scr_pdf_fetcher.py`

**Line 17**: Remove datetime import
```python
# DELETE:
from datetime import datetime
```

✓ **Check**: Search for `datetime.` usage - if not used, delete.

**Line 28**: Remove compute_file_checksum import
```python
# DELETE:
from src.utils import compute_file_checksum
```

**Line 379**: Remove json import
```python
# DELETE:
import json
```

#### File: `src/acquisition/scr_pdf_discovery.py`

**Line 19**: Remove ensure_directory import
```python
# DELETE:
from src.utils import ensure_directory
```

#### File: `src/cleaning/normalizer.py`

**Line 22**: Remove these imports (all three on same line)
```python
# DELETE:
from src.utils import (
    pipeline_logger,
    deduplicate_list,
    normalize_list_items
)
```

#### File: `src/extraction/scr_case_splitter.py`

**Lines 17, 20-21**: Remove these imports
```python
# DELETE:
from typing import Optional

# DELETE:
from config.constants import CASE_SPLIT_MARKERS
from config.settings import RAW_PDFs_DIR
```

#### File: `src/extraction/scr_metadata_extractor.py`

**Lines 16, 19**: Remove these imports
```python
# DELETE:
from typing import Optional

# DELETE:
from config.constants import SECTION_PATTERNS
```

#### File: `src/pipeline/run_scr_pipeline.py`

**Lines 15, 28, 30**: Remove these imports
```python
# DELETE:
import json

# DELETE:
from config.constants import SCR_CASE_SCHEMA

# DELETE:
from src.utils import load_json
```

---

### 3. Fix Operator Spacing (E221, E226) - 3 instances

#### File: `src/acquisition/run_acquisition.py`

**Line 374**:
```python
# BEFORE:
some_variable  = some_value  # Multiple spaces before =

# AFTER:
some_variable = some_value
```

#### File: `src/acquisition/scr_pdf_fetcher.py`

**Line 385**:
```python
# BEFORE:
some_variable  = some_value  # Multiple spaces before =

# AFTER:
some_variable = some_value
```

#### File: `src/utils.py`

**Lines 327, 329**:
```python
# BEFORE:
result = value*2  # Missing spaces around operator

# AFTER:
result = value * 2
```

---

### 4. Remove Unused Variables (F841) - 3 instances

#### File: `src/acquisition/scr_pdf_validator.py`

**Line 56**:
```python
# BEFORE:
with open(filepath) as f:  # ← f is assigned but never used
    pass

# AFTER (Option 1):
with open(filepath):  # ← Remove the variable
    pass

# AFTER (Option 2):
with open(filepath) as _:  # ← Use underscore convention
    pass
```

**Line 151**:
```python
# BEFORE:
text = pdf.extract_text()  # ← text is assigned but never used
# (no usage below)

# AFTER (Option 1):
pdf.extract_text()  # ← Remove assignment

# AFTER (Option 2):
_ = pdf.extract_text()  # ← Use underscore convention
```

#### File: `src/extraction/scr_case_splitter.py`

**Line 291**:
```python
# BEFORE:
results = self.split_text(volume_text)  # ← results never used

# AFTER (Option 1):
self.split_text(volume_text)  # ← Remove assignment

# AFTER (Option 2):
_ = self.split_text(volume_text)  # ← Use underscore convention
```

---

### 5. Fix Module Import Position (E402) - 1 instance

#### File: `src/utils.py`

**Line 503**: Check what's at line 503
```python
# ISSUE: Module-level import appears after code

# SOLUTION: Move all imports to the top of the file, below the docstring
# but before any function definitions or code
```

**Steps**:
1. Find the import statement at line 503
2. Copy it to the top of the file (after existing imports)
3. Delete from line 503

---

## ⚠️ MEDIUM EFFORT (15-20 minutes)

### 6. Fix Blank Line Whitespace (W293) - ~20 instances

These are blank lines that contain trailing whitespace (spaces or tabs).

**Quick fix**: Run this in each file:

```bash
# Using sed (if available):
sed -i 's/^[[:space:]]*$//' <filename>

# Or manually:
# 1. Find blank lines with whitespace
# 2. Delete the whitespace from those lines
```

**Files affected**:
- `src/acquisition/source_config.py` (lines 119, 124, 127, 131, 133)
- `src/extraction/scr_metadata_extractor.py` (lines 350, 352, 354, 357, 359)
- Other files (~20 instances total)

---

## 🔴 HARD FIXES (4-6 hours)

### 7. Reduce Function Complexity (C901) - 3 Functions

These functions have too many branches and need refactoring.

#### Function 1: `SCRPDFFetcher.download_pdf()` - Complexity 47

**File**: `src/acquisition/scr_pdf_fetcher.py` | **Line**: 93

**Issue**: Function does too many things:
- URL validation
- HTTP request handling
- Error handling & retries
- File writing
- Checksum calculation
- Logging

**Refactoring Strategy**:

1. **Extract error handling**:
```python
def _handle_download_error(self, error, url, filepath):
    """Handle download errors and cleanup."""
    # Move error handling logic here
    pass

def _retry_download(self, url, max_retries=3):
    """Retry download with exponential backoff."""
    # Move retry logic here
    pass
```

2. **Extract validation**:
```python
def _validate_response(self, response):
    """Validate HTTP response."""
    # Move response validation here
    pass
```

3. **Extract file operations**:
```python
def _save_pdf_file(self, filepath, content):
    """Save PDF file to disk."""
    # Move file writing here
    pass
```

4. **Refactor main function**:
```python
def download_pdf(self, url, filepath):
    """Download PDF from URL."""
    try:
        response = self._retry_download(url)
        self._validate_response(response)
        self._save_pdf_file(filepath, response.content)
        return True
    except Exception as e:
        self._handle_download_error(e, url, filepath)
        return False
```

**Expected Complexity After**: ~10-15 (reduced from 47)

#### Function 2: `SCRCaseSplitter.split_volume_text()` - Complexity 14

**File**: `src/extraction/scr_case_splitter.py` | **Line**: 117

**Refactoring Strategy**:

1. **Extract marker detection**:
```python
def _find_case_markers(self, text):
    """Find all case boundary markers in text."""
    pass
```

2. **Extract text splitting**:
```python
def _split_by_markers(self, text, markers):
    """Split text by identified markers."""
    pass
```

3. **Refactor main function**:
```python
def split_volume_text(self, volume_text):
    markers = self._find_case_markers(volume_text)
    cases = self._split_by_markers(volume_text, markers)
    return cases
```

**Expected Complexity After**: ~8-10 (reduced from 14)

#### Function 3: `SCRPipeline.phase_6_json_output()` - Complexity 13

**File**: `src/pipeline/run_scr_pipeline.py` | **Line**: 412

**Refactoring Strategy**:

1. **Extract JSON generation**:
```python
def _generate_json_output(self, data):
    """Generate JSON output from pipeline data."""
    pass
```

2. **Extract statistics**:
```python
def _calculate_statistics(self):
    """Calculate pipeline execution statistics."""
    pass
```

3. **Refactor main function**:
```python
def phase_6_json_output(self):
    stats = self._calculate_statistics()
    output = self._generate_json_output(stats)
    self._save_json_output(output)
```

**Expected Complexity After**: ~8-10 (reduced from 13)

---

## Automated Fix Commands

### Remove All Unused Imports

If you have the necessary tools installed:

```bash
# Using isort (auto-removes unused imports):
isort src/ --remove-redundant-aliases

# Using pylint (just for reporting):
pylint --disable=all --enable=unused-import src/
```

### Fix Whitespace Issues

```bash
# Windows PowerShell - remove trailing whitespace:
Get-ChildItem -Path src -File -Include *.py -Recurse | ForEach-Object {
    (Get-Content $_.FullName) -replace '\s+$', '' | Set-Content $_.FullName
}
```

---

## Verification Steps

After making fixes:

### 1. Verify each fix
```bash
# Check each file for issues:
flake8 src/acquisition/run_acquisition.py
flake8 src/utils.py
# etc.
```

### 2. Run all linting tools
```bash
flake8 src/ --max-line-length=100 --max-complexity=10
black --check src/
mypy src/
```

### 3. Run tests to ensure nothing broke
```bash
pytest tests/ -v
```

### 4. Check final count
```bash
flake8 src/ | wc -l  # Should be much lower
```

---

## Priority Order for Fixing

1. **First** (5 min): Fix f-string placeholders (F541)
2. **Second** (5 min): Remove unused imports (F401)
3. **Third** (5 min): Fix operator spacing (E221/E226)
4. **Fourth** (5 min): Remove unused variables (F841)
5. **Fifth** (2 min): Fix import position (E402)
6. **Sixth** (5 min): Fix blank line whitespace (W293)
7. **Finally** (4-6 hrs): Refactor complex functions (C901)

**Total Time**: 30-45 minutes for easy fixes + 4-6 hours for complex refactoring

---

## Tips & Tricks

### Use IDE Features
- **VS Code**: Use "Go to Definition" to find where variables are used
- **VS Code**: Use "Find All References" to find unused imports/variables
- **VS Code**: Use Find & Replace to fix multiple instances at once

### Test After Each Fix
```bash
# After each major change, run tests:
pytest tests/ -v --tb=short
```

### Use Git to Track Changes
```bash
# Commit fixes in logical groups:
git add src/acquisition/run_acquisition.py
git commit -m "Remove unused imports and fix f-strings"

git add src/utils.py  
git commit -m "Fix operator spacing and import position"
```

---

## Resources

- **Flake8 Error Codes**: https://flake8.pycqa.org/en/latest/
- **Black Documentation**: https://black.readthedocs.io/
- **Python PEP 8**: https://pep8.org/
- **Cyclomatic Complexity**: https://en.wikipedia.org/wiki/Cyclomatic_complexity

---

**Next**: Start with fixing easy issues! All 43 issues can be resolved in < 1 week.
