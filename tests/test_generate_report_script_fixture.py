import subprocess
import sys


FORBIDDEN_TERMS = [
    "buy",
    "sell",
    "guaranteed",
    "will rise",
    "will fall",
    "target price",
    "must trade",
]


def test_generate_report_script_fixture_pipeline(tmp_path):
    raw_path = tmp_path / "raw_news.csv"
    signals_path = tmp_path / "news_signals.csv"
    candidates_path = tmp_path / "taiwan_impact_candidates.csv"
    report_path = tmp_path / "taiwan_premarket_report.md"

    subprocess.run(
        [
            sys.executable,
            "scripts/collect_news.py",
            "--mode",
            "fixture",
            "--date",
            "2026-01-15",
            "--output",
            str(raw_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/classify_news.py",
            "--input",
            str(raw_path),
            "--date",
            "2026-01-15",
            "--output",
            str(signals_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/map_taiwan_impacts.py",
            "--input",
            str(signals_path),
            "--date",
            "2026-01-15",
            "--output",
            str(candidates_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_report.py",
            "--signals",
            str(signals_path),
            "--candidates",
            str(candidates_path),
            "--date",
            "2026-01-15",
            "--output",
            str(report_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert report_path.exists()
    assert "output path:" in result.stdout
    report = report_path.read_text(encoding="utf-8")

    for header in [
        "Executive Summary",
        "Overnight U.S. News Themes",
        "Taiwan Watchlist Candidates",
        "Potentially Positive Candidates",
        "Potentially Negative Candidates",
        "Neutral / Unmapped / Requires Review",
        "Source Provenance",
        "Limitations",
    ]:
        assert header in report

    lowered = report.lower()
    assert all(term not in lowered for term in FORBIDDEN_TERMS)
    assert "raw_summary" not in lowered
    assert "article_body" not in lowered
    assert "article body" not in lowered
    assert "requires validation" in lowered
    assert "not investment advice" in lowered
    assert "no llm generation" in lowered
    assert "taiwan targets" in lowered
