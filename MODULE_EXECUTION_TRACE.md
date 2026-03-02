# Module-Level Execution Trace

## What Gets Imported vs. What Gets Executed

### PYTEST Execution Trace

```
$ pytest
│
├─ pytest.main()
│  │
│  ├─ Read configuration: pyproject.toml
│  │
│  ├─ Load conftest.py (PYTEST PHASE 1)
│  │  │
│  │  ├─ import pytest
│  │  ├─ from pathlib import Path
│  │  ├─ import json
│  │  ├─ import tempfile
│  │  ├─ import shutil
│  │  │
│  │  └─ sys.path.insert(0, str(Path(__file__).parent.parent))
│  │     ↑ No external modules, just path setup
│  │
│  ├─ Discover test files (PYTEST PHASE 2)
│  │  │
│  │  ├─ tests/test_integration.py found
│  │  │  ├─ from pathlib import Path
│  │  │  ├─ import sys
│  │  │  ├─ from src.extraction.scr_case_splitter import SCRCaseSplitter
│  │  │  │  └─ scr_case_splitter.py imported
│  │  │  │     ├─ import re
│  │  │  │     ├─ from dataclasses import dataclass
│  │  │  │     ├─ from typing import List, Dict, Optional
│  │  │  │     └─ ✅ NO network imports
│  │  │  │
│  │  │  ├─ from src.extraction.scr_metadata_extractor import SCRMetadataExtractor
│  │  │  │  └─ scr_metadata_extractor.py imported
│  │  │  │     ├─ import re
│  │  │  │     ├─ from dataclasses import dataclass
│  │  │  │     ├─ from typing import Dict, List, Optional
│  │  │  │     └─ ✅ NO network imports
│  │  │  │
│  │  │  ├─ from src.cleaning.normalizer import Normalizer
│  │  │  │  └─ normalizer.py imported
│  │  │  │     ├─ import re
│  │  │  │     ├─ from typing import Dict, List, Any
│  │  │  │     └─ ✅ NO network imports
│  │  │  │
│  │  │  └─ from src.utils import validate_case_schema, save_json, load_json
│  │  │     └─ utils.py imported
│  │  │        ├─ import logging
│  │  │        ├─ import json
│  │  │        ├─ from pathlib import Path
│  │  │        ├─ from typing import Dict, List, Any, Optional
│  │  │        ├─ from datetime import datetime
│  │  │        │
│  │  │        └─ from config.settings import ...  (imports config)
│  │  │           ├─ LOGGING_LEVEL = "DEBUG" (from constants)
│  │  │           └─ ✅ NO network imports
│  │  │
│  │  ├─ tests/test_normalizer.py found
│  │  │  └─ Similar imports (no network)
│  │  │
│  │  ├─ tests/test_scr_case_splitter.py found
│  │  │  └─ Similar imports (no network)
│  │  │
│  │  └─ tests/test_scr_metadata_extractor.py found
│  │     └─ Similar imports (no network)
│  │
│  ├─ Collect fixtures (PYTEST PHASE 3)
│  │  └─ conftest.py fixtures:
│  │     ├─ @pytest.fixture temp_workspace
│  │     │  └─ Creates temporary directories
│  │     ├─ @pytest.fixture sample_case_text
│  │     │  └─ Returns hard-coded string (in memory)
│  │     ├─ @pytest.fixture sample_multi_case_text
│  │     │  └─ Returns hard-coded string (in memory)
│  │     ├─ @pytest.fixture schema_valid_case
│  │     │  └─ Returns hard-coded dict (in memory)
│  │     └─ [6 other fixtures]
│  │        └─ All return hard-coded data (in memory)
│  │
│  ├─ Run tests (PYTEST PHASE 4)
│  │  │
│  │  ├─ Test: test_integration.py::TestExtractionPipeline::test_full_extraction_workflow
│  │  │  │
│  │  │  ├─ Receive fixture: sample_multi_case_text (hard-coded string)
│  │  │  │
│  │  │  ├─ splitter = SCRCaseSplitter()  (instantiate)
│  │  │  │  └─ __init__(): Pure Python, no setup
│  │  │  │
│  │  │  ├─ cases = splitter.split_volume_text(sample_multi_case_text, "test_volume")
│  │  │  │  └─ Execute: Pattern matching on sample_multi_case_text string
│  │  │  │     ├─ No file reads
│  │  │  │     ├─ No network calls
│  │  │  │     └─ Returns list of CaseBlock objects (in memory)
│  │  │  │
│  │  │  ├─ extractor = SCRMetadataExtractor()
│  │  │  │  └─ __init__(): Pure Python, no setup
│  │  │  │
│  │  │  ├─ for case_block in cases:
│  │  │  │    metadata = extractor.extract_metadata(case_block.text, "test_volume")
│  │  │  │    └─ Execute: Regex pattern matching on case_block.text string
│  │  │  │       ├─ No file reads
│  │  │  │       ├─ No network calls
│  │  │  │       └─ Returns Metadata object (in memory)
│  │  │  │
│  │  │  ├─ normalizer = Normalizer()
│  │  │  │  └─ __init__(): Pure Python, no setup
│  │  │  │
│  │  │  ├─ normalized_cases = normalizer.normalize_cases(extracted_cases)
│  │  │  │  └─ Execute: Data cleaning on extracted_cases list
│  │  │  │     ├─ Remove duplicates
│  │  │  │     ├─ Normalize text
│  │  │  │     └─ Returns list of dicts (in memory)
│  │  │  │
│  │  │  ├─ for case in normalized_cases:
│  │  │  │    is_valid, errors = validate_case_schema(case)
│  │  │  │    └─ Execute: Dict validation against schema
│  │  │  │       └─ Returns (bool, list) (in memory)
│  │  │  │
│  │  │  └─ ✅ TEST PASSED (assertion succeeded)
│  │  │
│  │  ├─ Test: test_normalizer.py::TestJudgeNormalization::test_simple_judge_name
│  │  │  │
│  │  │  ├─ Receive fixture: sample_judge_names (hard-coded list)
│  │  │  │
│  │  │  ├─ normalizer = Normalizer()
│  │  │  │
│  │  │  ├─ result = normalizer.normalize_judge_names(sample_judge_names)
│  │  │  │  └─ Execute: String processing on judge names
│  │  │  │     └─ No file or network I/O
│  │  │  │
│  │  │  └─ ✅ TEST PASSED
│  │  │
│  │  ├─ [Run remaining 75 tests similar to above]
│  │  │  └─ All use hard-coded fixtures
│  │  │  └─ All operate on in-memory data
│  │  │  └─ No network calls
│  │  │  └─ No file reads except temp_workspace
│  │  │
│  │  └─ 77 tests: ✅ PASSED
│  │     6 tests: ❌ FAILED (fixture mismatch)
│  │
│  └─ Report results
│     └─ ===== 77 passed, 6 failed in 1.23s =====
│
└─ Exit code: 1 (because 6 failed, but non-critical)

NETWORK CALLS DURING PYTEST: ✅ ZERO
FILE DOWNLOADS DURING PYTEST: ✅ ZERO
SELENIUM EXECUTION: ✅ NO
```

