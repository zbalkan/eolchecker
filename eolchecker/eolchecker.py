import argparse
import logging
import sys
from typing import Optional

import colorama

from eolchecker.models import HardwareLifecycle, SoftwareLifecycle
from eolchecker.tools import Database, Downloader


def main() -> None:
    logging.basicConfig(filename='eol.log',
                        encoding='utf-8',
                        format='%(asctime)s %(message)s',
                        level=logging.DEBUG)

    excepthook = logging.error
    logging.debug('eolchecker started')

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
                        help="Updates the local database. \
                            When combined with a query, \
                            it updates the database before running the query.")
    args: argparse.Namespace = parser.parse_args()
    logging.debug('eolchecker parameters: %s', args)

    download: Downloader = Downloader()

    logging.debug('Opening database connection')
    database: Database = Database('eol.db')

    if (args.update_db is True):
        logging.debug('Starting download')
        new_eol_software: list[SoftwareLifecycle] = download.get_eol_software(
        )
        new_eol_hardware: list[HardwareLifecycle] = download.get_eol_hardware(
        )
        logging.debug('Finished download')

        logging.debug('Updating database')
        success: bool = database.save(
            software_list=new_eol_software, hardware_list=new_eol_hardware)

        if (success):
            logging.debug('Updated database')
            print("Updated the database.")

    if (args.query_software is not None):
        logging.debug('Querying for keyword: %s', args.query_software)

        eol_software_list: Optional[list[SoftwareLifecycle]] = database.search_software(
            args.query_software)

        if (eol_software_list is None):
            logging.debug("No software matches found with keyword.")
            print("No software matches found with keyword.")
        else:
            print("Software, Version: EOL Date")
            print("***************************")
            for eol_software in eol_software_list:
                logging.debug("Software found: %s", eol_software)
                print(eol_software)

            print("***************************")
            print('Total ' + str(len(eol_software_list)) +
                  ' software records found.')

    if (args.query_hardware is not None):
        logging.debug('Querying for keyword: %s', args.query_hardware)
        eol_hardware_list: Optional[list[HardwareLifecycle]] = database.search_hardware(
            args.query_hardware)

        if (eol_hardware_list is None):
            logging.debug("No hardware matches found with keyword.")
            print("No hardware matches found with keyword.")
        else:
            print("Manufacturer, Model: EOL Date")
            print("*****************************")
            for eol_hardware in eol_hardware_list:
                logging.debug("Hardware found: %s", eol_hardware)
                print(eol_hardware)

            print("*****************************")
            print('Total ' + str(len(eol_hardware_list)) +
                  ' hardware records found.')

    database.close()
    logging.debug('Closed database connection')
    logging.debug('Exiting')


if __name__ == '__main__':
    main()
