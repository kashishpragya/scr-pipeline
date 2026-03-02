"""
Pytest configuration and shared fixtures for SCR Pipeline tests.
"""

import pytest
from pathlib import Path
import json
import tempfile
import shutil

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    
    # Create directory structure
    (workspace / "data" / "raw_pdfs" / "2010").mkdir(parents=True)
    (workspace / "data" / "extracted_text" / "2010").mkdir(parents=True)
    (workspace / "data" / "output").mkdir(parents=True)
    (workspace / "logs" / "checkpoints").mkdir(parents=True)
    
    yield workspace
    
    # Cleanup happens automatically with tmp_path


@pytest.fixture
def sample_case_text():
    """Provide sample SCR case text for testing."""
    return """
ABC v. XYZ
[Coram: Hon'ble Justice John Smith, Hon'ble Justice Jane Doe]

This is a sample court judgment from Supreme Court Reports.

The petitioner alleged several violations of the Indian Penal Code, 1860, 
particularly Section 405 and Section 420.

The Court also referred to the Code of Civil Procedure, 1908 and 
Article 226 of the Constitution of India, 1950.

The Bench held that the actions violated Section 405, IPC.
"""


@pytest.fixture
def sample_multi_case_text():
    """Provide sample text with multiple cases for splitting tests."""
    return """
ABC v. XYZ
[Coram: Justice Smith, Justice Doe]
Page 100

This is Case 1 text here with case details.

---

DEF v. GHI
[Coram: Justice Johnson]
Page 105

This is Case 2 text with different judge and parties.

---

JKL v. MNO
vs. PQR
Page 110

This is Case 3 with vs. pattern in name.
"""


@pytest.fixture
def schema_valid_case():
    """Provide a valid case dictionary."""
    return {
        "court": "Supreme Court of India",
        "case_number": "",
        "petition_type": "",
        "petition_format": "",
        "judges": ["John Smith", "Jane Doe"],
        "petitioner": [],
        "respondent": [],
        "case_name": "ABC v. XYZ",
        "acts_referred": ["Indian Penal Code, 1860", "Code of Civil Procedure, 1908"],
        "sections_referred": ["405", "420"],
        "subject_categories": [],
    }


@pytest.fixture
def schema_invalid_case():
    """Provide an invalid case dictionary (missing required keys)."""
    return {
        "court": "Supreme Court of India",
        "case_name": "ABC v. XYZ",
        "judges": ["John Smith"],
        # Missing other required keys
    }


@pytest.fixture
def sample_judge_names():
    """Provide sample judge names for normalization testing."""
    return [
        "Hon'ble Justice John Smith",
        "The Hon'ble Mr. Justice Jane Doe",
        "Dr. Justice Williams",
        "Justice A.K. Sharma",
    ]


@pytest.fixture
def sample_act_names():
    """Provide sample act names for normalization testing."""
    return [
        "Indian Penal Code, 1860",
        "IPC",
        "Code of Civil Procedure, 1908",
        "CPC",
        "The Constitution of India, 1950",
    ]


@pytest.fixture
def sample_case_data_for_normalization():
    """Provide sample case data for normalization pipeline testing."""
    return [
        {
            "court": "Supreme Court of India",
            "case_number": "",
            "petition_type": "",
            "petition_format": "",
            "judges": ["Hon'ble Justice JOHN SMITH", "THE JUSTICE JANE DOE"],
            "petitioner": [],
            "respondent": [],
            "case_name": "ABC v. XYZ",
            "acts_referred": ["IPC", "Code of Civil Procedure, 1908"],
            "sections_referred": ["405", "405", "420"],
            "subject_categories": [],
        },
        {
            "court": "Supreme Court of India",
            "case_number": "",
            "petition_type": "",
            "petition_format": "",
            "judges": ["Justice A.K. Sharma", "Justice A.K. Sharma"],  # Duplicate
            "petitioner": [],
            "respondent": [],
            "case_name": "DEF v. GHI",
            "acts_referred": ["Indian Penal Code, 1860", "IPC"],  # Duplicate
            "sections_referred": [],
            "subject_categories": [],
        },
    ]