---

## run_acquisition.py Execution Trace

```
$ python -m src.acquisition.run_acquisition --year 2010
│
├─ __main__.py wrapper loads module
│  │
│  ├─ Import: src/acquisition/run_acquisition.py
│  │  │
│  │  ├─ import sys
│  │  ├─ import argparse
│  │  ├─ from pathlib import Path
│  │  ├─ from typing import List, Dict
│  │  ├─ from datetime import datetime
│  │  │
│  │  ├─ from config.settings import RAW_PDFs_DIR
│  │  │
│  │  ├─ from src.utils import ... (various utilities)
│  │  │
│  │  ├─ from src.acquisition.scr_pdf_fetcher import get_fetcher, PDFSourceProvider
│  │  │  ├─ scr_pdf_fetcher.py imported
│  │  │  │  ├─ import requests         ← IMPORTED (not called yet)
│  │  │  │  ├─ from pathlib import Path
│  │  │  │  ├─ from typing import Dict, List, Optional, Tuple
│  │  │  │  ├─ from datetime import datetime
│  │  │  │  ├─ import time
│  │  │  │  │
│  │  │  │  ├─ from config.settings import RAW_PDFs_DIR, PDF_DOWNLOAD_TIMEOUT, ...
│  │  │  │  │
│  │  │  │  ├─ from src.utils import pipeline_logger, failures_logger, ...
│  │  │  │  │
│  │  │  │  ├─ class SCRPDFFetcher: ← CLASS DEFINED (not instantiated)
│  │  │  │  │  └─ Methods defined but not called
│  │  │  │  │
│  │  │  │  ├─ class PDFSourceProvider:  ← CLASS DEFINED
│  │  │  │  │  ├─ KNOWN_SOURCES = {}  ← Empty dict
│  │  │  │  │  ├─ @staticmethod register_source()
│  │  │  │  │  └─ @staticmethod get_sources_for_year()
│  │  │  │  │
│  │  │  │  ├─ def get_fetcher(): ← FUNCTION DEFINED (not called)
│  │  │  │  │  └─ return SCRPDFFetcher()
│  │  │  │  │
│  │  │  │  └─ ✅ NO NETWORK CALLS ON IMPORT
│  │  │  │
│  │  │  └─ Returns: PDFSourceProvider class and get_fetcher function
│  │  │
│  │  ├─ from src.acquisition.scr_pdf_validator import PDFValidator
│  │  │  ├─ scr_pdf_validator.py imported
│  │  │  │  ├─ import pdfplumber    ← IMPORTED (not called)
│  │  │  │  ├─ from pathlib import Path
│  │  │  │  │
│  │  │  │  ├─ class PDFValidator: ← CLASS DEFINED (not instantiated)
│  │  │  │  │  └─ Methods defined but not called
│  │  │  │  │
│  │  │  │  └─ ✅ NO NETWORK CALLS ON IMPORT
│  │  │  │
│  │  │  └─ Returns: PDFValidator class
│  │  │
│  │  └─ ✅ Module imports complete - NO NETWORK CALLS
│  │
│  ├─ class AcquisitionPipeline: ← CLASS DEFINED
│  │  └─ Methods defined but not called
│  │
│  └─ def main(): ← FUNCTION DEFINED (not called yet)
│
├─ Execute: if __name__ == "__main__"
│  │
│  ├─ Call main()
│  │  │
│  │  ├─ parser = argparse.ArgumentParser(...)
│  │  │
│  │  ├─ parser.add_argument("--year", type=int, required=True)
│  │  │
│  │  ├─ args = parser.parse_args()
│  │  │  └─ args.year = 2010
│  │  │  └─ args.dry_run = False
│  │  │  └─ args.force_redownload = False
│  │  │
│  │  ├─ if args.show_sources:
│  │  │  └─ False (--show-sources not provided)
│  │  │
│  │  ├─ pipeline = AcquisitionPipeline(args.year)
│  │  │  │
│  │  │  ├─ __init__(year=2010)
│  │  │  │  │
│  │  │  │  ├─ is_valid, error_msg = validate_year(2010)
│  │  │  │  │  └─ Returns: (True, None)  ← Valid year
│  │  │  │  │
│  │  │  │  ├─ self.year = 2010
│  │  │  │  │
│  │  │  │  ├─ self.execution_log = {...}
│  │  │  │  │
│  │  │  │  └─ ✅ Instance created
│  │  │  │
│  │  │  └─ Returns: AcquisitionPipeline instance
│  │  │
│  │  ├─ success = pipeline.run_acquisition(
│  │  │              dry_run=False,
│  │  │              force_redownload=False
│  │  │            )
│  │  │  │
│  │  │  ├─ self.phase_0_setup()
│  │  │  │  │
│  │  │  │  ├─ log_phase_start(0, "Acquisition Setup")
│  │  │  │  │
│  │  │  │  ├─ year_dir = get_year_directory(RAW_PDFs_DIR, 2010)
│  │  │  │  │  └─ Returns: Path(data/raw_pdfs/2010)
│  │  │  │  │
│  │  │  │  ├─ pipeline_logger.info(f"Target directory: {year_dir}")
│  │  │  │  │  └─ Writes to logs/pipeline.log
│  │  │  │  │
│  │  │  │  └─ ✅ Phase 0 complete
│  │  │  │
│  │  │  ├─ sources = self.phase_1_discover_sources()
│  │  │  │  │
│  │  │  │  ├─ log_phase_start(1, "PDF Source Discovery")
│  │  │  │  │
│  │  │  │  ├─ sources = PDFSourceProvider.get_sources_for_year(2010)
│  │  │  │  │  │
│  │  │  │  │  ├─ Access: PDFSourceProvider.KNOWN_SOURCES[2010]
│  │  │  │  │  │  │
│  │  │  │  │  │  └─ But KNOWN_SOURCES is empty!
│  │  │  │  │  │     └─ Why? Because register_all_known_sources() 
│  │  │  │  │  │        in source_config.py was never called
│  │  │  │  │  │
│  │  │  │  │  └─ Returns: []  (empty list)
│  │  │  │  │
│  │  │  │  ├─ if sources:
│  │  │  │  │  └─ False (empty list evaluates to False)
│  │  │  │  │
│  │  │  │  ├─ else:
│  │  │  │  │  └─ pipeline_logger.warning("No sources registered...")
│  │  │  │  │
│  │  │  │  └─ Returns: [] (empty list)
│  │  │  │
│  │  │  ├─ if not sources:  ← TRUE (sources is [])
│  │  │  │  │
│  │  │  │  ├─ pipeline_logger.error(
│  │  │  │  │    "No PDF sources registered for year 2010. "
│  │  │  │  │    "Cannot proceed with acquisition."
│  │  │  │  │  )
│  │  │  │  │
│  │  │  │  ├─ self.execution_log["status"] = "no_sources"
│  │  │  │  │
│  │  │  │  └─ return False  ← EXIT HERE
│  │  │  │
│  │  │  └─ Never reaches Phase 2 (download)
│  │  │
│  │  ├─ success = False (from return above)
│  │  │
│  │  ├─ return 0 if success else 1
│  │  │  └─ Returns: 1 (failure)
│  │  │
│  │  └─ Returns to __main__
│  │
│  └─ sys.exit(1)
│
└─ Exit code: 1

NETWORK CALLS: ✅ ZERO
SELENIUM EXECUTION: ✅ NO
PDF DOWNLOADS: ✅ ZERO

Error: "No PDF sources registered for year 2010"
```

