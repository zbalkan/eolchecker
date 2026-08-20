from __future__ import annotations

from pathlib import Path

import eolchecker.eolchecker as cli
from eolchecker.models import HardwareLifecycle, SoftwareLifecycle
from eolchecker.tools.downloader import SourceError


def test_no_arguments_prints_help_without_creating_cache(tmp_path: Path, capsys: object) -> None:
    cache_path = tmp_path / "eol.db"

    exit_code = cli.main(["--cache-path", str(cache_path)])

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert exit_code == 0
    assert "usage:" in captured.out
    assert not cache_path.exists()


def test_missing_cache_query_is_read_only(tmp_path: Path, capsys: object) -> None:
    cache_path = tmp_path / "eol.db"

    exit_code = cli.main(["--cache-path", str(cache_path), "--software", "nginx"])

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert exit_code == 0
    assert captured.out == "No software matches found.\n"
    assert not cache_path.exists()


def test_update_persists_downloaded_records(tmp_path: Path, capsys: object, monkeypatch: object) -> None:
    cache_path = tmp_path / "eol.db"

    class StubDownloader:
        def __enter__(self) -> StubDownloader:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def get_eol_software(self) -> list[SoftwareLifecycle]:
            return [SoftwareLifecycle("nginx", "1.26", "2026-04-23")]

        def get_eol_hardware(self) -> list[HardwareLifecycle]:
            return [HardwareLifecycle("Dell", "PowerEdge", "2030-01-01")]

    monkeypatch.setattr(cli, "Downloader", StubDownloader)  # type: ignore[attr-defined]

    exit_code = cli.main(["--cache-path", str(cache_path), "--update", "--software", "nginx"])

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert exit_code == 0
    assert cache_path.is_file()
    assert "Updated lifecycle cache" in captured.out
    assert "nginx, 1.26: 2026-04-23" in captured.out


def test_update_failure_returns_operational_exit_code(
    tmp_path: Path, capsys: object, monkeypatch: object
) -> None:
    class FailingDownloader:
        def __enter__(self) -> FailingDownloader:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def get_eol_software(self) -> list[SoftwareLifecycle]:
            raise SourceError("upstream unavailable")

        def get_eol_hardware(self) -> list[HardwareLifecycle]:
            raise AssertionError("Hardware source must not be called after software failure")

    monkeypatch.setattr(cli, "Downloader", FailingDownloader)  # type: ignore[attr-defined]

    exit_code = cli.main(["--cache-path", str(tmp_path / "eol.db"), "--update"])

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert exit_code == 3
    assert "ERROR: upstream unavailable" in captured.err
