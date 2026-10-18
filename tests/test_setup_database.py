from scripts.setup_database import load_statements


def test_sql_loader_ignores_comments_and_splits_statements(tmp_path):
    sql_file = tmp_path / "sample.sql"
    sql_file.write_text("-- comment\nSELECT 1;\nSELECT 2;\n")

    assert load_statements(sql_file) == ["SELECT 1", "SELECT 2"]
