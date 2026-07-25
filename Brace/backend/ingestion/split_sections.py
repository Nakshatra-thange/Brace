import re

SECTION_PATTERNS = {
    "abstract": r"\babstract\b",
    "introduction": r"\bintroduction\b",
    "methods": r"\bmethods?\b|\bmaterials and methods\b",
    "results": r"\bresults?\b",
    "discussion": r"\bdiscussion\b",
    "conclusion": r"\bconclusion\b|\bconclusions\b",
}


def split_sections(text: str):
    lower = text.lower()

    matches = []

    for section, pattern in SECTION_PATTERNS.items():
        match = re.search(pattern, lower)

        if match:
            matches.append((match.start(), section))

    matches.sort()

    sections = {}

    for i, (start, name) in enumerate(matches):
        end = len(text)

        if i + 1 < len(matches):
            end = matches[i + 1][0]

        sections[name] = text[start:end].strip()

    return sections