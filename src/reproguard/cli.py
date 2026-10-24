from __future__ import annotations

import argparse
from pathlib import Path

from .agents import AuditOrchestrator
from .reports import report_to_json, report_to_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit a research PDF with ReproGuard AI.")
    parser.add_argument("pdf", type=Path, help="Path to a PDF paper")
    parser.add_argument("--offline", action="store_true", help="Extract evidence without calling external APIs")
    parser.add_argument("--email", default=None, help="Contact email for polite Crossref/OpenAlex API use")
    parser.add_argument("--github-token", default=None, help="Optional GitHub token for higher API limits")
    parser.add_argument("--json", type=Path, default=None, help="Write JSON report to this path")
    parser.add_argument("--markdown", type=Path, default=None, help="Write Markdown report to this path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pdf_bytes = args.pdf.read_bytes()
    auditor = AuditOrchestrator(
        contact_email=args.email,
        github_token=args.github_token,
        online=not args.offline,
    )
    report = auditor.audit_pdf(pdf_bytes, args.pdf.name)
    json_text = report_to_json(report)
    md_text = report_to_markdown(report)

    json_path = args.json or args.pdf.with_suffix(".reproguard.json")
    md_path = args.markdown or args.pdf.with_suffix(".reproguard.md")
    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    print(f"RCI: {report.rci_score:.1f}/100")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")


if __name__ == "__main__":
    main()
