# ReproGuard AI Research Plan

## Proposed research title

**ReproGuard: A Hybrid Agentic Framework for Automated Citation Integrity and Reproducibility Auditing of Machine Learning Research**

## Research objective

Evaluate whether an evidence-first automated system can reliably identify citation-verification outcomes and reproducibility documentation signals in machine-learning research papers while preserving uncertainty and minimizing unsupported judgments.

## Research questions

- **RQ1:** How accurately can automated DOI extraction and metadata resolution identify verifiable scholarly references?
- **RQ2:** How accurately can ReproGuard detect explicit reproducibility information in research papers?
- **RQ3:** Does a hybrid rule-based + LLM verifier outperform either approach used alone?
- **RQ4:** Does a critic/replan loop reduce unsupported audit findings?
- **RQ5:** Which reproducibility signals are most frequently missing or difficult to extract?
- **RQ6:** How strongly do repository reproducibility signals correspond to successful manual reproduction attempts?
- **RQ7:** Can static code analysis identify common ML data-leakage patterns with useful precision and recall?

## Benchmark: ReproAudit-100

Create a benchmark of 100 openly accessible ML/AI papers with manual labels for:

- DOI validity/resolution
- code availability
- repository availability
- dataset/data-source description
- data splitting/cross-validation
- preprocessing
- model/architecture
- hyperparameters
- random seed
- evaluation metrics
- baselines/ablation
- hardware/software environment
- statistical uncertainty/significance
- dependency specification
- license
- tests/CI signals

### Annotation protocol

1. Two annotators independently label each item as `present`, `absent`, or `unclear`.
2. Record supporting page/section evidence.
3. Resolve disagreements through adjudication.
4. Report inter-annotator agreement before evaluating ReproGuard.
5. Keep the benchmark versioned and document inclusion/exclusion criteria.

## Evaluation metrics

For each binary/multiclass extraction task report:

- precision
- recall
- F1-score
- accuracy where appropriate
- confusion matrix
- false-positive and false-negative analysis
- coverage / abstention rate

For citation metadata consistency, report source agreement and manual adjudication rather than treating one metadata provider as infallible ground truth.

## Experimental conditions

1. Deterministic rule-based baseline (current v0.1).
2. LLM-only extraction.
3. Hybrid rules + LLM.
4. Hybrid + critic verification.
5. Hybrid + critic + replan/fallback.

Record model version, prompt version, temperature, token budget, API cost, latency, and date of experiment.

## Ablation studies

- Remove Crossref fallback.
- Remove OpenAlex fallback.
- Remove critic stage.
- Remove repository evidence.
- Remove evidence snippets.
- Compare equal-weight RCI with empirically justified alternatives.

## ML leakage extension

A later code auditor can identify candidate patterns such as:

- fitting preprocessing on all data before train/test split
- target leakage through derived features
- duplicate rows across train/test
- temporal leakage
- feature selection before cross-validation
- test-set use during model selection

Static detectors must be evaluated on manually reviewed notebooks before being described as reliable leakage detection.

## Publication artifacts

A strong reproducible release should include:

- source code
- benchmark annotations (subject to licenses)
- experiment configuration
- evaluation scripts
- raw aggregate results
- environment/dependency specification
- model/prompt versions
- error analysis
- software release DOI

## Suggested paper structure

1. Introduction
2. Related work
3. Research gap
4. ReproGuard architecture
5. ReproAudit benchmark
6. Experimental methodology
7. Results
8. Error analysis
9. Threats to validity
10. Ethical and responsible-use considerations
11. Limitations
12. Conclusion
