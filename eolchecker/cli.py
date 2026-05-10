import argparse
import time
from typing import Final

from db import Database
from hardware import HardwareUpdater
from metadata import Metadata
from software import SoftwareUpdater
from tabulate import tabulate

RETENTION_PERIOD_SECONDS: Final[int] = 7 * 86400


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eol",
        description="EOL Checker: Query software and hardware end-of-life data."
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("update", help="Update local database with latest EOL data")

    search_parser = subparsers.add_parser("search", help="Search EOL data")
    search_parser.add_argument("query", help="Search term")
    search_parser.add_argument("--software", "-sw", action="store_true", help="Search software only")
    search_parser.add_argument("--hardware", "-hw", action="store_true", help="Search hardware only")
    return parser


def update_all_data(db: Database, metadata: Metadata, now: int | None = None) -> None:
    ts = str(now if now is not None else int(time.time()))
    SoftwareUpdater(db).update()
    metadata.set("last_update_software", ts)
    HardwareUpdater(db).update()
    metadata.set("last_update_hardware", ts)
    db.update_indexes()


def render_results(results: dict[str, list[dict]]) -> None:
    if not results:
        print("No results found.")
        return

    for t, rows in results.items():
        if len(rows) == 0:
            print(f'No {t} results')
        else:
            print(f"\n=== {t.capitalize()} Results ===")
            keys = [k for k in rows[0].keys() if k != "score"]
            table = [[r.get(k, "") for k in keys] for r in rows]
            print(tabulate(table, headers=[k.capitalize() for k in keys]))


def main() -> None:
    parser = build_parser()

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
    else:
        db = Database()
        metadata = Metadata(db)

        if args.command == "update":
            print("Updating software and hardware data...")
            update_all_data(db, metadata)
            print("Update complete.")

        elif args.command == "search":
            # Expiration check (7 days)
            now = int(time.time())
            last_sw = metadata.get("last_update_software")
            last_hw = metadata.get("last_update_hardware")

            if (not last_sw or now - int(last_sw) > RETENTION_PERIOD_SECONDS) or \
                    (not last_hw or now - int(last_hw) > RETENTION_PERIOD_SECONDS):
                print("Data older than 7 days. Updating...")
                update_all_data(db, metadata, now=now)

            results = db.search(args.query, software=args.software, hardware=args.hardware)
            render_results(results)

        else:
            print("Unknown command")
