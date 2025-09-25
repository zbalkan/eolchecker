import duckdb


class Database:
    def __init__(self, path: str = "eol.db") -> None:
        self.conn = duckdb.connect(path)
        self._init_extensions()
        self._init_schema()

    def _init_extensions(self) -> None:
        self.conn.execute("INSTALL httpfs; LOAD httpfs;")
        self.conn.execute("INSTALL fts; LOAD fts;")

    def _init_schema(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS software (
                id INTEGER PRIMARY KEY,
                name TEXT,
                cycle TEXT,
                eol TEXT,
                latest TEXT,
                lts TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS hardware (
                id INTEGER PRIMARY KEY,
                manufacturer TEXT,
                model TEXT,
                eol TEXT
            )
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

    def get_metadata(self, key: str):
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

    # BUG: Catalog Error: Table Function with name match_bm25 does not exist!
    # Did you mean "main.parquet_schema"?
    # LINE 4: JOIN LATERAL fts_main_software.match_bm25(s.rowid, ?) AS f(score) ON...
    #                                      ^
    #   File "C:\Users\zafer\source\repos\Personal\eolchecker\eolchecker\db.py", line 95, in search
    #         SELECT s.name, s.cycle, s.eol, s.latest, s.lts, f.score
    #            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #     ...<6 lines>...
    #   File "C:\Users\zafer\source\repos\Personal\eolchecker\eolchecker\cli.py", line 65, in main
    #     args.query, software=args.software, hardware=args.hardware)
    def search(self, query: str, software: bool = False, hardware: bool = False):
        results = []
        if not software and not hardware:
            software = hardware = True

        if software:
            rows = self.conn.execute("""
                SELECT s.name, s.cycle, s.eol, s.latest, s.lts, f.score
                FROM software AS s
                JOIN LATERAL fts_main_software.match_bm25(s.rowid, ?) AS f(score) ON TRUE
                WHERE f.score IS NOT NULL
                ORDER BY f.score DESC
                LIMIT 20
            """, [query]).fetchall()
            for r in rows:
                results.append(
                    {"type": "software", "name": r[0], "cycle": r[1],
                        "eol": r[2], "latest": r[3], "lts": r[4]}
                )

        if hardware:
            rows = self.conn.execute("""
                SELECT h.manufacturer, h.model, h.eol, f.score
                FROM hardware AS h
                JOIN LATERAL fts_main_hardware.match_bm25(h.rowid, ?) AS f(score) ON TRUE
                WHERE f.score IS NOT NULL
                ORDER BY f.score DESC
                LIMIT 20
            """, [query]).fetchall()
            for r in rows:
                results.append(
                    {"type": "hardware",
                        "manufacturer": r[0], "model": r[1], "eol": r[2]}
                )

        return results
