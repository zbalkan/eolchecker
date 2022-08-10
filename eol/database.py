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

    def save(self, softwareList: Optional[list[SoftwareLifecycle]] = None, hardwareList: Optional[list[HardwareLifecycle]] = None) -> bool:

        newSoftwareTable: bool = self.__recreate_software_table()
        newHardwareTable: bool = self.__recreate_hardware_table()

        softwareCount: int = 0
        hardwareCount: int = 0

        if (softwareList is not None and newSoftwareTable):
            softwareCount: int = len(softwareList)
            for software in softwareList:
                try:
                    softwareCmd: str = "INSERT INTO software VALUES (?, ?, ?, ?, ?, ?)"
                    softwareArgs: tuple[str, str, str, str, str, str] = (
                        software.name, software.cycle, software.cycleShortHand, software.support, software.eol, software.releaseDate)
                    self.__cursor.execute(softwareCmd, softwareArgs)
                except Exception as e:
                    print(str(e))
                    return False

            self.__connection.commit()

        if (hardwareList is not None and newHardwareTable):
            hardwareCount: int = len(hardwareList)

            for hardware in hardwareList:
                try:
                    hardwareCmd: str = "INSERT INTO hardware VALUES (?, ?, ?)"
                    hardwareArgs: tuple[str, str, str] = (
                        hardware.manufacturer, hardware.model, hardware.eol)
                    self.__cursor.execute(hardwareCmd, hardwareArgs)
                except Exception as e:
                    print(str(e))
                    return False

            self.__connection.commit()

        print('Total ', softwareCount, ' software and ',
              hardwareCount, ' hardware records found.')
        return True

    def search_software(self, softwareName: str) -> Optional[list[SoftwareLifecycle]]:
        cmd: str = "SELECT * FROM software WHERE name LIKE ?"
        args: str = '%' + softwareName + '%'
        self.__cursor.execute(cmd, (args,))

        rows: list = self.__cursor.fetchall()
        if(len(rows) == 0):
            return None
        else:
            eolSoftwareList: list[SoftwareLifecycle] = []
            for row in rows:
                eolSoftware: SoftwareLifecycle = SoftwareLifecycle(name=row[0])
                eolSoftware.cycle = row[1]
                eolSoftware.cycleShortHand = row[2]
                eolSoftware.support = row[3]
                eolSoftware.eol = row[4]
                eolSoftware.releaseDate = row[5]
                eolSoftwareList.append(eolSoftware)

            return eolSoftwareList

    def search_hardware(self, softwareName: str) -> Optional[list[HardwareLifecycle]]:
        cmd: str = "SELECT * FROM hardware WHERE manufacturer LIKE ? OR model LIKE ?"
        args: str = '%' + softwareName + '%'
        self.__cursor.execute(cmd, (args, args,))

        rows: list = self.__cursor.fetchall()
        if(len(rows) == 0):
            return None
        else:
            eolHardwareList: list[HardwareLifecycle] = []
            for row in rows:
                eolHardware: HardwareLifecycle = HardwareLifecycle(
                    manufacturer=row[0], model=row[1], eol=row[2])
                eolHardwareList.append(eolHardware)

            return eolHardwareList

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
        cmd: str = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?"
        args: list[str] = [table]
        self.__cursor.execute(cmd, args)
        return self.__cursor.fetchone()[0] == 1