---

## run_scr_pipeline.py Execution Trace

```
$ python -m src.pipeline.run_scr_pipeline --year 2010
│
├─ __main__.py wrapper loads module
│  │
│  ├─ Import: src/pipeline/run_scr_pipeline.py
│  │  │
│  │  ├─ import json         ← IMPORTED
│  │  ├─ from pathlib import Path
│  │  ├─ from typing import Dict, List, Optional
│  │  ├─ from datetime import datetime
│  │  │
│  │  ├─ from config.settings import OUTPUT_DIR, RAW_PDFs_DIR, ...
│  │  │
│  │  ├─ from config.constants import SCR_CASE_SCHEMA
│  │  │
│  │  ├─ from src.utils import ... (utilities)
│  │  │
│  │  ├─ from src.automation.scr_pdf_discovery import discover_pdfs_for_year
│  │  │  ├─ scr_pdf_discovery.py imported
│  │  │  │  ├─ from pathlib import Path
│  │  │  │  ├─ from typing import Dict, List, Optional
│  │  │  │  ├─ import json
│  │  │  │  ├─ from datetime import datetime
│  │  │  │  └─ ✅ NO network imports
│  │  │  └─ Returns: discover_pdfs_for_year function
│  │  │
│  │  ├─ from src.extraction.pdf_text_extractor import PDFTextExtractor
│  │  │  │
│  │  │  ├─ Try to import PDFTextExtractor from pdf_text_extractor.py
│  │  │  │  │
│  │  │  │  ├─ pdf_text_extractor.py contains:
│  │  │  │  │  ├─ import pdfplumber
│  │  │  │  │  ├─ def extract_text_from_pdf(pdf_path: str): ...
│  │  │  │  │  └─ ❌ NO class PDFTextExtractor
│  │  │  │  │
│  │  │  │  └─ ❌ ImportError: cannot import name 'PDFTextExtractor'
│  │  │  │
│  │  │  └─ ❌ MODULE IMPORT FAILS
│  │  │
│  │  └─ ❌ run_scr_pipeline.py cannot be imported
│  │
│  └─ ❌ IMPORT ERROR - CANNOT PROCEED
│
└─ Exit: ImportError

NETWORK CALLS: N/A (import failed)
SELENIUM EXECUTION: ❌ NO (import failed)
PDF DOWNLOADS: ❌ NO (import failed)

Error: ImportError: cannot import name 'PDFTextExtractor' from 'src.extraction.pdf_text_extractor'
```

