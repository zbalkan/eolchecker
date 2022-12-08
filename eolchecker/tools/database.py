import logging
import sqlite3
from typing import Optional

from ..models import HardwareLifecycle, SoftwareLifecycle


# TODO: Add ID field for the records
class Database:

    __connection: sqlite3.Connection
    __cursor: sqlite3.Cursor

    def __init__(self, path: str) -> None:
        logging.debug('Initiated database connection')

        self.__connection = sqlite3.connect(path)
        self.__cursor = self.__connection.cursor()

    def save(self, software_list: Optional[list[SoftwareLifecycle]] = None,
             hardware_list: Optional[list[HardwareLifecycle]] = None) -> bool:
        logging.debug('Initiating database recreation')

        if (software_list is None):
            logging.debug(
                'Provided software list is empty. Leaving the database as is.')
            return False

        new_software_table_created: bool = self.__recreate_software_table()
        if (new_software_table_created is False):
            logging.debug(
                'Could not update the data. Leaving the database as is.')
            return False

        for software in software_list:
            try:
                software_cmd: str = "INSERT INTO software VALUES (?, ?, ?)"
                software_args: tuple[str, str, str] = (
                    software.name, software.version, software.eol)
                self.__cursor.execute(software_cmd, software_args)
            except Exception as exception:
                raise SystemExit(str(exception)) from exception

            self.__connection.commit()
            logging.debug('Updated software table succesfully')

        if (hardware_list is None):
            logging.debug(
                'Provided hardware list is empty. Leaving the database as is.')
            return False

        new_hardware_table_created: bool = self.__recreate_hardware_table()
        if (new_hardware_table_created is False):
            logging.debug(
               'Could not update the data. Leaving the database as is.')
            return False

        for hardware in hardware_list:
            try:
                hardware_cmd: str = "INSERT INTO hardware VALUES (?, ?, ?)"
                hardware_args: tuple[str, str, str] = (
                    hardware.manufacturer, hardware.model, hardware.eol)
                self.__cursor.execute(hardware_cmd, hardware_args)
            except Exception as exception:
                raise SystemExit(str(exception)) from exception

        self.__connection.commit()
        logging.debug('Updated hardware table succesfully')

        return True

    def search_software(self, software_name: str) -> Optional[list[SoftwareLifecycle]]:

        logging.debug(
            'Searching for keyword %s in software list', software_name)

        cmd: str = "SELECT * FROM software WHERE name LIKE ?"
        args: str = '%' + software_name + '%'
        self.__cursor.execute(cmd, (args,))

        rows: list = self.__cursor.fetchall()
        if (len(rows) == 0):
            logging.debug('Could not find a software matching the keyword')
            return None
        eol_software_list: list[SoftwareLifecycle] = []
        for row in rows:
            eol_software: SoftwareLifecycle = SoftwareLifecycle(name=row[0])
            eol_software.version = row[1]
            eol_software.eol = row[2]
            eol_software_list.append(eol_software)

        logging.debug('Found %s records matching the keyword',
                      str(len(eol_software_list)))

        return eol_software_list

    def search_hardware(self, hardware_name: str) -> Optional[list[HardwareLifecycle]]:

        logging.debug(
            'Searching for keyword %s in hardware list', hardware_name)

        cmd: str = "SELECT * FROM hardware WHERE manufacturer LIKE ? OR model LIKE ?"
        args: str = '%' + hardware_name + '%'
        self.__cursor.execute(cmd, (args, args,))

        rows: list = self.__cursor.fetchall()
        if (len(rows) == 0):
            logging.debug('Could not find a hardware matching the keyword')
            return None

        eol_hardware_list: list[HardwareLifecycle] = []
        for row in rows:
            eol_hardware: HardwareLifecycle = HardwareLifecycle(
                manufacturer=row[0], model=row[1], eol=row[2])
            eol_hardware_list.append(eol_hardware)

        logging.debug('Found %s records matching the keyword',
                      str(len(eol_hardware_list)))

        return eol_hardware_list

    def close(self) -> None:
        logging.debug('Closing database connection')
        self.__connection.close()

    def __recreate_software_table(self) -> bool:
        logging.debug('Recreating the software table')

        if (self.__table_exists('software')):
            logging.debug('Backing up the table...')
            self.__cursor.execute(
                "ALTER TABLE software RENAME TO software_bak;")

        try:
            self.__cursor.execute(
                '''CREATE TABLE 'software' (name text, version text, eol text)''')

            if (self.__table_exists('software_bak')):
                self.__cursor.execute("DROP TABLE software_bak;")

            logging.debug('Updated software table successfully.')
            return True

        except Exception as exception:
            logging.error(str(exception))
            logging.debug('An error occured. Rolling back.')
            if (self.__table_exists('software')):
                self.__cursor.execute("DROP TABLE software;")
            self.__cursor.execute(
                "ALTER TABLE software_bak RENAME TO software;")

            logging.debug('Failed to update software table')

            return False

    def __recreate_hardware_table(self) -> bool:

        logging.debug('Recreating the hardware table')

        if (self.__table_exists('hardware')):
            logging.debug('Backing up the table...')
            self.__cursor.execute(
                "ALTER TABLE hardware RENAME TO hardware_bak;")

        try:
            self.__cursor.execute(
                '''CREATE TABLE 'hardware' (manufacturer text, model text, eol text)''')

            if (self.__table_exists('hardware_bak')):
                self.__cursor.execute("DROP TABLE hardware_bak;")

            logging.debug('Updated hardware table successfully.')
            return True

        except Exception as exception:
            logging.error(str(exception))
            logging.debug('An error occured. Rolling back.')

            if (self.__table_exists('hardware')):
                self.__cursor.execute("DROP TABLE hardware;")

            self.__cursor.execute(
                "ALTER TABLE hardware_bak RENAME TO hardware;")

            logging.debug('Failed to update hardware table')

            return False

    def __table_exists(self, table: str) -> bool:
        logging.debug('Querying if table %s exists', table)
        cmd: str = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?"
        args: list[str] = [table]
        self.__cursor.execute(cmd, args)
        exist: bool = self.__cursor.fetchone()[0] == 1
        if (exist):
            logging.debug('Table %s exists', table)
            return True

        logging.debug('Table %s does not exist', table)
        return False
