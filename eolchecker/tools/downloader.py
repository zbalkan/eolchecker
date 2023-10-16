import json
import logging
from typing import Any, Final, Optional

import bs4
import requests
from bs4 import BeautifulSoup

from ..models import HardwareLifecycle, SoftwareLifecycle

HtmlElement = Optional[bs4.NavigableString | bs4.Tag]


class Downloader:

    SOFTWARE_EOL_API: Final[str] = 'https://endoflife.date'
    HARDWARE_EOL_URL: Final[str] = "https://www.hardwarewartung.com/en/"
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
        logging.debug('Initiated downloader')

    def get_eol_software(self) -> list[SoftwareLifecycle]:
        software_list: list[SoftwareLifecycle] = []

        logging.debug('Getting software list')

        try:
            software_list_response: requests.Response = requests.get(
                self.SOFTWARE_EOL_API + "/api/all.json", timeout=10)
        except Exception as exception:
            raise SystemExit(str(exception)) from exception

        logging.debug('Getting EOL information for each software')
        software_list_json_string: list[str] = json.loads(
            software_list_response.content)
        for software_name in software_list_json_string:
            logging.debug('Getting EOL information for %s', software_name)
            try:
                software_response: requests.Response = requests.get(
                    self.SOFTWARE_EOL_API + "/api/" + software_name + ".json", timeout=10)
            except Exception as exception:
                raise SystemExit(str(exception)) from exception

            software_json_string: list[str] = json.loads(
                software_response.content)
            for software_lifecycle_json in software_json_string:
                temp: SoftwareLifecycle = SoftwareLifecycle.from_dict(
                    software_lifecycle_json)
                temp.name = software_name
                software_list.append(temp)

        logging.debug('Total %s EOL software records found',
                      str(len(software_list)))

        return software_list

    def get_eol_hardware(self) -> list[HardwareLifecycle]:
        eol_hardware: list[HardwareLifecycle] = []

        logging.debug('Getting hardware list')

        for manufacturer in self.HARDWARE_MANUFACTURERS:

            logging.debug('Getting EOL information for %s', manufacturer)

            try:
                page: requests.Response = requests.get(
                    self.HARDWARE_EOL_URL + '/' + manufacturer, timeout=10)
            except Exception as exception:
                raise SystemExit(str(exception)) from exception

            hardware_list_json: list[str] = json.loads(
                self.html_to_json(page.content, 4))

            for eol_hardware_json in hardware_list_json:
                temp: HardwareLifecycle = HardwareLifecycle.from_dict(
                    eol_hardware_json)
                eol_hardware.append(temp)

        logging.debug('Total %s EOL hardware records found',
                      str(len(eol_hardware)))

        return eol_hardware

    def html_to_json(self, content: bytes, indent: Optional[int] = None) -> str:
        soup: BeautifulSoup = BeautifulSoup(  # type: ignore
            content, "html.parser")  # type: ignore
        rows: bs4.ResultSet[Any] = soup.find_all("tr")  # type: ignore

        headers: dict[str, str] = {}
        thead: HtmlElement = soup.find("thead")  # type: ignore
        if thead:
            thead: HtmlElement = thead.find_all("th")  # type: ignore
            for i, item in enumerate(thead):  # type: ignore
                headers[i] = item.text.strip().lower()  # type: ignore
        data: list[list[str] | dict[str, str]] = []
        for row in rows:
            cells: HtmlElement = row.find_all("td")  # type: ignore
            if thead:
                items_with_headers: dict[str, str] = {}
                if len(cells) > 0:  # type: ignore
                    for index in headers:
                        items_with_headers[headers[index]
                                           ] = cells[index].text  # type: ignore
                if items_with_headers:
                    data.append(items_with_headers)
            else:
                items_without_headers: list[str] = []
                for index in cells:  # type: ignore
                    items_without_headers.append(
                        index.text.strip())  # type: ignore
                if items_without_headers:
                    data.append(items_without_headers)
        return json.dumps(data, indent=indent)
