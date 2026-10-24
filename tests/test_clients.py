from reproguard.clients import parse_github_repo
from reproguard.utils import normalize_doi, title_similarity


def test_parse_github_repo():
    assert parse_github_repo("https://github.com/openai/openai-python") == ("openai", "openai-python")


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1000/ABC.123).") == "10.1000/abc.123"


def test_title_similarity():
    score = title_similarity("Random Forests", "Random Forests")
    assert score == 1.0
