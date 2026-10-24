from pathlib import Path

from reproguard.agents import AuditOrchestrator


def test_offline_audit_runs_end_to_end():
    pdf = Path("examples/sample_research_paper.pdf").read_bytes()
    report = AuditOrchestrator(online=False).audit_pdf(pdf, "sample_research_paper.pdf")
    assert report.page_count == 2
    assert report.doi_count == 2
    assert report.github_url_count == 1
    assert report.rci_score >= 80
    assert len(report.trace) >= 5
    assert report.metadata["online_verification"] is False
