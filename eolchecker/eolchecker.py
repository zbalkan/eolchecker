from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from eolchecker.tools import CacheError, Database, Downloader, SourceError

APP_NAME = "eolchecker"
APP_VERSION = "0.2.0"
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} {APP_VERSION}: query cached software and hardware lifecycle data."
    )
    parser.add_argument("--software", metavar="NAME", help="Search software lifecycle records by product name")
    parser.add_argument("--hardware", metavar="NAME", help="Search hardware lifecycle records by manufacturer or model")
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Fetch, validate, and atomically replace the local lifecycle cache before querying",
    )
    parser.add_argument(
        "--cache-path",
        type=Path,
        default=default_cache_path(),
        help="Path to the local SQLite cache (default: %(default)s)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable diagnostic logging")
    return parser


def default_cache_path() -> Path:
    cache_home = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache_home / APP_NAME / "eol.db"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.update and args.software is None and args.hardware is None:
        parser.print_help()
        return 0

    configure_logging(args.verbose)
    database = Database(args.cache_path)

    try:
        if args.update:
            print("Updating the lifecycle cache. This may take a moment.")
            with Downloader() as downloader:
                database.save(
                    software_list=downloader.get_eol_software(),
                    hardware_list=downloader.get_eol_hardware(),
                )
            print(f"Updated lifecycle cache: {args.cache_path}")

        if args.software is not None:
            _print_software_results(database.search_software(args.software))
        if args.hardware is not None:
            _print_hardware_results(database.search_hardware(args.hardware))
    except (CacheError, SourceError) as exception:
        logger.error("Lifecycle operation failed: %s", exception)
        print(f"ERROR: {exception}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("Cancelled by user.", file=sys.stderr)
        return 130

    return 0


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )


def _print_software_results(records: Sequence[object]) -> None:
    if not records:
        print("No software matches found.")
        return
    print("Software, Version: EOL Date")
    print("***************************")
    for record in records:
        print(record)
    print("***************************")
    print(f"Total {len(records)} software records found.")


def _print_hardware_results(records: Sequence[object]) -> None:
    if not records:
        print("No hardware matches found.")
        return
    print("Manufacturer, Model: EOL Date")
    print("*****************************")
    for record in records:
        print(record)
    print("*****************************")
    print(f"Total {len(records)} hardware records found.")


if __name__ == "__main__":
    sys.exit(main())
