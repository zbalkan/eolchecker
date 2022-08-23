import logging
import sqlite3
from typing import Optional

from models.hardwareLifecycle import HardwareLifecycle
from models.softwareLifecycle import SoftwareLifecycle


# TODO: Add ID field for the records
class Database:

    __connection: sqlite3.Connection
    __cursor: sqlite3.Cursor

    def __init__(self, path: str) -> None:
        logging.debug('Initiated database connection')

        self.__connection = sqlite3.connect(path)
        self.__cursor = self.__connection.cursor()

    def save(self, softwareList: Optional[list[SoftwareLifecycle]] = None, hardwareList: Optional[list[HardwareLifecycle]] = None) -> bool:
        logging.debug('Initiating database recreation')

        softwareCount: int = 0
        hardwareCount: int = 0

        if (softwareList is None):
            logging.debug(
                'Provided software list is empty. Leaving the database as is.')
            return False
        else:
            newSoftwareTableCreated: bool = self.__recreate_software_table()
            if (newSoftwareTableCreated is False):
                logging.debug(
                    'Could not update the data. Leaving the database as is.')
                return False
            else:
                softwareCount: int = len(softwareList)
                for software in softwareList:
                    try:
                        softwareCmd: str = "INSERT INTO software VALUES (?, ?, ?)"
                        softwareArgs: tuple[str, str, str] = (
                            software.name, software.version, software.eol)
                        self.__cursor.execute(softwareCmd, softwareArgs)
                    except Exception as e:
                        raise SystemExit(str(e))

                self.__connection.commit()
                logging.debug('Updated software table succesfully')

        if (hardwareList is None):
            logging.debug(
                'Provided hardware list is empty. Leaving the database as is.')
            return False
        else:
            newHardwareTableCreated: bool = self.__recreate_hardware_table()
            if (newHardwareTableCreated is False):
                logging.debug(
                    'Could not update the data. Leaving the database as is.')
                return False
            else:
                hardwareCount: int = len(hardwareList)

                for hardware in hardwareList:
                    try:
                        hardwareCmd: str = "INSERT INTO hardware VALUES (?, ?, ?)"
                        hardwareArgs: tuple[str, str, str] = (
                            hardware.manufacturer, hardware.model, hardware.eol)
                        self.__cursor.execute(hardwareCmd, hardwareArgs)
                    except Exception as e:
                        raise SystemExit(str(e))

                self.__connection.commit()
                logging.debug('Updated hardware table succesfully')

        return True

    def search_software(self, softwareName: str) -> Optional[list[SoftwareLifecycle]]:

        logging.debug(
            'Searching for keyword ''%s'' in software list', softwareName)

        cmd: str = "SELECT * FROM software WHERE name LIKE ?"
        args: str = '%' + softwareName + '%'
        self.__cursor.execute(cmd, (args,))

        rows: list = self.__cursor.fetchall()
        if (len(rows) == 0):
            logging.debug('Could not find a software matching the keyword')
            return None
        else:
            eolSoftwareList: list[SoftwareLifecycle] = []
            for row in rows:
                eolSoftware: SoftwareLifecycle = SoftwareLifecycle(name=row[0])
                eolSoftware.version = row[1]
                eolSoftware.eol = row[2]
                eolSoftwareList.append(eolSoftware)

            logging.debug('Found %s records matching the keyword',
                          str(len(eolSoftwareList)))

            return eolSoftwareList

    def search_hardware(self, hardwareName: str) -> Optional[list[HardwareLifecycle]]:

        logging.debug(
            'Searching for keyword ''%s'' in hardware list', hardwareName)

        cmd: str = "SELECT * FROM hardware WHERE manufacturer LIKE ? OR model LIKE ?"
        args: str = '%' + hardwareName + '%'
        self.__cursor.execute(cmd, (args, args,))

        rows: list = self.__cursor.fetchall()
        if (len(rows) == 0):
            logging.debug('Could not find a hardware matching the keyword')
            return None
        else:
            eolHardwareList: list[HardwareLifecycle] = []
            for row in rows:
                eolHardware: HardwareLifecycle = HardwareLifecycle(
                    manufacturer=row[0], model=row[1], eol=row[2])
                eolHardwareList.append(eolHardware)

            logging.debug('Found %s records matching the keyword',
                          str(len(eolHardwareList)))

            return eolHardwareList

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

        except Exception as e:
            logging.error(str(e))
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

        except Exception as e:
            logging.error(str(e))
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
        else:
            logging.debug('Table %s does not exist', table)
            return False
