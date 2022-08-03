import sqlite3
from typing import Optional

from hardwareLifecycle import HardwareLifecycle
from softwareLifecycle import SoftwareLifecycle


# TODO: Add ID field for the records
class Database:

    __connection: sqlite3.Connection
    __cursor: sqlite3.Cursor

    def __init__(self, path: str) -> None:
        self.__connection = sqlite3.connect(path)
        self.__cursor = self.__connection.cursor()

    def flush(self, softwareList: Optional[list[SoftwareLifecycle]] = None, hardwareList: Optional[list[HardwareLifecycle]] = None) -> bool:
        committing: bool = False

        newSoftwareTable: bool = self.__recreate_software_table()
        newHardwareTable: bool = self.__recreate_hardware_table()

        if (softwareList is not None and newSoftwareTable):
            for software in softwareList:
                try:
                    softwareCmd: str = "INSERT INTO software VALUES (?, ?, ?, ?, ?, ?)"
                    softwareArgs: tuple[str, str, str, str, str, str] = (
                        software.name, software.cycle, software.cycleShortHand, software.support, software.eol, software.releaseDate)
                    self.__cursor.execute(softwareCmd, softwareArgs)
                    committing: bool = True
                except Exception as e:
                    print(str(e))
                    return False

        if (hardwareList is not None and newHardwareTable):
            for hardware in hardwareList:
                try:
                    hardwareCmd: str = "INSERT INTO hardware VALUES (?, ?, ?)"
                    hardwareArgs: tuple[str, str, str] = (
                        hardware.manufacturer, hardware.model, hardware.eol)
                    self.__cursor.execute(hardwareCmd, hardwareArgs)
                    committing: bool = True
                except Exception as e:
                    print(str(e))
                    return False

        if(committing):
            self.__connection.commit()

        return committing

    def close(self) -> None:
        self.__connection.close()

    def __recreate_software_table(self) -> bool:
        if (self.__table_exists('software')):
            print('Table ''software'' exists. Backing up the table...')
            self.__cursor.execute(
                "ALTER TABLE software RENAME TO software_bak;")

        try:
            self.__cursor.execute(
                '''CREATE TABLE 'software' (name text, cycle text, cycleShorthand text, support text, eol text, releaseDate text)''')

            if (self.__table_exists('software_bak')):
                self.__cursor.execute("DROP TABLE software_bak;")

            print('Updated software table successfully.')
            return True


        except Exception as e:
            print(str(e))
            print('An error occured. Rolling back.')
            if (self.__table_exists('software')):
                self.__cursor.execute("DROP TABLE software;")
            self.__cursor.execute(
                "ALTER TABLE software_bak RENAME TO software;")
            return False

    def __recreate_hardware_table(self) -> bool:
        if (self.__table_exists('hardware')):
            print('Table ''hardware'' exists. Backing up the table...')
            self.__cursor.execute(
                "ALTER TABLE hardware RENAME TO hardware_bak;")

        try:
            self.__cursor.execute(
                '''CREATE TABLE 'hardware' (manufacturer text, model text, eol text)''')

            if (self.__table_exists('hardware_bak')):
                self.__cursor.execute("DROP TABLE hardware_bak;")

            print('Updated hardware table successfully.')
            return True

        except Exception as e:
            print(str(e))
            print('An error occured. Rolling back.')

            if (self.__table_exists('hardware')):
                self.__cursor.execute("DROP TABLE hardware;")

            self.__cursor.execute(
                "ALTER TABLE hardware_bak RENAME TO hardware;")
            return False


    def __table_exists(self, table: str) -> bool:
        cmd : str = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?"
        args : list[str] = [table]
        self.__cursor.execute(cmd, args)
        return self.__cursor.fetchone()[0] == 1
