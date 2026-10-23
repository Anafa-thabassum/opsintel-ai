from pathlib import Path

from scripts.evaluate_public_corpus import evaluate, render_markdown


def test_public_corpus_is_reproducible_and_publishes_failures():
    root = Path(__file__).resolve().parents[1]
    report = evaluate(root / "evaluation" / "public_failure_corpus_v1.csv")
    markdown = render_markdown(report)

    assert report["total"] == 9
    assert report["correct"] < report["total"]
    assert all(result["source_url"] for result in report["results"])
    assert all(result["license"] == "Apache-2.0" for result in report["results"])
    assert "## Published failures" in markdown
    assert "not an independent accuracy estimate" in report["scope"]