---

## sci_judgement_date_client.py Execution Trace

```
Manual invocation (not part of normal pipeline):
$ python -c "from src.acquisition.sci_judgement_date_client import SCIJudgementDateClient; client = SCIJudgementDateClient()"
│
├─ Import: sci_judgement_date_client.py
│  │
│  ├─ import time
│  ├─ from selenium import webdriver      ← IMPORTED
│  ├─ from selenium.webdriver.common.by import By
│  ├─ from selenium.webdriver.chrome.service import Service
│  ├─ from selenium.webdriver.chrome.options import Options
│  ├─ from selenium.webdriver.support.ui import WebDriverWait
│  ├─ from selenium.webdriver.support import expected_conditions as EC
│  ├─ from webdriver_manager.chrome import ChromeDriverManager
│  │
│  ├─ class SCIJudgementDateClient: ← CLASS DEFINED (not instantiated)
│  │  └─ Methods defined but not called
│  │
│  └─ ✅ Module imports complete - NO NETWORK CALLS
│
├─ Instantiate: SCIJudgementDateClient()
│  │
│  ├─ __init__()
│  │  │
│  │  ├─ print("Launching Chrome...")
│  │  │
│  │  ├─ chrome_options = Options()
│  │  │
│  │  ├─ chrome_options.add_argument("--start-maximized")
│  │  ├─ ... (more arguments)
│  │  │
│  │  ├─ self.driver = webdriver.Chrome(
│  │  │      service=Service(ChromeDriverManager().install()),
│  │  │      options=chrome_options
│  │  │  )
│  │  │  │
│  │  │  ├─ ChromeDriverManager().install()
│  │  │  │  └─ 🌐 NETWORK CALL #1: Download chromedriver (if not cached)
│  │  │  │
│  │  │  ├─ webdriver.Chrome(...)
│  │  │  │  └─ Launches Chrome browser process
│  │  │  │
│  │  │  └─ Browser is now open
│  │  │
│  │  ├─ self.wait = WebDriverWait(self.driver, 30)
│  │  │
│  │  └─ ✅ Instance created with Chrome browser running
│  │
│  └─ Returns: SCIJudgementDateClient instance with browser open
│
├─ Call: client.open_page()
│  │
│  ├─ print("Opening judgement date page...")
│  │
│  ├─ self.driver.get("https://www.sci.gov.in/judgements-judgement-date/")
│  │  │
│  │  └─ 🌐 NETWORK CALL #2: GET request to SCI website
│  │     ├─ Browser navigates to URL
│  │     ├─ Page loads in Chrome
│  │     └─ 🌐 Additional network calls for page resources (CSS, JS, etc)
│  │
│  ├─ self.wait.until(EC.presence_of_element_located((By.ID, "from_date")))
│  │  └─ Waits for DOM element (no network call)
│  │
│  └─ ✅ Page loaded
│
├─ Call: client.fill_dates("01-01-2010", "31-12-2010")
│  │
│  ├─ self.driver.execute_script(...)  (JavaScript execution)
│  │
│  └─ ✅ Form filled (in browser memory)
│
├─ Call: client.click_search()
│  │
│  ├─ print("\n⚠️ Solve CAPTCHA manually in browser.")
│  ├─ input("After solving CAPTCHA press ENTER here...")
│  │  │
│  │  └─ ⚠️ BLOCKS - WAITING FOR HUMAN INPUT
│  │
│  ├─ [User manually solves CAPTCHA in browser]
│  │  └─ 🌐 CAPTCHA solution sent to SCI server (user's browser)
│  │
│  ├─ [User presses ENTER]
│  │  └─ Execution resumes
│  │
│  ├─ search_btn = self.driver.find_element(...)
│  │  └─ Finds search button element
│  │
│  ├─ search_btn.click()
│  │  │
│  │  └─ 🌐 NETWORK CALL #3: POST request with search parameters
│  │     ├─ Browser sends form data to SCI website
│  │     ├─ Server processes search
│  │     └─ Returns results page
│  │
│  ├─ self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
│  │  └─ Waits for results table (no network)
│  │
│  ├─ time.sleep(2)
│  │
│  └─ ✅ Search complete
│
├─ Call: client.extract_pdf_links()
│  │
│  ├─ links = self.driver.find_elements(By.TAG_NAME, "a")
│  │  └─ Finds all links in page (already loaded)
│  │
│  ├─ for link in links:
│  │  ├─ href = link.get_attribute("href")
│  │  └─ Check if PDF link
│  │
│  └─ Returns: list of PDF URLs
│
├─ Call: client.close()
│  │
│  └─ self.driver.quit()
│     └─ Closes Chrome browser
│
└─ Returns: PDF links found

NETWORK CALLS: 
├─ 🌐 ChromeDriverManager().install()
├─ 🌐 Page load (GET https://www.sci.gov.in/...)
├─ 🌐 CAPTCHA solve (user's browser, manual)
├─ 🌐 Search form submit (POST)
└─ 🌐 + Additional resource loads (CSS, JS, images)

SELENIUM EXECUTION: ✅ YES
CHROME BROWSER: ✅ LAUNCHED AND RUNNING
MANUAL INTERVENTION: ⚠️ REQUIRED (CAPTCHA)
AUTOMATION LEVEL: ❌ NOT FULLY AUTOMATED (manual CAPTCHA step)

INTEGRATION STATUS: ❌ NOT INTEGRATED INTO MAIN PIPELINE
```

