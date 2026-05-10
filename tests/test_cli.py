from eolchecker import cli


class DummyUpdater:
    calls = []

    def __init__(self, _db):
        pass

    def update(self):
        self.calls.append(True)


class DummyDB:
    def __init__(self):
        self.indexes_updated = False

    def update_indexes(self):
        self.indexes_updated = True


class DummyMetadata:
    def __init__(self):
        self.values = {}

    def set(self, key, value):
        self.values[key] = value


def test_update_all_data_sets_timestamps_and_updates_indexes():
    db = DummyDB()
    metadata = DummyMetadata()

    original_sw, original_hw = cli.SoftwareUpdater, cli.HardwareUpdater
    try:
        cli.SoftwareUpdater = DummyUpdater
        cli.HardwareUpdater = DummyUpdater
        cli.update_all_data(db, metadata, now=100)
    finally:
        cli.SoftwareUpdater, cli.HardwareUpdater = original_sw, original_hw

    assert metadata.values == {
        "last_update_software": "100",
        "last_update_hardware": "100",
    }
    assert db.indexes_updated is True
