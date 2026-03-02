"""
EXAMPLES - SCR Pipeline Output Examples & Use Cases

Examples of extracted data and how to interpret results.
"""

# ==================== INPUT/OUTPUT EXAMPLES ====================

## Example 1: Simple Case Extraction

### Input: Raw PDF Text (scanned from PDF volume)

```
HARISH CHANDRA MISRA v. GOVERNMENT OF INDIA
[Reported in [2014] 6 S.C.R. 543]
[Coram: Hon'ble Justice A.K. Goel, Hon'ble Justice U.U. Lalit]
Page 543

The petitioner, Harish Chandra Misra, seeks redressal of his grievance
arising from violation of Section 405 and Section 420 of the Indian
Penal Code, 1860. The respondent, Government of India, filed a reply.

The Constitution of India, 1950, which guarantees the right under
Article 226, was also cited.

The Bench directed compliance with Section 405 of the IPC.

JUDGMENT

...judgment text here...
```

### Output: Extracted Case JSON

```json
{
  "court": "Supreme Court of India",
  "case_number": "",
  "petition_type": "",
  "petition_format": "",
  "judges": [
    "A.K. Goel",
    "U.U. Lalit"
  ],
  "petitioner": [],
  "respondent": [],
  "case_name": "HARISH CHANDRA MISRA v. GOVERNMENT OF INDIA",
  "acts_referred": [
    "Indian Penal Code, 1860",
    "Constitution of India, 1950"
  ],
  "sections_referred": [
    "405",
    "420",
    "226"
  ],
  "subject_categories": []
}
```

### Explanation

- **case_name**: Extracted from first all-caps line with "v." pattern
- **judges**: Extracted from `[Coram: ...]` brackets, normalized (titles removed)
- **acts_referred**: Found explicitly named in text with years
- **sections_referred**: Found from patterns like "Section 405", "Article 226"
- **Empty fields**: `case_number`, `petition_type`, `petitioner`, `respondent` are not extracted (not explicit in court text)

---

## Example 2: Case with Minimal Metadata

### Input: Raw Text with Limited Information

```
ABC v. XYZ

A case about property rights. The parties disputed over ownership
of land in Delhi. Various precedents were cited, but no explicit
legal acts or sections were mentioned in this brief judgment.

The matter was disposed of accordingly.
```

### Output: Extracted Case

```json
{
  "court": "Supreme Court of India",
  "case_number": "",
  "petition_type": "",
  "petition_format": "",
  "judges": [],
  "petitioner": [],
  "respondent": [],
  "case_name": "ABC v. XYZ",
  "acts_referred": [],
  "sections_referred": [],
  "subject_categories": []
}
```

### Explanation

- **case_name**: Extracted from "ABC v. XYZ"
- **judges**: Empty (no explicit judge information)
- **acts_referred**: Empty (no acts explicitly named)
- **sections_referred**: Empty (no sections cited)

**This is correct behavior!** The system prefers missing data over guessed data.

---

## Example 3: Multiple Cases in One Volume

### Input: Text with Three Cases

```
ABC v. XYZ
[Coram: Justice Smith]

Text of case 1 here...

---

DEF v. GHI
[Coram: Justice Johnson]

Text of case 2 here...

---

JKL v. MNO
[Coram: Justice Williams]

Text of case 3 here...
```

### Output: Three Separate Case Objects

```json
[
  {
    "court": "Supreme Court of India",
    "case_name": "ABC v. XYZ",
    "judges": ["Smith"],
    "acts_referred": [],
    "sections_referred": [],
    ...
  },
  {
    "court": "Supreme Court of India",
    "case_name": "DEF v. GHI",
    "judges": ["Johnson"],
    "acts_referred": [],
    "sections_referred": [],
    ...
  },
  {
    "court": "Supreme Court of India",
    "case_name": "JKL v. MNO",
    "judges": ["Williams"],
    "acts_referred": [],
    "sections_referred": [],
    ...
  }
]
```

### Explanation

- Each case is split at boundaries (CORAM, separators)
- Each becomes a separate JSON object
- Total: 3 cases extracted from 1 volume

---

## Example 4: Case with Multiple Acts and Sections

### Input: Complex Legal Case

