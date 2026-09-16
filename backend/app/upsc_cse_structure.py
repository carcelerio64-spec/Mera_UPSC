"""UPSC Civil Services Examination structural coverage contract.

Detailed syllabus text is stored separately.  This module is the hard validation boundary used
by APIs/tests so no compulsory paper or Optional Paper-I/Paper-II can silently disappear.
"""

OFFICIAL_NOTIFICATION_SOURCE = "https://upsc.gov.in/sites/default/files/Notif-CSP-2025-Engl-220125.pdf"
OFFICIAL_PYQ_SOURCE = "https://www.upsc.gov.in/examinations/previous-question-papers"

PRELIMS_PAPERS = (
    "General Studies Paper-I",
    "General Studies Paper-II (CSAT)",
)
MAINS_QUALIFYING_PAPERS = ("Paper-A Indian Language", "Paper-B English")
MAINS_COMPULSORY_MERIT_PAPERS = (
    "Essay", "General Studies-I", "General Studies-II", "General Studies-III", "General Studies-IV",
)
OPTIONAL_PAPERS = ("Paper-I", "Paper-II")

NON_LITERATURE_OPTIONALS = (
    "Agriculture", "Animal Husbandry and Veterinary Science", "Anthropology", "Botany", "Chemistry",
    "Civil Engineering", "Commerce and Accountancy", "Economics", "Electrical Engineering", "Geography",
    "Geology", "History", "Law", "Management", "Mathematics", "Mechanical Engineering", "Medical Science",
    "Philosophy", "Physics", "Political Science and International Relations", "Psychology",
    "Public Administration", "Sociology", "Statistics", "Zoology",
)
LITERATURE_LANGUAGES = (
    "Assamese", "Bengali", "Bodo", "Dogri", "Gujarati", "Hindi", "Kannada", "Kashmiri", "Konkani",
    "Maithili", "Malayalam", "Manipuri", "Marathi", "Nepali", "Odia", "Punjabi", "Sanskrit", "Santhali",
    "Sindhi", "Tamil", "Telugu", "Urdu", "English",
)
LITERATURE_OPTIONALS = tuple(f"{x} Literature" for x in LITERATURE_LANGUAGES)
ALL_OPTIONALS = NON_LITERATURE_OPTIONALS + LITERATURE_OPTIONALS
COMPULSORY_INDIAN_LANGUAGES = tuple(x for x in LITERATURE_LANGUAGES if x != "English")

# Every selectable optional is contractually required to expose both papers.  Topic-level data may
# still report incomplete/unverified in optional_syllabus_registry; consumers must respect that flag.
OPTIONAL_PAPER_REQUIREMENTS = {
    subject: {"required_papers": OPTIONAL_PAPERS, "source": OFFICIAL_NOTIFICATION_SOURCE}
    for subject in ALL_OPTIONALS
}

REQUIRED_EXAM_STRUCTURE = {
    "prelims": PRELIMS_PAPERS,
    "mains_qualifying": MAINS_QUALIFYING_PAPERS,
    "mains_merit": MAINS_COMPULSORY_MERIT_PAPERS,
    "optional_papers": OPTIONAL_PAPERS,
}


def structural_coverage():
    return {
        "prelims_papers": len(PRELIMS_PAPERS),
        "mains_compulsory_merit_papers": len(MAINS_COMPULSORY_MERIT_PAPERS),
        "mains_qualifying_papers": len(MAINS_QUALIFYING_PAPERS),
        "optional_papers_per_subject": len(OPTIONAL_PAPERS),
        "non_literature_optionals": len(NON_LITERATURE_OPTIONALS),
        "literature_optionals": len(LITERATURE_OPTIONALS),
        "total_optional_choices": len(ALL_OPTIONALS),
        "required_optional_paper_slots": len(ALL_OPTIONALS) * len(OPTIONAL_PAPERS),
        "compulsory_indian_languages": len(COMPULSORY_INDIAN_LANGUAGES),
        "notification_source": OFFICIAL_NOTIFICATION_SOURCE,
        "pyq_source": OFFICIAL_PYQ_SOURCE,
    }


def validate_structure():
    assert len(PRELIMS_PAPERS) == 2 and len(set(PRELIMS_PAPERS)) == 2
    assert len(MAINS_QUALIFYING_PAPERS) == 2
    assert len(MAINS_COMPULSORY_MERIT_PAPERS) == 5
    assert OPTIONAL_PAPERS == ("Paper-I", "Paper-II")
    assert len(NON_LITERATURE_OPTIONALS) == 25
    assert len(LITERATURE_LANGUAGES) == 23
    assert len(ALL_OPTIONALS) == 48 and len(set(ALL_OPTIONALS)) == 48
    assert len(COMPULSORY_INDIAN_LANGUAGES) == 22
    assert set(OPTIONAL_PAPER_REQUIREMENTS) == set(ALL_OPTIONALS)
    assert all(tuple(v["required_papers"]) == OPTIONAL_PAPERS for v in OPTIONAL_PAPER_REQUIREMENTS.values())
    assert "Hindi Literature" in ALL_OPTIONALS and "English Literature" in ALL_OPTIONALS
    return True


validate_structure()
