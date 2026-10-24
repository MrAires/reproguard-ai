from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    UNVERIFIED = "unverified"
    ERROR = "error"


class CitationRecord(BaseModel):
    doi: str
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    crossref_title: str | None = None
    openalex_title: str | None = None
    publisher: str | None = None
    year: int | None = None
    type: str | None = None
    metadata_similarity: float | None = None
    issues: list[str] = Field(default_factory=list)
    sources_checked: list[str] = Field(default_factory=list)


class RepositorySignal(BaseModel):
    key: str
    label: str
    detected: bool
    evidence: str | None = None


class RepositoryAudit(BaseModel):
    url: str
    owner: str | None = None
    repo: str | None = None
    exists: bool = False
    archived: bool | None = None
    default_branch: str | None = None
    stars: int | None = None
    forks: int | None = None
    license_name: str | None = None
    last_pushed_at: str | None = None
    signals: list[RepositorySignal] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class ReproducibilityItem(BaseModel):
    key: str
    label: str
    description: str
    applicable: bool = True
    detected: bool = False
    evidence: str | None = None


class AgentTraceEvent(BaseModel):
    stage: str
    agent: str
    message: str


class EvidenceNode(BaseModel):
    id: str
    label: str
    kind: str


class EvidenceEdge(BaseModel):
    source: str
    target: str
    label: str


class AuditReport(BaseModel):
    schema_version: str = "1.0"
    reproguard_version: str = "0.1.0"
    file_name: str
    extracted_title: str | None = None
    page_count: int = 0
    character_count: int = 0
    doi_count: int = 0
    github_url_count: int = 0
    citations: list[CitationRecord] = Field(default_factory=list)
    repositories: list[RepositoryAudit] = Field(default_factory=list)
    reproducibility_items: list[ReproducibilityItem] = Field(default_factory=list)
    rci_score: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    evidence_nodes: list[EvidenceNode] = Field(default_factory=list)
    evidence_edges: list[EvidenceEdge] = Field(default_factory=list)
    trace: list[AgentTraceEvent] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
