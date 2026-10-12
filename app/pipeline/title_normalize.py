import re
from difflib import SequenceMatcher


def normalize_title(title: str) -> str:
    """Strip noise so titles from different sites become comparable."""
    title = title.lower()
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def dupe_check(new_title: str, existing_titles: list, threshold: float = 0.85) -> bool:
    """Return True if new_title is a near-duplicate of any title in existing_titles."""
    new_normalized = normalize_title(new_title)
    for existing in existing_titles:
        similarity = SequenceMatcher(None, new_normalized, normalize_title(existing)).ratio()
        if similarity >= threshold:
            return True
    return False
