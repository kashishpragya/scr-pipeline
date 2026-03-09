import re
from typing import List, Dict
from collections import defaultdict
from src.extraction.pdf_text_extractor import split_text_into_chunks


# ===============================
# Helper Functions
# ===============================

def extract_court(text: str) -> str:
    if "SUPREME COURT OF INDIA" in text.upper():
        return "Supreme Court of India"
    return ""


def extract_case_number(text: str) -> str:
    match = re.search(
        r"(CRIMINAL|CIVIL|WRIT|SLP|C\.A\.|CRL\.A\.|R\.P\.).*?NO\.?.*?\d+.*?\d{4}",
        text,
        re.IGNORECASE,
    )
    return match.group(0).strip() if match else ""


def extract_petition_type(case_number: str) -> str:
    if not case_number:
        return ""

    cn = case_number.upper()

    if "CRL" in cn:
        return "Criminal Appeal"
    if "CIVIL" in cn or "C.A." in cn:
        return "Civil Appeal"
    if "WRIT" in cn:
        return "Writ Petition"
    if "SLP" in cn:
        if "CRL" in cn:
            return "Special Leave Petition (Criminal)"
        return "Special Leave Petition (Civil)"
    if "R.P." in cn:
        if "CRL" in cn:
            return "Review Petition (Criminal)"
        return "Review Petition (Civil)"
    return ""


def extract_parties(text: str):
    petitioner = []
    respondent = []

    pet_match = re.search(r"\n(.+?)\s*…?\s*(Appellant|Petitioner)", text)
    if pet_match:
        petitioner.append(pet_match.group(1).strip())

    resp_match = re.search(
        r"Versus\s*\n(.+?)\s*…?\s*(Respondents?|Respondent)",
        text,
        re.IGNORECASE,
    )
    if resp_match:
        respondent.append(resp_match.group(1).strip())

    return petitioner, respondent


def extract_case_name(petitioner: List[str], respondent: List[str]) -> str:
    if petitioner and respondent:
        return f"{petitioner[0]} v. {respondent[0]}"
    return ""


def extract_judges(text: str) -> List[str]:
    judges = set()

    matches = re.findall(
        r"JUSTICE\s+([A-Z.\s]+)",
        text,
        re.IGNORECASE,
    )

    for m in matches:
        clean = m.strip()
        clean = re.sub(r"\s+", " ", clean)
        clean = clean.title()
        judges.add(clean)

    return sorted(list(judges))


# ===============================
# Improved Section Extraction
# ===============================

def extract_sections(text: str) -> List[str]:
    sections = set()

    # Section 302 IPC / Sec. 420 / u/s 498A
    pattern1 = re.findall(
        r"(?:Section|Sec\.?|S\.?|u/s)\s*(\d+[A-Za-z\-]*)",
        text,
        re.IGNORECASE,
    )

    # Article 14 / Article 21
    pattern2 = re.findall(
        r"Article\s*(\d+[A-Za-z\-]*)",
        text,
        re.IGNORECASE,
    )

    for sec in pattern1:
        sections.add(f"Section {sec}")

    for art in pattern2:
        sections.add(f"Article {art}")

    return sorted(list(sections))


# ===============================
# Improved Act Detection
# ===============================

def extract_acts(text: str) -> List[str]:
    acts = set()

    patterns = {
        "Indian Penal Code": r"\bIPC\b|\bIndian Penal Code\b",
        "Code of Criminal Procedure": r"\bCr\.?P\.?C\.?\b|Code of Criminal Procedure",
        "Constitution of India": r"\bConstitution\b",
        "Evidence Act": r"\bEvidence Act\b",
        "Motor Vehicles Act": r"\bMotor Vehicles Act\b",
        "Income Tax Act": r"\bIncome Tax Act\b",
    }

    for act, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            acts.add(act)

    return sorted(list(acts))


def extract_subject_categories(petition_type: str, acts: List[str]) -> List[str]:
    subjects = set()

    if "Indian Penal Code" in acts or "Criminal" in petition_type:
        subjects.add("Criminal Law")

    if "Constitution of India" in acts or "Writ" in petition_type:
        subjects.add("Constitutional Law")

    if not subjects:
        subjects.add("Civil Law")

    return sorted(list(subjects))


# ===============================
# Base Extraction
# ===============================

def extract_metadata(text: str) -> Dict:

    court = extract_court(text)
    case_number = extract_case_number(text)
    petition_type = extract_petition_type(case_number)

    petitioner, respondent = extract_parties(text)
    case_name = extract_case_name(petitioner, respondent)

    judges = extract_judges(text)
    sections_referred = extract_sections(text)
    acts_referred = extract_acts(text)
    subject_categories = extract_subject_categories(petition_type, acts_referred)

    return {
        "court": court,
        "case_number": case_number,
        "petition_type": petition_type,
        "petition_format": "",
        "judges": judges,
        "petitioner": petitioner,
        "respondent": respondent,
        "case_name": case_name,
        "acts_referred": acts_referred,
        "sections_referred": sections_referred,
        "subject_categories": subject_categories,
    }


# ===============================
# Chunk-Based Aggregation
# ===============================

def extract_metadata_with_chunking(full_text: str) -> Dict:

    if not full_text:
        return {}

    chunks = split_text_into_chunks(full_text)

    # PRIORITIZE FIRST 3 CHUNKS (header + summary)
    priority_chunks = chunks[:3]
    remaining_chunks = chunks[3:]

    aggregated = defaultdict(set)
    final = {
        "court": "",
        "case_number": "",
        "petition_type": "",
    }

    # Process priority chunks fully
    for chunk in priority_chunks:

        if not final["court"]:
            final["court"] = extract_court(chunk)

        if not final["case_number"]:
            final["case_number"] = extract_case_number(chunk)

        aggregated["judges"].update(extract_judges(chunk))
        aggregated["acts_referred"].update(extract_acts(chunk))
        aggregated["sections_referred"].update(extract_sections(chunk))

    # Remaining chunks: only extract sections & acts
    for chunk in remaining_chunks:
        aggregated["acts_referred"].update(extract_acts(chunk))
        aggregated["sections_referred"].update(extract_sections(chunk))

    final["petition_type"] = extract_petition_type(final["case_number"])

    subject_categories = extract_subject_categories(
        final["petition_type"],
        list(aggregated["acts_referred"]),
    )

    return {
        "court": final["court"],
        "case_number": final["case_number"],
        "petition_type": final["petition_type"],
        "petition_format": "",
        "judges": sorted(list(aggregated["judges"])),
        "petitioner": [],
        "respondent": [],
        "case_name": "",
        "acts_referred": sorted(list(aggregated["acts_referred"])),
        "sections_referred": sorted(list(aggregated["sections_referred"])),
        "subject_categories": subject_categories,
    }