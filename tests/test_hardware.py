from eolchecker.hardware import HardwareUpdater


class DummyDB:
    def __init__(self):
        self.cleared = []

    def clear_table(self, name):
        self.cleared.append(name)


class TestableHardwareUpdater(HardwareUpdater):
    def __init__(self, db):
        super().__init__(db)
        self.inserted = []

    def _HardwareUpdater__download(self):
        return [["dell", "r730", "2025-12-31"]]

    def insert(self, vals):
        self.inserted = vals


def test_hardware_update_inserts_downloaded_rows():
    db = DummyDB()
    updater = TestableHardwareUpdater(db)
    updater.update()

    assert db.cleared == ["hardware"]
    assert updater.inserted == [["dell", "r730", "2025-12-31"]]
