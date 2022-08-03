import json

import requests

from softwareLifecycle import SoftwareLifeCycle


class EOLChecker:

    SOFTWARE_EOL_API: str = 'https://endoflife.date'

    eolSoftware: list[SoftwareLifeCycle]

    def __init__(self) -> None:
        self.eolSoftware = self.get_eol_software()

    def get_eol_software(self) -> list[SoftwareLifeCycle]:
        softwareList: list[SoftwareLifeCycle] = []

        softwareListResponse: requests.Response = requests.get(
            self.SOFTWARE_EOL_API + "/api/all.json")
        softwareListJsonString: list[str] = json.loads(softwareListResponse.content)
        for softwareName in softwareListJsonString:
            softwareResponse: requests.Response = requests.get(
                self.SOFTWARE_EOL_API + "/api/" + softwareName + ".json")
            softwareJsonString: list[str] = json.loads(softwareResponse.content)
            for softwareLifecycleJson in softwareJsonString:
                temp: SoftwareLifeCycle = SoftwareLifeCycle.from_dict(softwareLifecycleJson)
                temp.name = softwareName
                softwareList.append(temp)

        return softwareList


def main() -> None:

    checker: EOLChecker = EOLChecker()
    for software in checker.eolSoftware:
        print(software)


if __name__ == '__main__':
    main()
