# ReproGuard AI

**Evidence-first citation integrity and reproducibility auditing for research papers.**

ReproGuard AI is an open-source research tool that accepts a PDF paper, extracts verifiable research artifacts, checks DOI metadata against scholarly services, inspects referenced GitHub repositories, and produces a transparent **Reproducibility Completeness Index (RCI)** plus an evidence report.

> **Important:** RCI measures detected documentation completeness. It is **not** a score of scientific truth, novelty, quality, ethics, or trustworthiness.

## Why this project exists

Research papers often distribute critical reproducibility information across prose, references, code repositories, dependency files, and external metadata systems. Manual checking is slow and inconsistent. ReproGuard AI turns that process into an auditable pipeline while preserving uncertainty instead of inventing missing evidence.

## v0.1 capabilities

- PDF text extraction with PyMuPDF.
- Research-title heuristic extraction.
- DOI extraction and normalization.
- DOI verification using **Crossref** and **OpenAlex**.
- Cross-source metadata consistency check.
- GitHub repository URL extraction.
- Public GitHub repository health/reproducibility audit.
- Transparent detection of 12 reproducibility documentation signals.
- Reproducibility Completeness Index (RCI).
- Evidence graph.
- Agent trace using **Plan → Act → Observe → Evaluate → Replan** stages.
- JSON and Markdown exports.
- Streamlit dashboard and headless CLI.
- Tests, Docker support, CI workflow, contribution and security guidance.

## Architecture

```text
Research PDF
    |
    v
ParserAgent
    |-- text / title
    |-- DOI identifiers
    |-- GitHub URLs
    v
+----------------------+-----------------------+
|                      |                       |
v                      v                       v
CitationAgent     RepositoryAgent       MethodologyAgent
Crossref          GitHub REST API       Rule-based evidence
OpenAlex          repo signals          detectors
|                      |                       |
+----------------------+-----------------------+
                       |
                       v
                  CriticAgent
                       |
                Preserve uncertainty
                       |
                       v
            RCI + Evidence Graph + Report
```

## Reproducibility signals in v0.1

1. Research objective / hypothesis
2. Dataset or data source
3. Train/validation/test split or cross-validation
4. Preprocessing
5. Model or architecture
6. Hyperparameters
7. Random seed
8. Evaluation metrics
9. Baseline comparison
10. Code availability
11. Hardware/software environment
12. Statistical uncertainty/significance

The current RCI uses equal weighting:

```text
RCI = detected applicable documentation signals / applicable signals x 100
```

Future research versions should benchmark alternative weighting schemes rather than assuming one is superior.

## Quick start

### 1. Create an environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Run the dashboard

```bash
streamlit run streamlit_app.py
```

Open the local URL shown by Streamlit, upload a PDF, and select **Online verification** to check scholarly metadata and public GitHub repositories.

### 4. Try the bundled demonstration paper

Use **Use bundled demo paper** in the dashboard, or run:

```bash
PYTHONPATH=src python -m reproguard.cli examples/sample_research_paper.pdf --offline
```

### 5. Run tests

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check src tests streamlit_app.py
```

## CLI

```bash
PYTHONPATH=src python -m reproguard.cli paper.pdf
```

Offline extraction only:

```bash
PYTHONPATH=src python -m reproguard.cli paper.pdf --offline
```

Optional polite scholarly-metadata identity and GitHub token:

```bash
PYTHONPATH=src python -m reproguard.cli paper.pdf \
  --email you@example.com \
  --github-token YOUR_TOKEN
```

Do not commit tokens to the repository.

## External data sources

ReproGuard v0.1 uses public APIs when online verification is enabled:

- Crossref REST API: https://api.crossref.org/
- OpenAlex API: https://api.openalex.org/
- GitHub REST API: https://api.github.com/

The tool degrades gracefully when a service is unavailable and marks uncertainty instead of fabricating metadata.

## GitHub repository checks

For public repository URLs detected in a paper, v0.1 checks signals such as:

- README
- open-source license
- dependency/environment file
- Docker/Compose configuration
- tests directory
- structured source directory
- GitHub Actions workflow
- archived/live repository status

These signals are indicators of reproducibility readiness, not guarantees that the original experiment can be reproduced.

## Research direction

ReproGuard is intentionally designed as both a software project and a research platform. See [`docs/RESEARCH_PLAN.md`](docs/RESEARCH_PLAN.md) for a publication-oriented roadmap including:

- `ReproAudit-100` benchmark creation
- human annotation protocol
- precision/recall/F1 evaluation
- rule-based vs LLM vs hybrid comparison
- code-level ML leakage detection
- self-reflective agentic auditing experiments

A possible paper direction is:

> **ReproGuard: A Hybrid Agentic Framework for Automated Citation Integrity and Reproducibility Auditing of Machine Learning Research**

## Current limitations

- PDF extraction quality depends on document structure and embedded text.
- Scanned/image-only PDFs require a future OCR/vision pathway.
- DOI presence does not guarantee that all citations in a paper contain DOIs.
- Rule-based signal detection can miss evidence expressed with unusual language.
- Repository checks inspect reproducibility signals; they do not execute untrusted external code.
- Automated results require human verification.
- Retraction status is not asserted by v0.1 unless future versions add a dedicated validated source and evaluation protocol.

## Safety and research integrity

ReproGuard should not be used to publicly accuse authors or journals of misconduct. A missing signal can mean the information is genuinely absent, phrased differently, located in a figure/supplement, or unavailable to the parser. Treat every automated result as an auditable lead for human review.

## Open source

Licensed under the MIT License. Contributions are welcome; see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Windows one-click desktop setup

For a non-command-line workflow on Windows:

1. Extract the project to a permanent folder, for example `C:\ReproGuardAI`.
2. Double-click **`setup_windows.bat`** once.
3. The installer creates a private `.venv`, installs the required Python packages, performs a quick import check, and creates a **ReproGuard AI** desktop shortcut.
4. From then on, double-click the **ReproGuard AI** desktop icon. It starts the local Streamlit service silently and opens `http://127.0.0.1:8501` in the default browser.
5. Use **`stop_reproguard.bat`** if you want to stop the local service explicitly.

The desktop shortcut targets the project's own virtual environment, so moving the project folder after setup can break the shortcut. If you move it, run `setup_windows.bat` again to recreate the shortcut.

Launcher diagnostics are written to `logs/reproguard_launcher.log`.
