import re
from typing import List, Dict


# ===============================
# Helper Functions
# ===============================

def extract_court(text: str) -> str:
    if "IN THE SUPREME COURT OF INDIA" in text:
        return "Supreme Court of India"
    return ""


def extract_case_number(text: str) -> str:
    match = re.search(
        r"(CRIMINAL|CIVIL|WRIT).*?NO\.?\s*\d+\s*OF\s*\d{4}",
        text,
        re.IGNORECASE,
    )
    return match.group(0).strip() if match else ""


def extract_petition_type(case_number: str) -> str:
    if "CRIMINAL" in case_number.upper():
        return "Criminal Appeal"
    if "CIVIL" in case_number.upper():
        return "Civil Appeal"
    if "WRIT" in case_number.upper():
        return "Writ Petition"
    return ""


def extract_parties(text: str):
    petitioner = []
    respondent = []

    pet_match = re.search(r"\n(.+?)\s*…?Appellant", text)
    if pet_match:
        petitioner.append(pet_match.group(1).strip())

    resp_match = re.search(r"Versus\s*\n(.+?)\s*…?Respondents?", text, re.IGNORECASE)
    if resp_match:
        respondent.append(resp_match.group(1).strip())

    return petitioner, respondent


def extract_case_name(petitioner: List[str], respondent: List[str]) -> str:
    if petitioner and respondent:
        return f"{petitioner[0]} v. {respondent[0]}"
    return ""


def extract_judges(text: str) -> List[str]:
    judges = []

    match = re.search(
        r"J\s*U\s*D\s*G\s*M\s*E\s*N\s*T\s*\n(.+?)\,?\s*J\.?",
        text,
        re.IGNORECASE,
    )

    if match:
        name = match.group(1).strip()

        # Remove unwanted patterns
        name = re.sub(r",?\s*CJI.*", "", name, flags=re.IGNORECASE)
        name = name.title()

        judges.append(name)

    return judges


def extract_sections(text: str) -> List[str]:
    sections = set()

    matches = re.findall(
        r"Sections?\s+([0-9,\sand]+)\s*IPC",
        text,
        re.IGNORECASE,
    )

    for group in matches:
        numbers = re.findall(r"\d+", group)
        for num in numbers:
            sections.add(num)

    return sorted(list(sections), key=lambda x: int(x))


def extract_acts(text: str) -> List[str]:
    acts = []

    if re.search(r"\bIPC\b|\bIndian Penal Code\b", text, re.IGNORECASE):
        acts.append("Indian Penal Code")

    if re.search(r"\bCr\.?P\.?C\.?\b|Code of Criminal Procedure", text, re.IGNORECASE):
        acts.append("Code of Criminal Procedure")

    if re.search(r"Constitution of India", text, re.IGNORECASE):
        acts.append("Constitution of India")

    return list(set(acts))


def extract_subject_categories(petition_type: str) -> List[str]:
    if "Criminal" in petition_type:
        return ["Criminal Law"]
    if "Civil" in petition_type:
        return ["Civil Law"]
    if "Writ" in petition_type:
        return ["Constitutional Law"]
    return []


# ===============================
# Main Extraction Function
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
    subject_categories = extract_subject_categories(petition_type)

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
from collections import defaultdict
from src.extraction.pdf_text_extractor import split_text_into_chunks


def extract_metadata_with_chunking(full_text: str) -> dict:
    """
    Improved metadata extraction using chunk-based parsing.

    Strategy:
    - Split text into chunks
    - Extract metadata from each chunk
    - Merge strongest signals
    """

    if not full_text:
        return {}

    chunks = split_text_into_chunks(full_text)

    aggregated = {
        "court": "",
        "case_number": "",
        "petition_type": "",
        "petition_format": "",
        "judges": set(),
        "petitioner": set(),
        "respondent": set(),
        "case_name": "",
        "acts_referred": set(),
        "sections_referred": set(),
        "subject_categories": set(),
    }

    for chunk in chunks:
        meta = extract_metadata(chunk)

        # Court
        if not aggregated["court"] and meta.get("court"):
            aggregated["court"] = meta["court"]

        # Case Number
        if not aggregated["case_number"] and meta.get("case_number"):
            aggregated["case_number"] = meta["case_number"]

        # Petition Type
        if meta.get("petition_type"):
            aggregated["petition_type"] = meta["petition_type"]

        # Judges
        for j in meta.get("judges", []):
            aggregated["judges"].add(j)

        # Parties
        for p in meta.get("petitioner", []):
            aggregated["petitioner"].add(p)

        for r in meta.get("respondent", []):
            aggregated["respondent"].add(r)

        # Acts
        for act in meta.get("acts_referred", []):
            aggregated["acts_referred"].add(act)

        # Sections
        for sec in meta.get("sections_referred", []):
            aggregated["sections_referred"].add(sec)

        # Subjects
        for sub in meta.get("subject_categories", []):
            aggregated["subject_categories"].add(sub)

    # Convert sets back to lists
    return {
        "court": aggregated["court"],
        "case_number": aggregated["case_number"],
        "petition_type": aggregated["petition_type"],
        "petition_format": "",
        "judges": sorted(list(aggregated["judges"])),
        "petitioner": sorted(list(aggregated["petitioner"])),
        "respondent": sorted(list(aggregated["respondent"])),
        "case_name": "",
        "acts_referred": sorted(list(aggregated["acts_referred"])),
        "sections_referred": sorted(list(aggregated["sections_referred"])),
        "subject_categories": sorted(list(aggregated["subject_categories"])),
    }