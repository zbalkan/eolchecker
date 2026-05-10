import duckdb
import pytest

from eolchecker.db import Database


def test_row_to_dict_excludes_id_and_score_without_values():
    db = object.__new__(Database)

    cols = ['id', 'name', 'score', 'eol']
    row = ['uuid', 'ubuntu', 0.5, None]

    parsed = db._Database__row_to_dict(cols, row)

    assert parsed == {'name': 'ubuntu'}


def test_clear_table_rejects_invalid_table_name():
    con = duckdb.connect(":memory:")
    db = Database(conn=con, init_extensions=False)

    with pytest.raises(ValueError, match="Invalid table name"):
        db.clear_table("invalid_table")


def test_metadata_roundtrip_with_in_memory_duckdb():
    con = duckdb.connect(":memory:")
    db = Database(conn=con, init_extensions=False)
    db._init_schema()

    db.set_metadata("last_update_software", "123")

    assert db.get_metadata("last_update_software") == "123"
