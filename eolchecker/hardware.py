import requests
from bs4 import BeautifulSoup
from db import Database


class HardwareUpdater:
    BASE_URL = "https://www.hardwarewartung.com/en/"

    def __init__(self, db: Database) -> None:
        self.db = db

    def update(self) -> None:
        self.db.clear_table("hardware")

        page = requests.get(self.BASE_URL, timeout=15)
        soup = BeautifulSoup(page.content, "html.parser")

        parent_menu = next(
            (
                li for li in soup.find_all("li", class_="fusion-dropdown-menu")
                if (label := li.find("span", class_="menu-text")) and "End of Life" in label.get_text(strip=True)
            ),
            None
        )

        if not parent_menu:
            return

        submenu = parent_menu.find("ul", class_="sub-menu")
        if not submenu:
            return

        vendors = [(a.get_text(strip=True), a["href"])
                   for a in submenu.find_all("a", href=True)]

        all_values: list[list] = []

        for vendor, url in vendors:
            try:
                page = requests.get(url, timeout=15)
                vendor_soup = BeautifulSoup(page.content, "html.parser")
                rows = vendor_soup.find_all("tr")
                headers = [th.get_text(strip=True).lower()
                           for th in vendor_soup.find_all("th")]

                for row in rows:
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) == len(headers):
                        data = dict(zip(headers, cells))
                        all_values.append([
                            vendor,
                            data.get("model"),
                            data.get("end of manufacturer support (some dates may be estimated)") or data.get(
                                "end-of-service-life"),
                        ])
            except Exception:
                continue

        if all_values:
            self.db.insert_many("hardware", all_values)
