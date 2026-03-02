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
