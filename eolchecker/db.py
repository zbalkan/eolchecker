import os
from typing import Any, Optional

import duckdb


class Database:
    def __init__(self, db_path: str = "eol.db") -> None:
        first_time = False
        if not os.path.exists(db_path):
            first_time = True

        self.conn = duckdb.connect(db_path)
        self._init_extensions()
        if first_time:
            self._init_schema()

    def _init_extensions(self) -> None:
        self.conn.execute("INSTALL httpfs; LOAD httpfs;")
        self.conn.execute("INSTALL fts; LOAD fts;")

    def _init_schema(self) -> None:
        self.conn.execute("""
            DROP TABLE IF EXISTS software;
            CREATE TABLE software (
                id UUID DEFAULT uuidv7() PRIMARY KEY,
                name TEXT,
                cycle TEXT,
                releaseLabel TEXT,
                releaseDate TEXT,
                eol TEXT,
                latest TEXT,
                latestReleaseDate TEXT,
                lts TEXT,
                support TEXT,
                extendedSupport TEXT,
                link TEXT
            );
        """)
        self.conn.execute("""
            DROP TABLE IF EXISTS hardware;
            CREATE TABLE hardware (
                id UUID DEFAULT uuidv7() PRIMARY KEY,
                manufacturer TEXT,
                model TEXT,
                eol TEXT
            );
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

    def set_metadata(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO metadata VALUES (?, ?)", [key, value])

    def get_metadata(self, key: str) -> Optional[Any]:
        row = self.conn.execute(
            "SELECT value FROM metadata WHERE key = ?", [key]).fetchone()
        return row[0] if row else None

    def clear_table(self, table: str) -> None:
        self.conn.execute(f"DELETE FROM {table}")

    def insert(self, table: str, values: list) -> None:
        placeholders = ", ".join(["?"] * len(values))
        self.conn.execute(
            f"INSERT INTO {table} VALUES (DEFAULT, {placeholders})", values
        )

    def insert_many(self, table: str, rows: list[list]) -> None:
        if not rows:
            return
        placeholders = ", ".join(["?"] * len(rows[0]))
        self.conn.executemany(
            f"INSERT INTO {table} VALUES ({placeholders})", rows
        )

    def update_indexes(self) -> None:
        self.conn.execute("""
            PRAGMA create_fts_index(
                'software',
                'id',
                'name',
                'cycle',
                'releaseLabel',
                'latest',
                'lts',
                overwrite = 1
            )
        """)
        self.conn.execute("""
            PRAGMA create_fts_index(
                'hardware',
                'id',
                'manufacturer',
                'model',
                'eol',
                overwrite = 1
            )
        """)

    def search(self, query: str, software: bool = False, hardware: bool = False) -> dict[str, list[dict]]:
        results: dict[str, list[dict]] = {}
        if not software and not hardware:
            software = hardware = True

        if software:
            cur = self.conn.execute("""
                SELECT *, sq.score
                FROM software s
                JOIN (
                    SELECT id, fts_main_software.match_bm25(id, ?) AS score
                    FROM software
                ) sq ON s.id = sq.id
                WHERE sq.score IS NOT NULL
                ORDER BY sq.score DESC
                LIMIT 10;
            """, [query])
            if cur is not None:
                cols = self.__get_column_names(cur)
                rows = cur.fetchall()
                results["software"] = [
                    self.__row_to_dict(cols, row) for row in rows]

        if hardware:
            cur = self.conn.execute("""
                SELECT h.*, sq.score
                FROM hardware h
                JOIN (
                    SELECT id, fts_main_hardware.match_bm25(id, ?) AS score
                    FROM hardware
                ) sq ON h.id = sq.id
                WHERE sq.score IS NOT NULL
                ORDER BY sq.score DESC
                LIMIT 10;
            """, [query])
            if cur is not None:
                cols = self.__get_column_names(cur)
                rows = cur.fetchall()
                results["hardware"] = [self.__row_to_dict(cols, row) for row in rows]

        return results

    def __get_column_names(self, cur: duckdb.DuckDBPyConnection) -> list[str]:
        cols: list[str] = [desc[0] if desc and desc[0] else f"col_{i}"
                for i, desc in enumerate(cur.description)]
        return cols

    def __row_to_dict(self, cols: list[str], row: list[str], exclude: tuple = ("id", "score")) -> dict:
        return {
            col: val
            for col, val in zip(cols, row)
            if col not in exclude and val is not None
        }
