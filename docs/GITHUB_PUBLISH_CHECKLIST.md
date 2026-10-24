# GitHub Publication Checklist

## Repository identity

**Repository name:** `reproguard-ai`

**Description:**

> Evidence-first citation integrity and reproducibility auditing for research papers.

**Suggested topics:**

`research-reproducibility`, `research-integrity`, `machine-learning`, `open-science`, `python`, `streamlit`, `crossref`, `openalex`, `github-api`, `agentic-ai`, `scientific-computing`

## Before publishing

- Replace generic contributor metadata in `CITATION.cff` with the actual author/contributor names.
- Add the final GitHub repository URL to `CITATION.cff`.
- Run `pytest -q`.
- Run `ruff check src tests streamlit_app.py`.
- Run the bundled demo paper in online mode.
- Test one real open-access research PDF.
- Capture dashboard screenshots.
- Check that no API token, email secret, or private paper was committed.
- Confirm `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, and `.gitignore` are present.

## Suggested first commits

1. `feat: initialize evidence-first PDF audit pipeline`
2. `feat: add Crossref and OpenAlex citation verification`
3. `feat: add GitHub repository reproducibility audit`
4. `feat: add RCI and evidence graph`
5. `test: add parser and scoring regression tests`
6. `docs: add research plan and reproducibility limitations`

If building in one day, one initial commit is acceptable; future development should use focused commits so the repository demonstrates engineering practice.

## First release

Tag: `v0.1.0`

Release title: **ReproGuard AI v0.1.0 — Evidence-First Baseline**

Release notes should mention:

- deterministic baseline
- DOI verification
- GitHub repository audit
- 12-signal RCI
- evidence graph
- Streamlit dashboard
- JSON/Markdown export
- known limitations

## Later: archival DOI

After the repository is stable and public, connect the GitHub repository to Zenodo and archive a tagged release. Add the resulting DOI badge to the README only after Zenodo actually creates it.
