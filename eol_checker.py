import json

import requests


def main() -> None:

    response: requests.Response = requests.get(
        "https://endoflife.date/api/all.json")
    val: bytes = response.content
    products: list[str] = json.loads(val)
    for product in products:
        print(product)


if __name__ == '__main__':
    main()
