# ReproGuard AI Audit Report

**File:** sample_research_paper.pdf
**Extracted title:** Reproducible Benchmarking of Tree Ensembles on Tabular Data
**Pages:** 2
**Reproducibility Completeness Index (RCI):** 100.0/100

> RCI measures detected documentation completeness only. It is not a score of scientific truth, quality, novelty, or trustworthiness.

## Summary

- DOI identifiers detected: 2
- DOI identifiers verified in both metadata sources: 0
- GitHub URLs detected: 1
- Public repositories reached: 0

## Reproducibility checklist

| Signal | Detected | Evidence |
|---|:---:|---|
| Research objective | Yes | ular classification. We use a public benchmark dataset and compare a Random Forest baseline with Gradient Boosting. The objective is to document enough experimental detail for an independent researcher to repeat the analysis. 1. Dataset and preproce |
| Dataset / data source | Yes | Abstract This study evaluates reproducible benchmarking practices for tabular classification. We use a public benchmark dataset and compare a Random Forest baseline with Gradient Boosting. The objective is to document enough experimental detail fo |
| Train/validation/test split | Yes | beled samples and 20 features. Missing values are imputed using the median. Numeric features are standardized after the train/test split. We use a stratified 80/20 training/test split and five-fold cross-validation on the training set. 2. Models and |
| Preprocessing | Yes | bjective is to document enough experimental detail for an independent researcher to repeat the analysis. 1. Dataset and preprocessing The dataset contains 1,000 labeled samples and 20 features. Missing values are imputed using the median. Numeric fea |
| Model / architecture | Yes | aluates reproducible benchmarking practices for tabular classification. We use a public benchmark dataset and compare a Random Forest baseline with Gradient Boosting. The objective is to document enough experimental detail for an independent researcher |
| Hyperparameters | Yes | split. We use a stratified 80/20 training/test split and five-fold cross-validation on the training set. 2. Models and hyperparameters The Random Forest uses n_estimators=200, max_depth=12, and random_state=42. The Gradient Boosting model uses 150 estim |
| Random seed | Yes | th=12, and random_state=42. The Gradient Boosting model uses 150 estimators and learning rate=0.05. All experiments use random seed 42. 3. Evaluation We report accuracy, precision, recall, F1-score, and ROC-AUC. Results are compared with the Random Fo |
| Evaluation metrics | Yes | Boosting model uses 150 estimators and learning rate=0.05. All experiments use random seed 42. 3. Evaluation We report accuracy, precision, recall, F1-score, and ROC-AUC. Results are compared with the Random Forest baseline. Each configuration is |
| Baseline comparison | Yes | ucible benchmarking practices for tabular classification. We use a public benchmark dataset and compare a Random Forest baseline with Gradient Boosting. The objective is to document enough experimental detail for an independent researcher to repeat |
| Code availability | Yes | n with 16 GB RAM. The reference implementation uses scikit-learn. A public software repository is referenced at https://github.com/scikit-learn/scikit-learn . 5. Limitations This demonstration is intentionally small and is not intended to establish a |
| Hardware / environment | Yes | e report mean and standard deviation. 4. Environment and code availability Experiments were run with Python 3.12 on a CPU workstation with 16 GB RAM. The reference implementation uses scikit-learn. A public software repository is referenced |
| Statistical uncertainty / significance | Yes | compared with the Random Forest baseline. Each configuration is evaluated in five repeated runs and we report mean and standard deviation. 4. Environment and code availability Experiments were run with Python 3.12 on a CPU workstation with 16 GB RAM. The |

## Citation verification

| DOI | Status | Metadata title | Issues |
|---|---|---|---|
| 10.1023/a:1010933404324 | unverified | — | — |
| 10.1145/2939672.2939785 | unverified | — | — |

## Repository audit

### scikit-learn / scikit-learn
- URL: https://github.com/scikit-learn/scikit-learn
- Publicly reachable: No

## Strengths

- The paper documents most baseline reproducibility signals checked by ReproGuard v0.1.

## Cautions

- Automated findings require human review; absence of a detected signal does not prove the information is absent from figures, supplements, external repositories, or non-standard wording.

## Audit trace

- **PLAN · Orchestrator:** Parse document, verify scholarly identifiers, inspect repositories, assess reproducibility evidence, then critique the result.
- **ACT · ParserAgent:** Extracting PDF text, title, DOI identifiers, GitHub URLs, and references section.
- **OBSERVE · ParserAgent:** Extracted 2 pages, 2 unique DOI(s), and 1 GitHub URL(s).
- **OBSERVE · CitationAgent:** Online verification disabled; DOI identifiers are extracted but not resolved.
- **OBSERVE · RepositoryAgent:** Online repository audit disabled; repository URLs were extracted only.
- **ACT · MethodologyAgent:** Scanning the paper for explicit reproducibility evidence using transparent rule-based detectors.
- **EVALUATE · MethodologyAgent:** Reproducibility Completeness Index (RCI): 100.0/100 based on documented evidence items.
- **EVALUATE · CriticAgent:** Generated 1 caution(s) and 1 documented strength(s).
