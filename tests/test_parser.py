from pathlib import Path

from reproguard.parser import extract_dois, extract_github_urls, parse_pdf


def test_extract_dois_normalizes_and_deduplicates():
    text = "DOI: 10.1023/A:1010933404324 and https://doi.org/10.1023/A:1010933404324."
    assert extract_dois(text) == ["10.1023/a:1010933404324"]


def test_extract_github_urls_deduplicates_and_strips_git():
    text = "See https://github.com/example/project.git and https://github.com/example/project."
    assert extract_github_urls(text) == ["https://github.com/example/project"]


def test_parse_bundled_demo_pdf():
    path = Path("examples/sample_research_paper.pdf")
    parsed = parse_pdf(path.read_bytes())
    assert parsed.page_count == 2
    assert parsed.title is not None
    assert "Reproducible Benchmarking" in parsed.title
    assert len(parsed.dois) == 2
    assert "https://github.com/scikit-learn/scikit-learn" in parsed.github_urls
