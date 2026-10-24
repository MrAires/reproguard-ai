from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ReproducibilityItem
from .utils import snippet


@dataclass(frozen=True)
class SignalRule:
    key: str
    label: str
    description: str
    patterns: tuple[str, ...]


RULES: tuple[SignalRule, ...] = (
    SignalRule("problem", "Research objective", "A concrete task, objective, hypothesis, or research question is described.", (r"\bresearch question\b", r"\bobjective\b", r"\bwe (?:aim|investigate|evaluate|study|propose)\b", r"\bhypothes(?:is|es)\b")),
    SignalRule("dataset", "Dataset / data source", "The dataset or data source is identified or described.", (r"\bdataset\b", r"\bdata set\b", r"\bdata (?:were|was) (?:collected|obtained|downloaded|sourced)\b", r"\bbenchmark data\b")),
    SignalRule("split", "Train/validation/test split", "Data partitioning or cross-validation is documented.", (r"train(?:ing)?\s*[/,-]\s*(?:validation\s*[/,-]\s*)?test", r"\btrain(?:ing)? set\b", r"\btest set\b", r"\bk[- ]?fold cross[- ]?validation\b", r"\bcross[- ]?validation\b")),
    SignalRule("preprocessing", "Preprocessing", "Data cleaning, normalization, tokenization, augmentation, or feature preprocessing is documented.", (r"\bpreprocess", r"\bnormaliz", r"\bstandardiz", r"\btokeniz", r"\bdata augmentation\b", r"\bmissing values?\b")),
    SignalRule("model", "Model / architecture", "The model, algorithm, or architecture is identified.", (r"\bmodel architecture\b", r"\barchitecture\b", r"\brandom forest\b", r"\bgradient boost", r"\bneural network\b", r"\btransformer\b", r"\blogistic regression\b", r"\bsupport vector")),
    SignalRule("hyperparameters", "Hyperparameters", "Hyperparameters or training configuration are reported.", (r"\bhyperparameter", r"\blearning rate\b", r"\bbatch size\b", r"\bepochs?\b", r"\bmax_depth\b", r"\bn_estimators\b", r"\bweight decay\b")),
    SignalRule("seed", "Random seed", "Randomness control or deterministic seed is reported.", (r"\brandom seed\b", r"\brandom_state\b", r"\bseed\s*[=:]\s*\d+", r"\bseed of\s+\d+")),
    SignalRule("metrics", "Evaluation metrics", "Quantitative evaluation metrics are identified.", (r"\baccuracy\b", r"\bprecision\b", r"\brecall\b", r"\bf1[- ]?score\b", r"\broc[- ]?auc\b", r"\brmse\b", r"\bmae\b", r"\bbleu\b", r"\bperplexity\b")),
    SignalRule("baselines", "Baseline comparison", "A baseline, comparator, ablation, or prior method comparison is described.", (r"\bbaseline\b", r"\bcompared with\b", r"\bcomparison with\b", r"\bablation\b", r"\bstate[- ]of[- ]the[- ]art\b")),
    SignalRule("code", "Code availability", "Source code, implementation repository, or code availability is mentioned.", (r"github\.com/", r"\bsource code\b", r"\bcode is (?:available|released)\b", r"\bimplementation is available\b")),
    SignalRule("hardware", "Hardware / environment", "Compute hardware or software environment is described.", (r"\bgpu\b", r"\bcuda\b", r"\bnvidia\b", r"\btpu\b", r"\bcpu\b", r"\bpython\s*\d", r"\bpytorch\b", r"\btensorflow\b")),
    SignalRule("statistics", "Statistical uncertainty / significance", "Confidence intervals, significance tests, standard deviation, or repeated runs are reported.", (r"\bconfidence interval\b", r"\bp[- ]?value\b", r"\bstatistical(?:ly)? significant\b", r"\bstandard deviation\b", r"\bmean\s*[±+/-]", r"\brepeated runs?\b")),
)


def assess_reproducibility(text: str) -> list[ReproducibilityItem]:
    items: list[ReproducibilityItem] = []
    for rule in RULES:
        match = None
        for pattern in rule.patterns:
            match = re.search(pattern, text, flags=re.I | re.M)
            if match:
                break
        items.append(
            ReproducibilityItem(
                key=rule.key,
                label=rule.label,
                description=rule.description,
                detected=bool(match),
                evidence=snippet(text, match.start(), match.end()) if match else None,
            )
        )
    return items


def calculate_rci(items: list[ReproducibilityItem]) -> float:
    applicable = [item for item in items if item.applicable]
    if not applicable:
        return 0.0
    detected = sum(1 for item in applicable if item.detected)
    return round(100 * detected / len(applicable), 1)
