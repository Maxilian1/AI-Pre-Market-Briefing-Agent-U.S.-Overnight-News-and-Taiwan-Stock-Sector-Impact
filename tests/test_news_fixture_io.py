from src.news_collectors.base import NewsItem
from src.news_collectors.dedupe import assign_duplicate_group_ids
from src.news_collectors.io import load_fixture_news, load_news_csv, save_news_csv


def test_fixture_loads():
    items = load_fixture_news("data/fixtures/sample_raw_news.json")

    assert len(items) >= 8


def test_fixture_can_be_converted_into_news_items():
    items = load_fixture_news("data/fixtures/sample_raw_news.json")

    assert all(isinstance(item, NewsItem) for item in items)
    assert all(item.collection_mode == "fixture" for item in items)
    assert all(item.normalized_title_hash for item in items)


def test_saving_and_loading_csv_works(tmp_path):
    items = load_fixture_news("data/fixtures/sample_raw_news.json")
    rows = assign_duplicate_group_ids(items)
    output_path = tmp_path / "news.csv"

    save_news_csv(rows, output_path)
    loaded_rows = load_news_csv(output_path)

    assert len(loaded_rows) == len(rows)
    assert "duplicate_group_id" in loaded_rows[0]
    assert "news_id" in loaded_rows[0]
