import json
from typing import Any, Optional

import bs4
import requests
from bs4 import BeautifulSoup

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
