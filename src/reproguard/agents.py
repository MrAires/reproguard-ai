from __future__ import annotations

from datetime import datetime, timezone

from . import __version__
from .clients import CrossrefClient, GitHubClient, OpenAlexClient, verify_doi
from .models import (
    AgentTraceEvent,
    AuditReport,
    EvidenceEdge,
    EvidenceNode,
    VerificationStatus,
)
from .parser import parse_pdf
from .reproducibility import assess_reproducibility, calculate_rci


class AuditOrchestrator:
    """Deterministic multi-agent-style audit pipeline.

    The current v0.1 agents are evidence extractors/verifiers rather than autonomous
    LLMs. This keeps the baseline auditable, cheap, and reproducible. LLM-based
    reasoning can be added later as an optional layer and benchmarked against this
    deterministic baseline.
    """

    def __init__(
        self,
        contact_email: str | None = None,
        github_token: str | None = None,
        online: bool = True,
    ):
        self.contact_email = contact_email or None
        self.github_token = github_token or None
        self.online = online
        self.crossref = CrossrefClient(self.contact_email)
        self.openalex = OpenAlexClient(self.contact_email)
        self.github = GitHubClient(self.github_token)
        self.trace: list[AgentTraceEvent] = []

    def _trace(self, stage: str, agent: str, message: str) -> None:
        self.trace.append(AgentTraceEvent(stage=stage, agent=agent, message=message))

    def audit_pdf(self, pdf_bytes: bytes, file_name: str) -> AuditReport:
        self.trace = []
        self._trace("PLAN", "Orchestrator", "Parse document, verify scholarly identifiers, inspect repositories, assess reproducibility evidence, then critique the result.")

        self._trace("ACT", "ParserAgent", "Extracting PDF text, title, DOI identifiers, GitHub URLs, and references section.")
        parsed = parse_pdf(pdf_bytes)
        self._trace("OBSERVE", "ParserAgent", f"Extracted {parsed.page_count} pages, {len(parsed.dois)} unique DOI(s), and {len(parsed.github_urls)} GitHub URL(s).")

        citations = []
        if parsed.dois:
            if self.online:
                self._trace("ACT", "CitationAgent", "Resolving DOI metadata against Crossref and OpenAlex.")
                for doi in parsed.dois:
                    citations.append(verify_doi(doi, self.crossref, self.openalex))
                verified = sum(1 for item in citations if item.status == VerificationStatus.VERIFIED)
                self._trace("EVALUATE", "CitationAgent", f"Verified {verified}/{len(citations)} DOI(s) in both metadata sources where available.")
                if any(item.status in {VerificationStatus.ERROR, VerificationStatus.UNVERIFIED} for item in citations):
                    self._trace("REPLAN", "CitationAgent", "Some identifiers could not be fully verified; preserving uncertainty rather than inferring metadata.")
            else:
                self._trace("OBSERVE", "CitationAgent", "Online verification disabled; DOI identifiers are extracted but not resolved.")
                from .models import CitationRecord
                citations = [CitationRecord(doi=doi) for doi in parsed.dois]

        repositories = []
        if parsed.github_urls:
            if self.online:
                self._trace("ACT", "RepositoryAgent", "Inspecting public GitHub repository metadata and root-level reproducibility signals.")
                repositories = [self.github.audit_repository(url) for url in parsed.github_urls]
                live = sum(1 for repo in repositories if repo.exists)
                self._trace("EVALUATE", "RepositoryAgent", f"Reached {live}/{len(repositories)} referenced repository/repositories.")
            else:
                from .clients import parse_github_repo
                from .models import RepositoryAudit
                for url in parsed.github_urls:
                    owner, repo = parse_github_repo(url)
                    repositories.append(RepositoryAudit(url=url, owner=owner, repo=repo))
                self._trace("OBSERVE", "RepositoryAgent", "Online repository audit disabled; repository URLs were extracted only.")

        self._trace("ACT", "MethodologyAgent", "Scanning the paper for explicit reproducibility evidence using transparent rule-based detectors.")
        repro_items = assess_reproducibility(parsed.text)
        rci = calculate_rci(repro_items)
        self._trace("EVALUATE", "MethodologyAgent", f"Reproducibility Completeness Index (RCI): {rci:.1f}/100 based on documented evidence items.")

        warnings, strengths = self._critique(parsed, citations, repositories, repro_items, rci)
        self._trace("EVALUATE", "CriticAgent", f"Generated {len(warnings)} caution(s) and {len(strengths)} documented strength(s).")

        nodes, edges = self._build_evidence_graph(parsed, citations, repositories, repro_items)
        report = AuditReport(
            reproguard_version=__version__,
            file_name=file_name,
            extracted_title=parsed.title,
            page_count=parsed.page_count,
            character_count=len(parsed.text),
            doi_count=len(parsed.dois),
            github_url_count=len(parsed.github_urls),
            citations=citations,
            repositories=repositories,
            reproducibility_items=repro_items,
            rci_score=rci,
            warnings=warnings,
            strengths=strengths,
            evidence_nodes=nodes,
            evidence_edges=edges,
            trace=self.trace,
            metadata={
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "online_verification": self.online,
                "rci_definition": "Percentage of applicable reproducibility documentation signals detected. It is not a truth, quality, novelty, or trustworthiness score.",
            },
        )
        return report

    def _critique(self, parsed, citations, repositories, items, rci):
        warnings: list[str] = []
        strengths: list[str] = []
        item_map = {item.key: item for item in items}

        for key, message in {
            "dataset": "Dataset or data source was not clearly detected.",
            "split": "Train/validation/test split or cross-validation was not clearly detected.",
            "hyperparameters": "Hyperparameter/training configuration was not clearly detected.",
            "seed": "Random seed or randomness-control statement was not clearly detected.",
            "metrics": "Evaluation metrics were not clearly detected.",
            "hardware": "Hardware/software execution environment was not clearly detected.",
            "statistics": "No clear statistical uncertainty/significance evidence was detected.",
        }.items():
            if key in item_map and not item_map[key].detected:
                warnings.append(message)

        if not parsed.dois:
            warnings.append("No DOI identifiers were detected; citation integrity coverage is therefore limited.")
        elif citations and all(c.status in {VerificationStatus.VERIFIED, VerificationStatus.PARTIAL} for c in citations):
            strengths.append("Detected DOI identifiers resolved in at least one scholarly metadata source.")

        if parsed.github_urls:
            if repositories and any(repo.exists for repo in repositories):
                strengths.append("At least one referenced GitHub repository is publicly reachable.")
            if repositories and any(any(sig.key == "license" and sig.detected for sig in repo.signals) for repo in repositories):
                strengths.append("At least one referenced repository exposes an open-source license signal.")
        else:
            warnings.append("No GitHub repository URL was detected in the paper text.")

        if rci >= 75:
            strengths.append("The paper documents most baseline reproducibility signals checked by ReproGuard v0.1.")
        elif rci < 50:
            warnings.append("Fewer than half of the baseline reproducibility documentation signals were detected.")

        warnings.append("Automated findings require human review; absence of a detected signal does not prove the information is absent from figures, supplements, external repositories, or non-standard wording.")
        return warnings, strengths

    def _build_evidence_graph(self, parsed, citations, repositories, items):
        nodes = [EvidenceNode(id="paper", label=parsed.title or "Uploaded paper", kind="paper")]
        edges: list[EvidenceEdge] = []

        for idx, citation in enumerate(citations[:25]):
            node_id = f"doi_{idx}"
            label = citation.crossref_title or citation.openalex_title or citation.doi
            nodes.append(EvidenceNode(id=node_id, label=label[:90], kind="citation"))
            edges.append(EvidenceEdge(source="paper", target=node_id, label=citation.status.value))

        for idx, repo in enumerate(repositories[:10]):
            node_id = f"repo_{idx}"
            label = f"{repo.owner}/{repo.repo}" if repo.owner and repo.repo else repo.url
            nodes.append(EvidenceNode(id=node_id, label=label, kind="repository"))
            edges.append(EvidenceEdge(source="paper", target=node_id, label="references code"))

        for item in items:
            if item.detected:
                node_id = f"signal_{item.key}"
                nodes.append(EvidenceNode(id=node_id, label=item.label, kind="reproducibility"))
                edges.append(EvidenceEdge(source="paper", target=node_id, label="documents"))
        return nodes, edges
