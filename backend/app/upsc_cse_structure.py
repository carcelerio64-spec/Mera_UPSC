"""Verified UPSC Civil Services Examination structure used for coverage validation.

Source: UPSC Civil Services Examination notification.  Keep this module structural: detailed
optional topic transcription lives in optional_syllabus_registry.py and must never be marked
complete until both papers are populated and verified.
"""

OFFICIAL_NOTIFICATION_SOURCE = "https://upsc.gov.in/sites/default/files/Notif-CSP-2025-Engl-220125.pdf"
OFFICIAL_PYQ_SOURCE = "https://www.upsc.gov.in/examinations/previous-question-papers"

PRELIMS_PAPERS = (
    "General Studies Paper-I",
    "General Studies Paper-II (CSAT)",
)

MAINS_MERIT_PAPERS = (
    "Essay",
    "General Studies-I",
    "General Studies-II",
    "General Studies-III",
    "General Studies-IV",
    "Optional Paper-I",
    "Optional Paper-II",
)

MAINS_QUALIFYING_PAPERS = (
    "Paper-A Indian Language",
    "Paper-B English",
)

NON_LITERATURE_OPTIONALS = (
    "Agriculture",
    "Animal Husbandry and Veterinary Science",
    "Anthropology",
    "Botany",
    "Chemistry",
    "Civil Engineering",
    "Commerce and Accountancy",
    "Economics",
    "Electrical Engineering",
    "Geography",
    "Geology",
    "History",
    "Law",
    "Management",
    "Mathematics",
    "Mechanical Engineering",
    "Medical Science",
    "Philosophy",
    "Physics",
    "Political Science and International Relations",
    "Psychology",
    "Public Administration",
    "Sociology",
    "Statistics",
    "Zoology",
)

LITERATURE_LANGUAGES = (
    "Assamese", "Bengali", "Bodo", "Dogri", "Gujarati", "Hindi", "Kannada",
    "Kashmiri", "Konkani", "Maithili", "Malayalam", "Manipuri", "Marathi",
    "Nepali", "Odia", "Punjabi", "Sanskrit", "Santhali", "Sindhi", "Tamil",
    "Telugu", "Urdu", "English",
)

LITERATURE_OPTIONALS = tuple(f"{language} Literature" for language in LITERATURE_LANGUAGES)
ALL_OPTIONALS = NON_LITERATURE_OPTIONALS + LITERATURE_OPTIONALS

# Paper-A can be selected from the languages allowed by the UPSC notification (subject to
# notification exemptions). English is separately compulsory as Paper-B.
COMPULSORY_INDIAN_LANGUAGES = (
    "Assamese", "Bengali", "Bodo", "Dogri", "Gujarati", "Hindi", "Kannada",
    "Kashmiri", "Konkani", "Maithili", "Malayalam", "Manipuri", "Marathi",
    "Nepali", "Odia", "Punjabi", "Sanskrit", "Santhali", "Sindhi", "Tamil",
    "Telugu", "Urdu",
)


def structural_coverage():
    """Return deterministic counts used by API/tests to catch accidental omissions."""
    return {
        "prelims_papers": len(PRELIMS_PAPERS),
        "mains_merit_papers": len(MAINS_MERIT_PAPERS),
        "mains_qualifying_papers": len(MAINS_QUALIFYING_PAPERS),
        "non_literature_optionals": len(NON_LITERATURE_OPTIONALS),
        "literature_optionals": len(LITERATURE_OPTIONALS),
        "total_optional_choices": len(ALL_OPTIONALS),
        "compulsory_indian_languages": len(COMPULSORY_INDIAN_LANGUAGES),
        "notification_source": OFFICIAL_NOTIFICATION_SOURCE,
        "pyq_source": OFFICIAL_PYQ_SOURCE,
    }


def validate_structure():
    """Fail loudly if a future edit drops or duplicates an official structural entry."""
    assert len(PRELIMS_PAPERS) == 2
    assert len(MAINS_QUALIFYING_PAPERS) == 2
    assert len(NON_LITERATURE_OPTIONALS) == 25
    assert len(LITERATURE_LANGUAGES) == 23
    assert len(ALL_OPTIONALS) == 48
    assert len(set(ALL_OPTIONALS)) == len(ALL_OPTIONALS)
    assert "Hindi Literature" in ALL_OPTIONALS
    assert "English Literature" in ALL_OPTIONALS
    return True


validate_structure()