---

## Summary: Which Modules Execute Network Code in Each Scenario

| Scenario | Module | Network Method | Executes? |
|----------|--------|-----------------|-----------|
| **pytest** | test_*.py | (none) | ❌ No |
| **pytest** | conftest.py | (none) | ❌ No |
| **run_acquisition** | scr_pdf_fetcher.py | requests.get() | ❌ No (sources empty) |
| **run_acquisition** | sci_judgement_date_client.py | webdriver.get() | ❌ No (not imported) |
| **run_scr_pipeline** | (not executed) | (not executed) | ❌ No (import fails) |
| **Manual browser** | sci_judgement_date_client.py | webdriver.get() | ✅ Yes |
| **Manual browser** | sci_judgement_date_client.py | form.click() | ✅ Yes |

---

## Bottom Line

```
Import-time behavior:
└─ ✅ All modules import successfully (except run_scr_pipeline)
└─ ✅ No network calls during imports
└─ ✅ Only class/function definitions occur
└─ ❌ PDFTextExtractor class missing (import error in run_scr_pipeline)

Execution-time behavior:
└─ ✅ pytest: Pure in-memory testing, zero network
└─ ✅ run_acquisition: Fails before reaching network code
└─ ❌ run_scr_pipeline: Fails at import
└─ ⚠️ Manual browser: Makes network calls, requires manual CAPTCHA

Network-capable modules (but not called):
└─ scr_pdf_fetcher.py: requests.get() available but unused (sources empty)
└─ sci_judgement_date_client.py: selenium webdriver available but unused/unintegrated
```
