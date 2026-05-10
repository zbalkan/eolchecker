from db import Database


class Metadata:
    def __init__(self, db: Database) -> None:
        self.db = db

    def set(self, key: str, value: str) -> None:
        self.db.set_metadata(key, value)

    def get(self, key: str) -> str | None:
        return self.db.get_metadata(key)
