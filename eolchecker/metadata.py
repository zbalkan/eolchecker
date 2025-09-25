from db import Database

class Metadata:
    def __init__(self, db: Database):
        self.db = db

    def set(self, key: str, value: str):
        self.db.set_metadata(key, value)

    def get(self, key: str):
        return self.db.get_metadata(key)
