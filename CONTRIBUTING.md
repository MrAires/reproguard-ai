# Contributing to ReproGuard AI

Thank you for improving reproducible research tooling.

## Good first contributions

- Add a new transparent reproducibility detector with tests.
- Improve DOI extraction edge cases.
- Add support for another scholarly metadata source.
- Improve repository reproducibility checks.
- Add benchmark annotations to an openly licensed evaluation set.
- Improve accessibility or the Streamlit interface.

## Development workflow

1. Fork the repository and create a focused branch.
2. Install development dependencies: `pip install -r requirements-dev.txt`.
3. Add or update tests for behavior changes.
4. Run `pytest -q` and `ruff check .`.
5. Open a pull request describing the problem, evidence, and validation.

## Research integrity rule

Do not label a paper fraudulent, false, low quality, or retracted based only on automated output. ReproGuard reports documentation signals and metadata checks that require human interpretation.
