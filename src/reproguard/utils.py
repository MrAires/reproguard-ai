from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable


DOI_PREFIX = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.I)


def normalize_doi(value: str) -> str:
    value = DOI_PREFIX.sub("", value.strip())
    value = value.strip().rstrip(".,;:)]}>'\"")
    return value.lower()


def unique_preserve(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def normalize_title(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"[^a-z0-9\s]", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def title_similarity(a: str | None, b: str | None) -> float | None:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return None
    return round(SequenceMatcher(None, na, nb).ratio(), 3)


def first_year(value) -> int | None:
    """Extract a year from Crossref/OpenAlex-style date structures."""
    try:
        if isinstance(value, dict):
            parts = value.get("date-parts")
            if parts and parts[0] and parts[0][0]:
                return int(parts[0][0])
        if isinstance(value, str):
            match = re.search(r"\b(19|20)\d{2}\b", value)
            if match:
                return int(match.group(0))
        if isinstance(value, int):
            return value
    except (TypeError, ValueError, IndexError):
        return None
    return None


def snippet(text: str, start: int, end: int, radius: int = 120) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    value = re.sub(r"\s+", " ", text[left:right]).strip()
    return value[:320]
