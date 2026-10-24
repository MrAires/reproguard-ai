from reproguard.reproducibility import assess_reproducibility, calculate_rci


def test_reproducibility_signals_detect_clear_documentation():
    text = """
    We aim to evaluate a model on a public dataset. We use an 80/20 train/test split.
    Data preprocessing includes standardization. A random forest model uses n_estimators=200,
    max_depth=12, and random_state=42. We report accuracy, precision, recall and F1-score.
    The baseline is logistic regression. Source code is available at https://github.com/x/y.
    Experiments use Python 3.12 on an NVIDIA GPU. Five repeated runs report mean and standard deviation.
    """
    items = assess_reproducibility(text)
    detected = {item.key: item.detected for item in items}
    for key in ["problem", "dataset", "split", "preprocessing", "model", "hyperparameters", "seed", "metrics", "baselines", "code", "hardware", "statistics"]:
        assert detected[key], key
    assert calculate_rci(items) == 100.0


def test_rci_is_documentation_completeness_not_boolean_quality():
    items = assess_reproducibility("This paper has a dataset and reports accuracy.")
    score = calculate_rci(items)
    assert 0 < score < 100
