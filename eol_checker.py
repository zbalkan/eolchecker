import argparse
import json
import sys
from typing import Any, Optional

import bs4
import colorama
import requests
from bs4 import BeautifulSoup

from database import Database
from hardwareLifecycle import HardwareLifecycle
from softwareLifecycle import SoftwareLifecycle

HtmlElement = Optional[bs4.NavigableString | bs4.Tag]


class Downloader:

    SOFTWARE_EOL_API: str = 'https://endoflife.date'
    HARDWARE_EOL_URL: str = "https://www.hardwarewartung.com/en/"
    HARDWARE_MANUFACTURERS: list[str] = [
        'hp-end-of-life-en',
        'ibm-end-of-life-en',
        'dell-end-of-life-en',
        'fujitsu-end-of-life-en',
        'netapp-end-of-life-en',
        'emc-end-of-life-en',
        'cisco-end-of-life-en',
        'sun-end-of-life-en',
        'hitachi-end-of-life-en'
        # 'brocade-end-of-life-en' # Ignore Brocade due to problematic HTML table
    ]

    def __init__(self) -> None:
        pass

    def get_eol_software(self) -> list[SoftwareLifecycle]:
        softwareList: list[SoftwareLifecycle] = []

        softwareListResponse: requests.Response = requests.get(
            self.SOFTWARE_EOL_API + "/api/all.json")
        softwareListJsonString: list[str] = json.loads(
            softwareListResponse.content)
        for softwareName in softwareListJsonString:
            softwareResponse: requests.Response = requests.get(
                self.SOFTWARE_EOL_API + "/api/" + softwareName + ".json")
            softwareJsonString: list[str] = json.loads(
                softwareResponse.content)
            for softwareLifecycleJson in softwareJsonString:
                temp: SoftwareLifecycle = SoftwareLifecycle.from_dict(
                    softwareLifecycleJson)
                temp.name = softwareName
                softwareList.append(temp)

        return softwareList

    def get_eol_hardware(self) -> list[HardwareLifecycle]:
        eolHardware: list[HardwareLifecycle] = []
        for manufacturer in self.HARDWARE_MANUFACTURERS:
            page: requests.Response = requests.get(
                self.HARDWARE_EOL_URL + '/' + manufacturer)
            hardwareListJson: list[str] = json.loads(
                self.html_to_json(page.content, 4))

            for eolHardwareJson in hardwareListJson:
                temp: HardwareLifecycle = HardwareLifecycle.from_dict(
                    eolHardwareJson)
                eolHardware.append(temp)

        return eolHardware

    def html_to_json(self, content: bytes, indent=None) -> str:
        soup: BeautifulSoup = BeautifulSoup(content, "html.parser")
        rows: bs4.ResultSet[Any] = soup.find_all("tr")

        headers: dict[str, str] = {}
        thead: HtmlElement = soup.find("thead")
        if thead:
            thead: HtmlElement = thead.find_all("th")  # type: ignore
            for i in range(len(thead)):  # type: ignore
                headers[i] = thead[i].text.strip().lower()  # type: ignore
        data: list[list[str] | dict[str, str]] = []
        for row in rows:
            cells: HtmlElement = row.find_all("td")
            if thead:
                itemsWithHeaders: dict[str, str] = {}
                if len(cells) > 0:  # type: ignore
                    for index in headers:
                        itemsWithHeaders[headers[index]
                                         ] = cells[index].text  # type: ignore
                if itemsWithHeaders:
                    data.append(itemsWithHeaders)
            else:
                itemsWithoutHeaders: list[str] = []
                for index in cells:  # type: ignore
                    itemsWithoutHeaders.append(index.text.strip())
                if itemsWithoutHeaders:
                    data.append(itemsWithoutHeaders)
        return json.dumps(data, indent=indent)


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
        eolSoftwareList: list[SoftwareLifecycle] | None = database.search_software(
            args.query_software)

        if(eolSoftwareList is None):
            print("No software matches found with keyword.")
        else:
            for eolSoftware in eolSoftwareList:
                print(eolSoftware)

    if(args.query_hardware is not None):
        eolHardwareList: list[HardwareLifecycle] | None = database.search_hardware(
            args.query_hardware)

        if(eolHardwareList is None):
            print("No hardware matches found with keyword.")
        else:
            for eolHardware in eolHardwareList:
                print(eolHardware)

    database.close()


if __name__ == '__main__':
    main()
