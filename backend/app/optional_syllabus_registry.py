"""UPSC CSE optional syllabus registry.

Only verified topic groups are exposed as loaded. A subject is marked complete only when
both Paper-I and Paper-II are fully transcribed and checked against an official UPSC CSE
notification. This prevents the app from pretending that partial optional data is complete.
"""

from copy import deepcopy

OFFICIAL_NOTIFICATION_SOURCE = "https://upsc.gov.in/sites/default/files/Notif-CSP-2025-Engl-220125.pdf"
OFFICIAL_PYQ_SOURCE = "https://www.upsc.gov.in/examinations/previous-question-papers"

# Verified transcription currently being expanded subject-by-subject.  `complete=False`
# is deliberate until every numbered/sub-numbered syllabus point for both papers is loaded.
OPTIONAL_DATA = {
    "Anthropology": {
        "source_url": OFFICIAL_NOTIFICATION_SOURCE,
        "complete": False,
        "papers": [
            {
                "paper": "Paper-I",
                "topics": [
                    "1.1 Meaning, scope and development of Anthropology",
                    "1.2 Relationships with other disciplines",
                    "1.3 Main branches of Anthropology and their relevance",
                    "1.4 Human evolution and emergence of man",
                    "1.5 Primates: characteristics, taxonomy, adaptations and behaviour",
                    "1.6 Fossil hominids and phylogenetic status",
                    "1.7 Biological basis of life",
                    "1.8 Prehistoric archaeology and cultural evolution",
                    "2 Culture: concept, characteristics and theories",
                    "3 Society, social institutions and social organisation",
                    "4 Economic organisation",
                    "5 Political organisation and social control",
                    "6 Religion and magic",
                    "7 Anthropological theories",
                    "8 Research methods in Anthropology",
                    "9 Human genetics and biological variation",
                    "10 Human growth and development",
                    "11 Fertility and demographic anthropology",
                    "12 Applications of Anthropology",
                ],
                "fully_verified": False,
            },
            {
                "paper": "Paper-II",
                "topics": [
                    "1 Evolution of Indian culture and civilization, palaeo-anthropology and ethno-archaeology",
                    "2 Demographic profile of India",
                    "3 Traditional Indian social system and social change",
                    "4 Emergence and growth of Anthropology in India",
                    "5 Indian village studies and linguistic/religious minorities",
                    "6 Tribal situation in India and constitutional safeguards",
                    "7 Social change, ethnicity and tribal movements",
                    "8 Religion, tribes and nation-state",
                    "9 Tribal administration, development and applied Anthropology",
                ],
                "fully_verified": False,
            },
        ],
    },
}


def get_optional_subject(subject: str):
    data = OPTIONAL_DATA.get(subject)
    if not data:
        return {
            "subject": subject,
            "source_url": OFFICIAL_NOTIFICATION_SOURCE,
            "pyq_source_url": OFFICIAL_PYQ_SOURCE,
            "complete": False,
            "papers": [
                {"paper": "Paper-I", "topics": [], "fully_verified": False},
                {"paper": "Paper-II", "topics": [], "fully_verified": False},
            ],
        }
    out = deepcopy(data)
    out["subject"] = subject
    out["pyq_source_url"] = OFFICIAL_PYQ_SOURCE
    return out


def optional_topic_is_verified(subject: str, paper: str, topic: str) -> bool:
    data = OPTIONAL_DATA.get(subject)
    if not data or not data.get("complete"):
        return False
    for p in data.get("papers", []):
        if p.get("paper") == paper and p.get("fully_verified") and topic in p.get("topics", []):
            return True
    return False


def optional_coverage(subjects):
    complete = []
    partial = []
    empty = []
    for subject in subjects:
        data = get_optional_subject(subject)
        if data.get("complete"):
            complete.append(subject)
        elif any(p.get("topics") for p in data.get("papers", [])):
            partial.append(subject)
        else:
            empty.append(subject)
    return {
        "total_subjects": len(subjects),
        "complete_subjects": complete,
        "partial_subjects": partial,
        "not_loaded_subjects": empty,
        "complete_count": len(complete),
        "partial_count": len(partial),
        "not_loaded_count": len(empty),
    }
