import requests
from db import Database


class SoftwareUpdater:
    BASE_URL = "https://endoflife.date/api"

    def __init__(self, db: Database):
        self.db = db

    def update(self) -> None:
        self.db.clear_table("software")

        # Load the list of all products directly in DuckDB
        products = self.db.conn.execute(f"""
            SELECT *
            FROM read_json('{self.BASE_URL}/all.json')
        """).fetchall()

        for (product,) in products:
            try:
                query = f"""
                    INSERT INTO software
                    SELECT
                        '{product}' AS name,
                        cycle,
                        eol,
                        latest,
                        CASE WHEN lts = true THEN 'LTS' ELSE NULL END AS lts
                    FROM read_json('{self.BASE_URL}/{product}.json', auto_detect=true)
                """
                self.db.conn.execute(query)
            except Exception:
                continue
