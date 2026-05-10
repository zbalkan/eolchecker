import duckdb

from eolchecker.db import Database
from eolchecker.metadata import Metadata


def test_metadata_set_and_get_roundtrip():
    con = duckdb.connect(":memory:")
    db = Database(conn=con, init_extensions=False)
    db._init_schema()
    metadata = Metadata(db)

    metadata.set("last_update_hardware", "123")

    assert metadata.get("last_update_hardware") == "123"
