from __future__ import annotations

from urllib.parse import quote, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import CitationRecord, RepositoryAudit, RepositorySignal, VerificationStatus
from .utils import first_year, normalize_doi, title_similarity


def build_session(user_agent: str = "ReproGuardAI/0.1") -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.35,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
    return session


class CrossrefClient:
    BASE = "https://api.crossref.org"

    def __init__(self, email: str | None = None, session: requests.Session | None = None):
        agent = "ReproGuardAI/0.1"
        if email:
            agent += f" (mailto:{email})"
        self.session = session or build_session(agent)
        self.email = email

    def get_work(self, doi: str) -> dict | None:
        doi = normalize_doi(doi)
        params = {"mailto": self.email} if self.email else None
        url = f"{self.BASE}/works/{quote(doi, safe='')}"
        response = self.session.get(url, params=params, timeout=12)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        return payload.get("message") or None


class OpenAlexClient:
    BASE = "https://api.openalex.org"

    def __init__(self, email: str | None = None, session: requests.Session | None = None):
        self.session = session or build_session("ReproGuardAI/0.1")
        self.email = email

    def get_work_by_doi(self, doi: str) -> dict | None:
        doi = normalize_doi(doi)
        params = {"filter": f"doi:https://doi.org/{doi}", "per-page": 1}
        if self.email:
            params["mailto"] = self.email
        response = self.session.get(f"{self.BASE}/works", params=params, timeout=12)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        return results[0] if results else None


def verify_doi(
    doi: str,
    crossref: CrossrefClient,
    openalex: OpenAlexClient,
) -> CitationRecord:
    record = CitationRecord(doi=normalize_doi(doi))
    crossref_data: dict | None = None
    openalex_data: dict | None = None

    try:
        crossref_data = crossref.get_work(record.doi)
        record.sources_checked.append("Crossref")
    except requests.RequestException as exc:
        record.issues.append(f"Crossref request failed: {exc.__class__.__name__}")

    try:
        openalex_data = openalex.get_work_by_doi(record.doi)
        record.sources_checked.append("OpenAlex")
    except requests.RequestException as exc:
        record.issues.append(f"OpenAlex request failed: {exc.__class__.__name__}")

    if crossref_data:
        titles = crossref_data.get("title") or []
        record.crossref_title = titles[0] if titles else None
        record.publisher = crossref_data.get("publisher")
        record.type = crossref_data.get("type")
        record.year = (
            first_year(crossref_data.get("published-print"))
            or first_year(crossref_data.get("published-online"))
            or first_year(crossref_data.get("issued"))
        )

    if openalex_data:
        record.openalex_title = openalex_data.get("title") or openalex_data.get("display_name")
        if record.year is None:
            record.year = openalex_data.get("publication_year")
        if record.type is None:
            record.type = openalex_data.get("type")

    if crossref_data and openalex_data:
        record.metadata_similarity = title_similarity(record.crossref_title, record.openalex_title)
        if record.metadata_similarity is not None and record.metadata_similarity < 0.72:
            record.status = VerificationStatus.PARTIAL
            record.issues.append("Crossref/OpenAlex title metadata disagree materially.")
        else:
            record.status = VerificationStatus.VERIFIED
    elif crossref_data or openalex_data:
        record.status = VerificationStatus.PARTIAL
        record.issues.append("DOI resolved in only one metadata source.")
    elif record.issues:
        record.status = VerificationStatus.ERROR
    else:
        record.status = VerificationStatus.UNVERIFIED
        record.issues.append("DOI did not resolve in Crossref or OpenAlex.")

    return record


def parse_github_repo(url: str) -> tuple[str | None, str | None]:
    parsed = urlparse(url)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None, None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None, None
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.session = session or build_session("ReproGuardAI/0.1")
        self.session.headers.update({"X-GitHub-Api-Version": "2022-11-28"})
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _get(self, path: str):
        return self.session.get(f"{self.BASE}{path}", timeout=12)

    def _list_dir(self, owner: str, repo: str, path: str = "") -> list[dict]:
        suffix = f"/{quote(path, safe='/')}" if path else ""
        response = self._get(f"/repos/{owner}/{repo}/contents{suffix}")
        if response.status_code == 404:
            return []
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else [payload]

    def audit_repository(self, url: str) -> RepositoryAudit:
        owner, repo = parse_github_repo(url)
        audit = RepositoryAudit(url=url, owner=owner, repo=repo)
        if not owner or not repo:
            audit.issues.append("Unsupported GitHub repository URL.")
            return audit

        try:
            response = self._get(f"/repos/{owner}/{repo}")
            if response.status_code == 404:
                audit.issues.append("Repository not found or not publicly accessible.")
                return audit
            response.raise_for_status()
            meta = response.json()
            audit.exists = True
            audit.archived = meta.get("archived")
            audit.default_branch = meta.get("default_branch")
            audit.stars = meta.get("stargazers_count")
            audit.forks = meta.get("forks_count")
            audit.last_pushed_at = meta.get("pushed_at")
            license_info = meta.get("license") or {}
            audit.license_name = license_info.get("spdx_id") or license_info.get("name")

            root = self._list_dir(owner, repo)
            names = {entry.get("name", "").lower(): entry for entry in root}
            root_names = set(names)

            signals = [
                ("readme", "README", any(name.startswith("readme") for name in root_names), "README documentation"),
                ("license", "License", any(name.startswith("license") or name.startswith("copying") for name in root_names), audit.license_name or "License file"),
                ("dependencies", "Dependency specification", bool({"requirements.txt", "pyproject.toml", "environment.yml", "environment.yaml", "poetry.lock", "pipfile"} & root_names), "Dependency/environment file"),
                ("container", "Container configuration", "dockerfile" in root_names or "docker-compose.yml" in root_names or "compose.yml" in root_names, "Docker/Compose configuration"),
                ("tests", "Test directory", "tests" in root_names or "test" in root_names, "tests/ directory"),
                ("src_layout", "Source layout", "src" in root_names or any(name in root_names for name in {"app", "package", "packages"}), "Structured source directory"),
            ]

            ci_detected = False
            if ".github" in root_names:
                try:
                    workflows = self._list_dir(owner, repo, ".github/workflows")
                    ci_detected = bool(workflows)
                except requests.RequestException:
                    pass
            signals.append(("ci", "CI workflow", ci_detected, ".github/workflows" if ci_detected else None))

            audit.signals = [
                RepositorySignal(key=key, label=label, detected=detected, evidence=evidence if detected else None)
                for key, label, detected, evidence in signals
            ]
            if audit.archived:
                audit.issues.append("Repository is archived.")
            if not any(signal.key == "license" and signal.detected for signal in audit.signals):
                audit.issues.append("No obvious open-source license detected at repository root.")
            if not any(signal.key == "dependencies" and signal.detected for signal in audit.signals):
                audit.issues.append("No common dependency/environment file detected.")
        except requests.RequestException as exc:
            audit.issues.append(f"GitHub API request failed: {exc.__class__.__name__}")
        return audit
