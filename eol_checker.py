import argparse
import logging
import sys
from typing import Optional

import colorama

from database import Database
from downloader import Downloader
from hardwareLifecycle import HardwareLifecycle
from softwareLifecycle import SoftwareLifecycle


def main() -> None:
    logging.basicConfig(filename='eol.log',
                        encoding='utf-8',
                        format='%(asctime)s %(message)s',
                        level=logging.DEBUG)

    excepthook = logging.error
    logging.debug('eol_checker started')

    colorama.init(autoreset=True)
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Query EOL software or hardware.")
    if len(sys.argv) < 2:
        parser.print_help()
    parser.add_argument("--software", dest="query_software",
                        type=str, required=False,
                        help="Query the software by name")
    parser.add_argument("--hardware", dest="query_hardware",
                        type=str,
                        required=False,
                        help="Query the software by name")
    parser.add_argument("-u", "--update",
                        dest="update_db",
                        action='store_true',
                        required=False,
                        help="Updates the local database. When combined with a query, it updates the database before running the query.")
    args: argparse.Namespace = parser.parse_args()
    logging.debug('eol_checker parameters: %s', args)

    download: Downloader = Downloader()

    logging.debug('Opening database connection')
    db: Database = Database('eol.db')

    if(args.update_db is True):
        logging.debug('Starting download')
        newEolSoftware: list[SoftwareLifecycle] = download.get_eol_software(
        )
        newEolHardware: list[HardwareLifecycle] = download.get_eol_hardware(
        )
        logging.debug('Finished download')

        logging.debug('Updating database')
        success: bool = db.save(
            softwareList=newEolSoftware, hardwareList=newEolHardware)

        if(success):
            logging.debug('Updated database')
            print("Updated the database.")

    if(args.query_software is not None):
        logging.debug('querying for %s', args.query_software)

        eolSoftwareList: Optional[list[SoftwareLifecycle]] = db.search_software(
            args.query_software)

        if(eolSoftwareList is None):
            logging.debug("No software matches found with keyword.")
            print("No software matches found with keyword.")
        else:
            for eolSoftware in eolSoftwareList:
                logging.debug("Software found.")
                print(eolSoftware)

    if(args.query_hardware is not None):
        logging.debug('querying for %s', args.query_hardware)
        eolHardwareList: Optional[list[HardwareLifecycle]] = db.search_hardware(
            args.query_hardware)

        if(eolHardwareList is None):
            logging.debug("No hardware matches found with keyword.")
            print("No hardware matches found with keyword.")
        else:
            for eolHardware in eolHardwareList:
                logging.debug("Hardware found.")
                print(eolHardware)

    db.close()
    logging.debug('Closed database connection')


if __name__ == '__main__':
    main()
