# LinkedIn Launch Draft

## Recommended post after the GitHub repository and screenshots are live

I built **ReproGuard AI v0.1** — an open-source research auditing tool designed to make reproducibility checks more evidence-driven and transparent.

Instead of simply summarizing a paper, ReproGuard extracts verifiable research artifacts and asks practical questions:

- Do the detected DOI references resolve in scholarly metadata sources?
- Is code availability documented?
- Is a referenced GitHub repository still reachable?
- Are data splits, preprocessing, hyperparameters, random seeds, evaluation metrics, hardware, and statistical uncertainty described?
- What evidence supports each automated finding?

The current release combines PDF analysis, Crossref/OpenAlex metadata checks, GitHub repository inspection, an evidence graph, and a transparent **Reproducibility Completeness Index (RCI)**.

A key design decision: **RCI is not a “research quality” or “truth” score.** It measures detected documentation completeness and preserves uncertainty when evidence is missing or cannot be verified.

The project is being developed as both an engineering portfolio project and a research platform. The next stages include a manually annotated `ReproAudit-100` benchmark, hybrid LLM verification, self-reflective audit loops, and ML data-leakage analysis.

**Tech:** Python · Streamlit · PyMuPDF · Crossref · OpenAlex · GitHub REST API · Pydantic · pytest · Docker · GitHub Actions

GitHub: [add repository link after publishing]
Live demo: [add deployment link after publishing]

Feedback and open-source contributions are welcome.

#OpenSource #MachineLearning #Research #Reproducibility #Python #ArtificialIntelligence #SoftwareEngineering #GitHub #ResearchIntegrity #AgenticAI

## Screenshots to attach

1. Main dashboard with an uploaded paper.
2. RCI metrics row.
3. Citation verification table.
4. Reproducibility checklist with evidence.
5. Evidence graph.
6. GitHub repository audit tab.
