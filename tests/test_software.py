from eolchecker.software import SoftwareUpdater


class DummyDB:
    def __init__(self):
        self.cleared = []

    def clear_table(self, name):
        self.cleared.append(name)


class TestableSoftwareUpdater(SoftwareUpdater):
    def __init__(self, db):
        super().__init__(db)
        self.inserted = []

    def _SoftwareUpdater__fetch_json(self, url):
        if url.endswith("/all.json"):
            return ["ubuntu"]
        return [{"cycle": "22.04"}]

    def insert(self, product, vals):
        self.inserted.append((product, vals))


def test_software_update_inserts_product_rows():
    db = DummyDB()
    updater = TestableSoftwareUpdater(db)
    updater.update()

    assert db.cleared == ["software"]
    assert updater.inserted[0][0] == "ubuntu"
    assert updater.inserted[0][1][0][0] == "22.04"
