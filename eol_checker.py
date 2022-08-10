import argparse
import sys
from typing import Optional

import colorama

from .eol.database import Database
from .eol.downloader import Downloader
from .eol.hardwareLifecycle import HardwareLifecycle
from .eol.softwareLifecycle import SoftwareLifecycle


def main() -> None:
    colorama.init(autoreset=True)
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Query EOL software or hardware.")
    if len(sys.argv) < 2:
        parser.print_help()
    parser.add_argument("--software", dest="query_software", type=str, required=False,
                        help="Query the software by name")
    parser.add_argument("--hardware", dest="query_hardware", type=str, required=False,
                        help="Query the software by name")
    parser.add_argument("-u", "--update", dest="update_db", action='store_true', required=False,
                        help="Updates the local database. When combined with a query, it updates the database before running the query.")
    args: argparse.Namespace = parser.parse_args()

    downloader: Downloader = Downloader()
    database: Database = Database('eol.db')

    if(args.update_db is True):
        success: bool = database.save(
            softwareList=downloader.get_eol_software(), hardwareList=downloader.get_eol_hardware())
        if(success):
            print("Updated the database.")

    if(args.query_software is not None):
        eolSoftwareList: Optional[list[SoftwareLifecycle]] = database.search_software(
            args.query_software)

        if(eolSoftwareList is None):
            print("No software matches found with keyword.")
        else:
            for eolSoftware in eolSoftwareList:
                print(eolSoftware)

    if(args.query_hardware is not None):
        eolHardwareList: Optional[list[HardwareLifecycle]] = database.search_hardware(
            args.query_hardware)

        if(eolHardwareList is None):
            print("No hardware matches found with keyword.")
        else:
            for eolHardware in eolHardwareList:
                print(eolHardware)

    database.close()


if __name__ == '__main__':
    main()
