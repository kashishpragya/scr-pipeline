import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path

from src.acquisition.sci_judgement_date_client import SCIJudgementDateClient
from src.extraction.pdf_text_extractor import extract_text_from_pdf
from src.extraction.scr_metadata_extractor import extract_metadata_with_chunking

def classify_petition_type(case_number: str) -> str:
    if not case_number:
        return ""

    case_number = case_number.upper()

    if case_number.startswith("CRL.A"):
        return "Criminal Appeal"
    elif case_number.startswith("C.A"):
        return "Civil Appeal"
    elif case_number.startswith("W.P"):
        return "Writ Petition"
    elif case_number.startswith("SLP(CRL"):
        return "Special Leave Petition (Criminal)"
    elif case_number.startswith("SLP(C"):
        return "Special Leave Petition (Civil)"
    elif case_number.startswith("R.P.(CRL"):
        return "Review Petition (Criminal)"
    elif case_number.startswith("R.P.(C"):
        return "Review Petition (Civil)"
    elif case_number.startswith("CONMT.PET"):
        return "Contempt Petition"
    elif case_number.startswith("T.P"):
        return "Transfer Petition"
    elif case_number.startswith("MA-"):
        return "Miscellaneous Application"

    return ""
def build_case_name(petitioner, respondent):
    if petitioner and respondent:
        return f"{petitioner[0]} v. {respondent[0]}"
    return ""
# ============================================================
# LOGGER CONFIG
# ============================================================

logger = logging.getLogger("unified_builder")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


# ============================================================
# CANONICAL ACT NORMALIZATION
# ============================================================

CANONICAL_ACTS = {
    "Indian Penal Code": "Indian Penal Code",
    "IPC": "Indian Penal Code",
    "Code of Criminal Procedure": "Code of Criminal Procedure",
    "CrPC": "Code of Criminal Procedure",
    "Constitution of India": "Constitution of India"
}


def normalize_acts(acts):
    normalized = []
    for act in acts:
        act = act.strip()
        if act in CANONICAL_ACTS:
            normalized.append(CANONICAL_ACTS[act])
        else:
            normalized.append(act)
    return list(set(normalized))


# ============================================================
# CLEANERS
# ============================================================

def clean_party_name(name):
    name = name.strip()
    name = re.sub(r"\.+$", "", name)
    return name.title()


def clean_judgment_date(raw_date):
    match = re.search(r"\d{2}-\d{2}-\d{4}", raw_date)
    if not match:
        return ""

    try:
        dt = datetime.strptime(match.group(), "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        return match.group()


def extract_judges_from_bench(bench_text):
    judges = []
    lines = bench_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        line = re.sub(r"HON'?BLE\s+(MR|MS|THE)?\.?\s+JUSTICE\s+", "", line, flags=re.IGNORECASE)
        line = re.sub(r"HON'?BLE\s+THE\s+CHIEF\s+JUSTICE", "Chief Justice of India", line, flags=re.IGNORECASE)

        judges.append(line.title())

    # Remove duplicates while preserving order
    return list(dict.fromkeys(judges))


# ============================================================
# CASE NUMBER PARSER (FIXED)
# ============================================================

def parse_case_number(case_number):
    if not case_number:
        return {}

    pattern = r"([A-Za-z\.\(\)]+)\s*No\.-?\s*([0-9\-]+)\s*-\s*(\d{4})"
    match = re.search(pattern, case_number)

    if match:
        return {
            "case_type": match.group(1).strip(),
            "case_serial": match.group(2).strip(),
            "case_year": int(match.group(3))
        }

    return {}


# ============================================================
# SUBJECT CLASSIFICATION (IMPROVED)
# ============================================================

def classify_subject(petition_type, acts):
    categories = []

    if petition_type and "Criminal" in petition_type:
        categories.append("Criminal Law")

    if petition_type and "Civil" in petition_type:
        categories.append("Civil Law")

    if petition_type and "Writ" in petition_type:
        categories.append("Constitutional Law")

    if "Indian Penal Code" in acts:
        categories.append("Criminal Law")

    if "Constitution of India" in acts:
        categories.append("Constitutional Law")

    return list(set(categories))


# ============================================================
# PDF INDEX BUILDER
# ============================================================

def build_pdf_index(base_path="data/raw_pdfs"):
    pdf_index = {}

    for root, _, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_index[file] = os.path.join(root, file)

    logger.info(f"Indexed {len(pdf_index)} PDFs")
    return pdf_index


# ============================================================
# UNIFIED RECORD BUILDER (STRUCTURED SCHEMA)
# ============================================================
def build_unified_record(table_row: dict, pdf_metadata: dict) -> dict:

    petitioner = []
    respondent = []

    parties_text = table_row.get("parties", "")

    if "VS" in parties_text.upper():
        parts = re.split(r"\bVS\b", parties_text, flags=re.IGNORECASE)
        petitioner = [parts[0].strip()]
        if len(parts) > 1:
            respondent = [parts[1].strip()]
    else:
        petitioner = [parties_text.strip()] if parties_text else []

    bench_text = table_row.get("bench", "")
    judges = extract_judges_from_bench(bench_text)

    judgment_date = clean_judgment_date(
        table_row.get("judgment_raw", "")
    )

    # Clean sections but DO NOT remove anything
    sections = pdf_metadata.get("sections_referred", [])

    return {
        "court": "Supreme Court of India",

        "case_number": table_row.get("case_number") or pdf_metadata.get("case_number", ""),

        "petition_type": classify_petition_type(
            table_row.get("case_number", "")
        ),

        "petition_format": pdf_metadata.get("petition_format", ""),

        "judges": judges if judges else pdf_metadata.get("judges", []),

        "petitioner": petitioner,

        "respondent": respondent,

        "case_name": build_case_name(petitioner, respondent),

        "acts_referred": pdf_metadata.get("acts_referred", []),

        "sections_referred": sections,

        "subject_categories": pdf_metadata.get("subject_categories", [])
    }

# ============================================================
# MAIN PIPELINE
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("STAGE 5: BUILDING UNIFIED RECORDS (IMPROVED VERSION)")
    print("=" * 70 + "\n")

    pdf_index = build_pdf_index()
    client = SCIJudgementDateClient()

    try:
        rows = client.search_with_metadata_by_date_range(
            "01-01-2021",
            "31-01-2021"
        )

        unified_records = []
        skipped_missing_pdf = 0
        skipped_text_fail = 0

        for row in rows[:50]:

            pdf_url = row.get("pdf_url")
            if not pdf_url:
                skipped_missing_pdf += 1
                continue

            filename = pdf_url.split("/")[-1]

            if filename not in pdf_index:
                skipped_missing_pdf += 1
                continue

            pdf_path = pdf_index[filename]
            text = extract_text_from_pdf(pdf_path)

            if not text:
                skipped_text_fail += 1
                continue

            pdf_metadata = extract_metadata_with_chunking(text)
            unified = build_unified_record(row, pdf_metadata)
            unified_records.append(unified)

        print(f"\nBuilt {len(unified_records)} unified records")
        print(f"Skipped (missing PDF): {skipped_missing_pdf}")
        print(f"Skipped (text extraction failed): {skipped_text_fail}")

        output_dir = Path("data/final_metadata")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "2021_final_metadata_structured.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(unified_records, f, indent=2, ensure_ascii=False)

        print("\nSaved to:")
        print(output_file.resolve())

    finally:
        client.close()