from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
from collections.abc import Sequence
from pathlib import Path

from ..models import HardwareLifecycle, SoftwareLifecycle

logger = logging.getLogger(__name__)


class CacheError(RuntimeError):
    """Raised when the lifecycle cache cannot be read or safely replaced."""


class Database:
    """A SQLite-backed lifecycle cache with atomic refresh semantics."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser()

    def save(
        self,
        software_list: Sequence[SoftwareLifecycle],
        hardware_list: Sequence[HardwareLifecycle],
    ) -> bool:
        """Persist a complete validated generation without risking the active cache.

        A new database is built alongside the active cache and then atomically
        substituted only after both datasets have been written successfully.
        """
        software_records = list(software_list)
        hardware_records = list(hardware_list)
        self._validate_records(software_records, hardware_records)

        self._path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self._path.parent,
            prefix=f".{self._path.name}.",
            suffix=".tmp",
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)

        try:
            self._build_generation(temporary_path, software_records, hardware_records)
            os.replace(temporary_path, self._path)
            logger.info(
                "Replaced lifecycle cache at %s with %s software and %s hardware records",
                self._path,
                len(software_records),
                len(hardware_records),
            )
            return True
        except (OSError, sqlite3.Error) as exception:
            raise CacheError(f"Could not safely replace cache at {self._path}: {exception}") from exception
        finally:
            if temporary_path.exists():
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError as exception:
                    logger.warning("Could not remove temporary cache file %s: %s", temporary_path, exception)

    def search_software(self, software_name: str) -> list[SoftwareLifecycle]:
        """Return software records whose product name contains the supplied term."""
        query = self._normalized_query(software_name)
        rows = self._fetch_all(
            "SELECT name, version, eol FROM software WHERE name LIKE ? ORDER BY name, version",
            (query,),
        )
        return [SoftwareLifecycle(name=row[0], version=row[1], eol=row[2]) for row in rows]

    def search_hardware(self, hardware_name: str) -> list[HardwareLifecycle]:
        """Return hardware records whose manufacturer or model contains the supplied term."""
        query = self._normalized_query(hardware_name)
        rows = self._fetch_all(
            """
            SELECT manufacturer, model, eol
            FROM hardware
            WHERE manufacturer LIKE ? OR model LIKE ?
            ORDER BY manufacturer, model
            """,
            (query, query),
        )
        return [HardwareLifecycle(manufacturer=row[0], model=row[1], eol=row[2]) for row in rows]

    def close(self) -> None:
        """Retain the previous public API; connections are scoped per operation."""

    @staticmethod
    def _validate_records(
        software_records: Sequence[SoftwareLifecycle], hardware_records: Sequence[HardwareLifecycle]
    ) -> None:
        if not software_records:
            raise CacheError("Refusing to replace the cache with an empty software dataset")
        if not hardware_records:
            raise CacheError("Refusing to replace the cache with an empty hardware dataset")
        if not all(isinstance(record, SoftwareLifecycle) for record in software_records):
            raise CacheError("Software dataset contains an invalid record")
        if not all(isinstance(record, HardwareLifecycle) for record in hardware_records):
            raise CacheError("Hardware dataset contains an invalid record")

    @staticmethod
    def _build_generation(
        path: Path,
        software_records: Sequence[SoftwareLifecycle],
        hardware_records: Sequence[HardwareLifecycle],
    ) -> None:
        connection = sqlite3.connect(path)
        try:
            connection.execute("PRAGMA journal_mode = DELETE")
            connection.execute(
                "CREATE TABLE software (name TEXT NOT NULL, version TEXT NOT NULL, eol TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE hardware (manufacturer TEXT NOT NULL, model TEXT NOT NULL, eol TEXT NOT NULL)"
            )
            connection.executemany(
                "INSERT INTO software (name, version, eol) VALUES (?, ?, ?)",
                [(record.name, record.version, record.eol) for record in software_records],
            )
            connection.executemany(
                "INSERT INTO hardware (manufacturer, model, eol) VALUES (?, ?, ?)",
                [(record.manufacturer, record.model, record.eol) for record in hardware_records],
            )
            connection.execute("CREATE INDEX software_name_index ON software(name)")
            connection.execute("CREATE INDEX hardware_lookup_index ON hardware(manufacturer, model)")
            software_count = connection.execute("SELECT COUNT(*) FROM software").fetchone()[0]
            hardware_count = connection.execute("SELECT COUNT(*) FROM hardware").fetchone()[0]
            if software_count != len(software_records) or hardware_count != len(hardware_records):
                raise CacheError("Cache validation failed after writing the refreshed datasets")
            connection.commit()
        finally:
            connection.close()

    def _fetch_all(self, statement: str, parameters: tuple[str, ...]) -> list[tuple[str, ...]]:
        if not self._path.is_file():
            return []
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(f"{self._path.resolve().as_uri()}?mode=ro", uri=True)
            return connection.execute(statement, parameters).fetchall()
        except sqlite3.Error as exception:
            raise CacheError(f"Could not read cache at {self._path}: {exception}") from exception
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _normalized_query(value: str) -> str:
        return f"%{value.strip()}%"