```
STATE OF MAHARASHTRA v. RAJENDRA SONI
[Coram: Hon'ble Justice P.N. Bhagwati, Hon'ble Justice V. Krishnamurthy]

The petitioner contends violation of Sections 406, 420, and 120B of
the Indian Penal Code, 1860. Additionally, the Code of Criminal
Procedure, 1973, Section 304 was considered.

The respondent cited the Hindu Succession Act, 1956 regarding property
rights. The Court examined Articles 21 and 226 of the Constitution of
India, 1950.

Under the Bharatiya Nyaya Sanhita, 2023, new provisions were also
considered. Sec. 168A was particularly relevant.
```

### Output: Extracted Case

```json
{
  "court": "Supreme Court of India",
  "case_number": "",
  "petition_type": "",
  "petition_format": "",
  "judges": [
    "P.N. Bhagwati",
    "V. Krishnamurthy"
  ],
  "petitioner": [],
  "respondent": [],
  "case_name": "STATE OF MAHARASHTRA v. RAJENDRA SONI",
  "acts_referred": [
    "Indian Penal Code, 1860",
    "Code of Criminal Procedure, 1973",
    "Hindu Succession Act, 1956",
    "Constitution of India, 1950",
    "Bharatiya Nyaya Sanhita, 2023"
  ],
  "sections_referred": [
    "406",
    "420",
    "120B",
    "304",
    "21",
    "226",
    "168A"
  ],
  "subject_categories": []
}
```

### Explanation

- **Multiple judges**: All extracted and normalized
- **Multiple acts**: All recognized ones are included
- **Mixed sections**: Both numbered and lettered (120B), various references (Sec., Section, Article) all normalized

---

# ==================== PIPELINE OUTPUT STRUCTURE ====================

## Main Output File Format

**Location:** `data/output/scr_YYYY.json`

**Structure:** Array of case objects

```json
[
  { case_object_1 },
  { case_object_2 },
  ...
  { case_object_N }
]
```

**Total file size:** Typically 2-10 MB for a year (1000+ cases)

---

## Execution Summary

**Location:** `logs/execution_summary_YYYY.json`

### Example Summary for Year 2010

```json
{
  "year": 2010,
  "timestamp": "2026-02-18T10:30:45.123456",
  "status": "success",
  "total_cases_extracted": 1247,
  "invalid_cases": 3,
  "output_file": "/path/to/data/output/scr_2010.json",
  "output_file_size_bytes": 5242880,
  "case_statistics": {
    "total_with_names": 1247,
    "total_with_judges": 1200,
    "total_with_acts": 856,
    "total_with_sections": 920
  },
  "phases_completed": [
    "phase_0",
    "phase_1",
    "phase_2",
    "phase_3",
    "phase_4",
    "phase_5",
    "phase_6"
  ],
  "checkpoints_used": [],
  "errors_encountered": []
}
```

### Interpretation

