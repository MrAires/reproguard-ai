from __future__ import annotations

import json

from .models import AuditReport


def report_to_json(report: AuditReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False)


def report_to_markdown(report: AuditReport) -> str:
    verified = sum(1 for c in report.citations if c.status.value == "verified")
    lines = [
        "# ReproGuard AI Audit Report",
        "",
        f"**File:** {report.file_name}",
        f"**Extracted title:** {report.extracted_title or 'Not confidently detected'}",
        f"**Pages:** {report.page_count}",
        f"**Reproducibility Completeness Index (RCI):** {report.rci_score:.1f}/100",
        "",
        "> RCI measures detected documentation completeness only. It is not a score of scientific truth, quality, novelty, or trustworthiness.",
        "",
        "## Summary",
        "",
        f"- DOI identifiers detected: {report.doi_count}",
        f"- DOI identifiers verified in both metadata sources: {verified}",
        f"- GitHub URLs detected: {report.github_url_count}",
        f"- Public repositories reached: {sum(1 for r in report.repositories if r.exists)}",
        "",
        "## Reproducibility checklist",
        "",
        "| Signal | Detected | Evidence |",
        "|---|:---:|---|",
    ]
    for item in report.reproducibility_items:
        evidence = (item.evidence or "—").replace("|", "\\|")
        lines.append(f"| {item.label} | {'Yes' if item.detected else 'No'} | {evidence} |")

    lines.extend(["", "## Citation verification", ""])
    if not report.citations:
        lines.append("No DOI identifiers were detected.")
    else:
        lines.extend(["| DOI | Status | Metadata title | Issues |", "|---|---|---|---|"])
        for citation in report.citations:
            title = citation.crossref_title or citation.openalex_title or "—"
            issues = "; ".join(citation.issues) or "—"
            lines.append(f"| {citation.doi} | {citation.status.value} | {title.replace('|', '\\|')} | {issues.replace('|', '\\|')} |")

    lines.extend(["", "## Repository audit", ""])
    if not report.repositories:
        lines.append("No GitHub repository URLs were detected.")
    else:
        for repo in report.repositories:
            lines.append(f"### {repo.owner or '?'} / {repo.repo or '?'}")
            lines.append(f"- URL: {repo.url}")
            lines.append(f"- Publicly reachable: {'Yes' if repo.exists else 'No'}")
            if repo.exists:
                lines.append(f"- License: {repo.license_name or 'Not detected'}")
                for signal in repo.signals:
                    lines.append(f"- {'✓' if signal.detected else '✗'} {signal.label}")
            for issue in repo.issues:
                lines.append(f"- Caution: {issue}")
            lines.append("")

    lines.extend(["## Strengths", ""])
    lines.extend([f"- {item}" for item in report.strengths] or ["- No strengths were automatically asserted."])
    lines.extend(["", "## Cautions", ""])
    lines.extend([f"- {item}" for item in report.warnings])

    lines.extend(["", "## Audit trace", ""])
    for event in report.trace:
        lines.append(f"- **{event.stage} · {event.agent}:** {event.message}")

    return "\n".join(lines) + "\n"
