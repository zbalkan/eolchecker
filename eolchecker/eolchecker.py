import argparse
import datetime
import logging
import os
import sys
from typing import Final, Optional

import colorama

from eolchecker.models import HardwareLifecycle, SoftwareLifecycle
from eolchecker.tools import Database, Downloader

ENCODING: Final[str] = "utf-8"
APP_NAME: Final[str] = 'eolchecker'
APP_VERSION: Final[str] = '0.1'
DB_PATH: Final[str] = 'eol.db'


def main() -> None:
    colorama.init(autoreset=True)
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=f"""
        {APP_NAME} (v{APP_VERSION})": Query EOL software or hardware.
        """)
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
    logging.info('eolchecker parameters: %s', args)
    update_db: bool = args.update_db

    logging.info('Initiating downloader.')
    download: Downloader = Downloader()

    logging.info('Initiate database on first use.')

    # If update parameter is given, no need to check
    if update_db == False:
        # Create the database on first use
        if os.path.exists(DB_PATH) is False:
            update_db = True
        else:
            # Update if database is older than 7 days
            modify_date = datetime.datetime.fromtimestamp(
                os.path.getmtime(DB_PATH))
            if modify_date < (datetime.datetime.now() - datetime.timedelta(days=7)):
                print(
                    'Database is older than 7 days. It will be updated before the query.')
                update_db = True

    logging.info('Opening database connection')
    database: Database = Database(DB_PATH)

    if (update_db is True):

        print('Updating the database, it will take time.')
        logging.info('Starting download')
        new_eol_software: list[SoftwareLifecycle] = download.get_eol_software(
        )
        new_eol_hardware: list[HardwareLifecycle] = download.get_eol_hardware(
        )
        logging.info('Finished download')

        logging.info('Updating database')
        success: bool = database.save(
            software_list=new_eol_software, hardware_list=new_eol_hardware)

        if (success):
            logging.info('Updated database')
            print("Updated the database.")

    if (args.query_software is not None):
        logging.info('Querying for keyword: %s', args.query_software)

        eol_software_list: Optional[list[SoftwareLifecycle]] = database.search_software(
            args.query_software)

        if (eol_software_list is None):
            logging.info("No software matches found with keyword.")
            print("No software matches found with keyword.")
        else:
            print("Software, Version: EOL Date")
            print("***************************")
            for eol_software in eol_software_list:
                logging.info("Software found: %s", eol_software)
                print(eol_software)

            print("***************************")
            print('Total ' + str(len(eol_software_list)) +
                  ' software records found.')

    if (args.query_hardware is not None):
        logging.info('Querying for keyword: %s', args.query_hardware)
        eol_hardware_list: Optional[list[HardwareLifecycle]] = database.search_hardware(
            args.query_hardware)

        if (eol_hardware_list is None):
            logging.info("No hardware matches found with keyword.")
            print("No hardware matches found with keyword.")
        else:
            print("Manufacturer, Model: EOL Date")
            print("*****************************")
            for eol_hardware in eol_hardware_list:
                logging.info("Hardware found: %s", eol_hardware)
                print(eol_hardware)

            print("*****************************")
            print('Total ' + str(len(eol_hardware_list)) +
                  ' hardware records found.')

    database.close()
    logging.info('Closed database connection')
    logging.info('Exiting')


def get_root_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(__file__)
    else:
        return './'


if __name__ == "__main__":
    try:
        logging.basicConfig(filename=os.path.join(get_root_dir(), f'{APP_NAME}.log'),
                            encoding=ENCODING,
                            format='%(asctime)s:%(levelname)s:%(message)s',
                            datefmt="%Y-%m-%dT%H:%M:%S%z",
                            level=logging.INFO)

        excepthook = logging.error
        logging.info('Starting')
        main()
        logging.info('Exiting.')
    except KeyboardInterrupt:
        print('Cancelled by user.')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except Exception as ex:
        print('ERROR: ' + str(ex))
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
