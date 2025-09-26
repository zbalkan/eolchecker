from typing import Any

from db import Database
from helper import requests_session_with_retries


class SoftwareUpdater:
    BASE_URL = "https://endoflife.date/api"

    def __init__(self, db: Database) -> None:
        self.db = db
        self.session = requests_session_with_retries()

    def update(self) -> None:
        self.db.clear_table("software")
        products = self.__fetch_json(f"{self.BASE_URL}/all.json")

        for product in products:
            all_values: list[list[str]] = self.__download(product)
            if all_values:
                self.insert(product, all_values)

    def insert(self, product: str, vals: list[list[str]]) -> None:
        self.db.conn.executemany("""
                    INSERT INTO software (
                        id, name, cycle, releaseLabel, releaseDate,
                        eol, latest, latestReleaseDate, lts,
                        support, extendedSupport, link
                    ) VALUES (
                        uuid(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, [(product, *r) for r in vals])

    def __fetch_json(self, url: str) -> Any:
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def __download(self, product: str) -> list[list[str]]:
        all_values: list[list[str]] = []
        print(f"Downloading data for {product}")
        try:
            data = self.__fetch_json(f"{self.BASE_URL}/{product}.json")

            for entry in data:
                all_values.append([
                    entry.get("cycle"),
                    entry.get("releaseLabel"),
                    entry.get("releaseDate"),
                    entry.get("eol"),
                    entry.get("latest"),
                    entry.get("latestReleaseDate"),
                    entry.get("lts"),
                    entry.get("support"),
                    entry.get("extendedSupport"),
                    entry.get("link"),
                ])
        except Exception as ex:
            print(f"Failed for {product}: {ex}")

        return all_values
