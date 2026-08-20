from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest

from eolchecker.models import HardwareLifecycle, SoftwareLifecycle
from eolchecker.tools.database import CacheError, Database


def software(name: str = "nginx") -> SoftwareLifecycle:
    return SoftwareLifecycle(name=name, version="1.0", eol="2030-01-01")


def hardware(model: str = "PowerEdge") -> HardwareLifecycle:
    return HardwareLifecycle(manufacturer="Dell", model=model, eol="2030-01-01")


def test_empty_refresh_is_rejected_and_preserves_active_cache(tmp_path: Path) -> None:
    cache_path = tmp_path / "eol.db"
    database = Database(cache_path)
    database.save([software()], [hardware()])

    with pytest.raises(CacheError, match="empty software"):
        database.save([], [hardware("Replacement")])

    assert database.search_software("nginx") == [software()]
    assert database.search_hardware("PowerEdge") == [hardware()]


def test_failed_generation_build_preserves_active_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_path = tmp_path / "eol.db"
    database = Database(cache_path)
    database.save([software()], [hardware()])

    def fail_build(*_: object) -> None:
        raise sqlite3.OperationalError("simulated disk failure")

    monkeypatch.setattr(database, "_build_generation", fail_build)

    with pytest.raises(CacheError, match="simulated disk failure"):
        database.save([software("replacement")], [hardware("replacement")])

    assert database.search_software("nginx") == [software()]
    assert database.search_hardware("PowerEdge") == [hardware()]


def test_searching_a_missing_or_empty_cache_returns_no_records(tmp_path: Path) -> None:
    database = Database(tmp_path / "missing.db")

    assert database.search_software("nginx") == []
    assert database.search_hardware("PowerEdge") == []


def test_successful_refresh_replaces_the_whole_generation(tmp_path: Path) -> None:
    database = Database(tmp_path / "eol.db")
    database.save([software("old")], [hardware("old")])

    database.save([software("new")], [hardware("new")])

    assert database.search_software("old") == []
    assert database.search_hardware("old") == []
    assert database.search_software("new") == [software("new")]
    assert database.search_hardware("new") == [hardware("new")]


def test_generation_connection_is_closed_before_cache_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import eolchecker.tools.database as database_module

    original_connect = sqlite3.connect
    connections: list[TrackingConnection] = []

    class TrackingConnection:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._connection = connection
            self.closed = False

        def __getattr__(self, name: str) -> object:
            return getattr(self._connection, name)

        def __enter__(self) -> TrackingConnection:
            self._connection.__enter__()
            return self

        def __exit__(
            self,
            exception_type: type[BaseException] | None,
            exception: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None:
            return self._connection.__exit__(exception_type, exception, traceback)

        def close(self) -> None:
            self.closed = True
            self._connection.close()

    def tracking_connect(*arguments: Any, **keywords: Any) -> TrackingConnection:
        connection = TrackingConnection(
            original_connect(*arguments, **keywords)  # type: ignore[call-overload]
        )
        connections.append(connection)
        return connection

    monkeypatch.setattr(database_module.sqlite3, "connect", tracking_connect)

    Database(tmp_path / "eol.db").save([software()], [hardware()])

    assert len(connections) == 1
    assert connections[0].closed
