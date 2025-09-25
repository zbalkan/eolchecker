import argparse
import time
from typing import Final

from db import Database
from hardware import HardwareUpdater
from metadata import Metadata
from software import SoftwareUpdater
from tabulate import tabulate

RETENTION_PERIOD_SECONDS: Final[int] = 7 * 86400


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="eol",
        description="EOL Checker: Query software and hardware end-of-life data."
    )

    subparsers = parser.add_subparsers(dest="command")

    # Update command
    subparsers.add_parser(
        "update", help="Update local database with latest EOL data")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search EOL data")
    search_parser.add_argument("query", help="Search term")
    search_parser.add_argument(
        "--software", "-sw", action="store_true", help="Search software only")
    search_parser.add_argument(
        "--hardware", "-hw", action="store_true", help="Search hardware only")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
    else:
        db = Database()
        metadata = Metadata(db)

        if args.command == "update":
            print("Updating software and hardware data...")
            SoftwareUpdater(db).update()
            metadata.set("last_update_software", str(int(time.time())))
            HardwareUpdater(db).update()
            metadata.set("last_update_hardware", str(int(time.time())))
            db.update_indexes()
            print("Update complete.")

        elif args.command == "search":
            # Expiration check (7 days)
            now = int(time.time())
            last_sw = metadata.get("last_update_software")
            last_hw = metadata.get("last_update_hardware")

            if (not last_sw or now - int(last_sw) > RETENTION_PERIOD_SECONDS) or \
                    (not last_hw or now - int(last_hw) > RETENTION_PERIOD_SECONDS):
                print("Data older than 7 days. Updating...")
                SoftwareUpdater(db).update()
                metadata.set("last_update_software", str(now))
                HardwareUpdater(db).update()
                metadata.set("last_update_hardware", str(now))
                db.update_indexes()

            results = db.search(
                args.query, software=args.software, hardware=args.hardware)

            if not results:
                print("No results found.")
                return

            if results[0]["type"] == "software":
                table = [[r["name"], r["cycle"], r["eol"],
                          r["latest"], r["lts"]] for r in results]
                print(tabulate(table, headers=[
                    "Software", "Cycle", "EOL", "Latest", "LTS"]))
            else:
                table = [[r["manufacturer"], r["model"], r["eol"]]
                         for r in results]
                print(tabulate(table, headers=["Manufacturer", "Model", "EOL"]))
        else:
            print("Unknown command")
