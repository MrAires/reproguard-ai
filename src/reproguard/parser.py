from __future__ import annotations

import re
from dataclasses import dataclass

import fitz  # PyMuPDF

from .utils import normalize_doi, unique_preserve


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
GITHUB_RE = re.compile(
    r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?",
    re.I,
)


@dataclass
class ParsedPaper:
    text: str
    page_count: int
    title: str | None
    dois: list[str]
    github_urls: list[str]
    reference_block: str


def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, list[str]]:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages = [page.get_text("text") for page in doc]
    return "\n\n".join(pages), pages


def extract_title(first_page_text: str) -> str | None:
    lines = [re.sub(r"\s+", " ", line).strip() for line in first_page_text.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return None

    stop = len(lines)
    for idx, line in enumerate(lines[:40]):
        if re.match(r"^(abstract|introduction|keywords?)\b", line, re.I):
            stop = idx
            break

    candidates: list[tuple[float, str]] = []
    for idx, line in enumerate(lines[:stop][:20]):
        words = line.split()
        if len(words) < 4 or len(words) > 28:
            continue
        if len(line) < 24 or len(line) > 220:
            continue
        if re.search(r"@|doi\b|https?://|university|department|institute|volume|issue|journal", line, re.I):
            continue
        alpha_ratio = sum(ch.isalpha() for ch in line) / max(1, len(line))
        if alpha_ratio < 0.55:
            continue
        length_score = 1 - min(abs(len(line) - 95) / 120, 1)
        position_score = 1 - min(idx / 20, 1)
        title_case_bonus = 0.15 if line[:1].isupper() else 0
        candidates.append((length_score + position_score + title_case_bonus, line))

    if not candidates:
        return lines[0][:220]
    return max(candidates, key=lambda item: item[0])[1]


def extract_dois(text: str) -> list[str]:
    matches = []
    for match in DOI_RE.finditer(text):
        doi = normalize_doi(match.group(0))
        if doi:
            matches.append(doi)
    return unique_preserve(matches)


def extract_github_urls(text: str) -> list[str]:
    urls = []
    for match in GITHUB_RE.finditer(text):
        url = match.group(0).rstrip(".,;:)]}>'\"")
        if url.endswith(".git"):
            url = url[:-4]
        urls.append(url)
    return unique_preserve(urls)


def extract_reference_block(text: str) -> str:
    matches = list(re.finditer(r"(?im)^\s*(references|bibliography)\s*$", text))
    if not matches:
        return ""
    start = matches[-1].end()
    tail = text[start:]
    # Avoid accidentally swallowing appendices when a clear new major section appears.
    end_match = re.search(r"(?im)^\s*(appendix|acknowledg(?:e)?ments?|author contributions)\s*$", tail)
    if end_match:
        tail = tail[: end_match.start()]
    return tail.strip()


def parse_pdf(pdf_bytes: bytes) -> ParsedPaper:
    text, pages = extract_pdf_text(pdf_bytes)
    first_page = pages[0] if pages else ""
    return ParsedPaper(
        text=text,
        page_count=len(pages),
        title=extract_title(first_page),
        dois=extract_dois(text),
        github_urls=extract_github_urls(text),
        reference_block=extract_reference_block(text),
    )
