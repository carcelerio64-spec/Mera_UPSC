"""UPSC CSE Optional syllabus registry with fail-closed completeness checks.

No subject is treated as generation-ready until both Paper-I and Paper-II contain verified
hierarchical syllabus entries.  This prevents an empty/partial Optional from producing fake papers.
"""
from copy import deepcopy
from .upsc_cse_structure import ALL_OPTIONALS, NON_LITERATURE_OPTIONALS, LITERATURE_LANGUAGES, OFFICIAL_NOTIFICATION_SOURCE, OFFICIAL_PYQ_SOURCE

OFFICIAL_OPTIONAL_SUBJECTS = list(ALL_OPTIONALS)
OPTIONAL_DATA = {
    "Anthropology": {
        "source_url": OFFICIAL_NOTIFICATION_SOURCE,
        "complete": False,
        "papers": [
            {"paper":"Paper-I","fully_verified":False,"topics":[
                {"topic":"Anthropology: meaning, scope and development","subtopics":["Relationships with other disciplines","Main branches and relevance"]},
                {"topic":"Human evolution","subtopics":["Primates","Fossil hominids","Biological basis of life","Prehistoric archaeology and cultural evolution"]},
                {"topic":"Culture and society","subtopics":["Culture concept and theories","Social institutions and organisation","Economic organisation","Political organisation and social control","Religion and magic"]},
                {"topic":"Anthropological theory and methods","subtopics":["Anthropological theories","Research methods"]},
                {"topic":"Biological anthropology","subtopics":["Human genetics and biological variation","Human growth and development","Fertility and demographic anthropology","Applications of Anthropology"]},
            ]},
            {"paper":"Paper-II","fully_verified":False,"topics":[
                {"topic":"Indian anthropology","subtopics":["Evolution of Indian culture and civilization","Palaeo-anthropology and ethno-archaeology","Demographic profile of India"]},
                {"topic":"Indian social system","subtopics":["Traditional social system and social change","Village studies","Linguistic and religious minorities"]},
                {"topic":"Anthropology in India","subtopics":["Emergence and growth of Anthropology in India"]},
                {"topic":"Tribes in India","subtopics":["Tribal situation","Constitutional safeguards","Social change and ethnicity","Tribal movements","Religion and nation-state","Tribal administration and development"]},
            ]},
        ],
    }
}


def _blank_papers():
    return [
        {"paper":"Paper-I","topics":[],"fully_verified":False},
        {"paper":"Paper-II","topics":[],"fully_verified":False},
    ]


def _paper_complete(paper):
    topics = paper.get("topics") or []
    return bool(paper.get("fully_verified")) and bool(topics) and all(
        isinstance(t, dict) and t.get("topic") and t.get("subtopics") and all(t.get("subtopics"))
        for t in topics
    )


def get_optional_subject(subject: str):
    if subject not in OFFICIAL_OPTIONAL_SUBJECTS:
        return {"subject":subject,"official_subject":False,"source_url":OFFICIAL_NOTIFICATION_SOURCE,
                "pyq_source_url":OFFICIAL_PYQ_SOURCE,"complete":False,"generation_ready":False,"papers":_blank_papers()}
    data = deepcopy(OPTIONAL_DATA.get(subject) or {"source_url":OFFICIAL_NOTIFICATION_SOURCE,"complete":False,"papers":_blank_papers()})
    data.update(subject=subject, official_subject=True, pyq_source_url=OFFICIAL_PYQ_SOURCE)
    papers = data.get("papers") or []
    by_name = {p.get("paper"):p for p in papers}
    normalized = [by_name.get("Paper-I", _blank_papers()[0]), by_name.get("Paper-II", _blank_papers()[1])]
    data["papers"] = normalized
    data["generation_ready"] = bool(data.get("complete")) and all(_paper_complete(p) for p in normalized)
    if not data["generation_ready"]:
        data["complete"] = False
    return data


def optional_topic_is_verified(subject: str, paper: str, topic: str) -> bool:
    data = get_optional_subject(subject)
    if not data["generation_ready"]:
        return False
    for p in data["papers"]:
        if p["paper"] != paper:
            continue
        for item in p["topics"]:
            if item["topic"] == topic or topic in item["subtopics"]:
                return True
    return False


def optional_coverage(subjects=None):
    subjects = list(subjects or OFFICIAL_OPTIONAL_SUBJECTS)
    ready, partial, empty = [], [], []
    for subject in subjects:
        data = get_optional_subject(subject)
        if data["generation_ready"]:
            ready.append(subject)
        elif any(p.get("topics") for p in data["papers"]):
            partial.append(subject)
        else:
            empty.append(subject)
    return {"total_subjects":len(subjects),"official_non_literature_count":len(NON_LITERATURE_OPTIONALS),
            "official_literature_count":len(LITERATURE_LANGUAGES),"generation_ready_subjects":ready,
            "partial_subjects":partial,"not_loaded_subjects":empty,"generation_ready_count":len(ready),
            "partial_count":len(partial),"not_loaded_count":len(empty),"source_url":OFFICIAL_NOTIFICATION_SOURCE}


def validate_official_optional_registry():
    if len(NON_LITERATURE_OPTIONALS) != 25 or len(LITERATURE_LANGUAGES) != 23:
        raise ValueError("UPSC Optional structural counts are incomplete")
    if len(OFFICIAL_OPTIONAL_SUBJECTS) != 48 or len(set(OFFICIAL_OPTIONAL_SUBJECTS)) != 48:
        raise ValueError("UPSC Optional registry must contain exactly 48 unique choices")
    for subject in OFFICIAL_OPTIONAL_SUBJECTS:
        papers = get_optional_subject(subject)["papers"]
        if tuple(p["paper"] for p in papers) != ("Paper-I","Paper-II"):
            raise ValueError(f"{subject}: Paper-I/Paper-II contract missing")
    return True


validate_official_optional_registry()