- **total_cases_extracted**: 1247 cases successfully extracted
- **total_with_judges**: 1200 (96%) have judge information
- **total_with_acts**: 856 (69%) cite legal acts
- **total_with_sections**: 920 (74%) cite specific sections
- **invalid_cases**: 3 failed schema validation (shouldn't happen)

---

## Detailed Execution Log

**Location:** `logs/execution_log_YYYY.json`

Contains detailed phase-by-phase information:

```json
{
  "year": 2010,
  "status": "success",
  "phases": {
    "phase_0": {
      "status": "complete",
      "directories_initialized": true
    },
    "phase_2": {
      "status": "complete",
      "pdfs_processed": 15,
      "pdfs_successful": 14,
      "pdfs_failed": 1,
      "total_pages": 3247,
      "failed_pdfs": [
        {
          "filename": "volume_5.pdf",
          "error": "PDF is corrupted"
        }
      ]
    },
    "phase_4": {
      "status": "complete",
      "cases_processed": 1250,
      "cases_extracted": 1247,
      "cases_failed": 3,
      "with_judges": 1200,
      "with_acts": 856,
      "with_sections": 920,
      "failed_cases": [
        {
          "volume": "volume_8.txt",
          "case_index": 42,
          "error": "No case name found"
        }
      ]
    }
  }
}
```

---

# ==================== DATA QUALITY EXPECTATIONS ====================

## What WILL Be Extracted

✓ Case names (if case title in text with "v." or "vs.")
✓ Judges (if in explicit brackets: `[Coram: ...]`)
✓ Acts (if explicitly named with year: "Indian Penal Code, 1860")
✓ Sections (if explicitly numbered: "Section 405", "Article 226")

## What WON'T Be Extracted (By Design)

✗ Case numbers (usually not explicit)
✗ Petition types (not in PDF text)
✗ Petitioner/Respondent parties (not always clear)
✗ Subject categories (would require inference)
✗ Inferred metadata (to avoid hallucination)

---

## Data Quality Metrics

### Coverage by Field

```
Field                   Coverage    Notes
────────────────────────────────────────────────
case_name               95-99%      Almost always present
judges                  85-95%      Usually explicitly stated
acts_referred           60-75%      Often named
sections_referred       70-80%      Usually numbered
case_number             5-10%       Rarely explicit
petition_type           0%          Not in PDF
petitioner/respondent   0%          Not reliably clear
```

### Typical Output Statistics (Per Year)

```
Year 2010 Statistics:
─────────────────────
Total cases:           1,247
With judges:           1,200 (96%)
With acts cited:         856 (69%)
With sections cited:      920 (74%)
Average acts/case:     1.2
Average sections/case: 1.5
```

---

# ==================== USAGE EXAMPLES ====================

## Processing the Output JSON

### Example 1: Count Cases by Year

```python
import json

with open("data/output/scr_2010.json") as f:
    cases = json.load(f)
    
print(f"Total cases in 2010: {len(cases)}")
```

### Example 2: Find Cases by Judge

```python
import json

with open("data/output/scr_2010.json") as f:
    cases = json.load(f)

judge_name = "A.K. Goel"
cases_by_judge = [c for c in cases if judge_name in c.get("judges", [])]

print(f"{judge_name} presided over {len(cases_by_judge)} cases")
for case in cases_by_judge[:3]:
    print(f"  - {case['case_name']}")
```

### Example 3: Find Cases Citing a Specific Act

```python
import json

with open("data/output/scr_2010.json") as f:
    cases = json.load(f)

act = "Constitution of India, 1950"
cases_citing_act = [c for c in cases if act in c.get("acts_referred", [])]

print(f"{len(cases_citing_act)} cases cited {act}")
```

### Example 4: Extract All Section References

```python
import json
from collections import Counter

with open("data/output/scr_2010.json") as f:
    cases = json.load(f)

all_sections = []
for case in cases:
    all_sections.extend(case.get("sections_referred", []))

section_counts = Counter(all_sections)
print("Most cited sections:")
for section, count in section_counts.most_common(10):
    print(f"  Section {section}: {count} times")
```

### Example 5: Compare Years

```python
import json

for year in [2010, 2015, 2020]:
    with open(f"data/output/scr_{year}.json") as f:
        cases = json.load(f)
        judges_count = len(set(j for c in cases for j in c.get("judges", [])))
        acts_count = len(set(a for c in cases for a in c.get("acts_referred", [])))
        
        print(f"Year {year}: {len(cases)} cases, {judges_count} judges, {acts_count} acts")
```

---

## Validation Examples

### Verify All Cases Are Valid

```python
import json
from src.utils import validate_case_schema

with open("data/output/scr_2010.json") as f:
    cases = json.load(f)

invalid = []
for i, case in enumerate(cases):
    is_valid, errors = validate_case_schema(case)
    if not is_valid:
        invalid.append((i, errors))

if invalid:
    print(f"Found {len(invalid)} invalid cases:")
    for idx, errors in invalid[:5]:
        print(f"  Case {idx}: {errors}")
else:
    print("✓ All cases are valid!")
```

---

## Export Examples

### Export to CSV

```python
import json
import csv

with open("data/output/scr_2010.json") as f:
    cases = json.load(f)

with open("scr_2010_export.csv", "w", newline="") as csv_f:
    writer = csv.writer(csv_f)
    writer.writerow(["Case Name", "Judges", "Acts", "Sections"])
    
    for case in cases:
        writer.writerow([
            case["case_name"],
            "; ".join(case["judges"]),
            "; ".join(case["acts_referred"]),
            "; ".join(case["sections_referred"]),
        ])

print("✓ Exported to scr_2010_export.csv")
```

### Export to SQLite

```python
import json
import sqlite3

conn = sqlite3.connect("scr_cases.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY,
        year INTEGER,
        case_name TEXT,
        judges TEXT,
        acts TEXT,
        sections TEXT
    )
""")

with open("data/output/scr_2010.json") as f:
    cases = json.load(f)

for case in cases:
    cursor.execute("""
        INSERT INTO cases (year, case_name, judges, acts, sections)
        VALUES (?, ?, ?, ?, ?)
    """, (
        2010,
        case["case_name"],
        "|".join(case["judges"]),
        "|".join(case["acts_referred"]),
        "|".join(case["sections_referred"]),
    ))

conn.commit()
print(f"✓ Loaded {len(cases)} cases into database")
```
