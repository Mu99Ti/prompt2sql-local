from app.core.normalizer.sql_normalizer import SQLNormalizer


def test_normalizer_adds_semicolon() -> None:
    n = SQLNormalizer()
    assert n.normalize("select 1") == "select 1;"
