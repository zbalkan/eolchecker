from bs4 import BeautifulSoup
from db import Database
from helper import requests_session_with_retries
from requests.models import Response
from requests.sessions import Session


class HardwareUpdater:
    BASE_URL = "https://www.hardwarewartung.com/en/"

    def __init__(self, db: Database) -> None:
        self.db: Database = db
        self.session: Session = requests_session_with_retries()

    def update(self) -> None:
        self.db.clear_table("hardware")

        result: list[list[str]] = self.__download()

        if result:
            self.insert(result)

    def insert(self, vals: list[list[str]]) -> None:
        placeholders = ", ".join(["(?, ?, ?)"] * len(vals))
        query = f"""
            INSERT INTO hardware (id, manufacturer, model, eol)
            SELECT uuid(), v.*
            FROM (VALUES {placeholders}) AS v(manufacturer, model, eol)
            """
        # flatten values for parameters
        flat: list[str] = [item for row in vals for item in row]
        self.db.conn.execute(query, flat)

    def __fetch(self, url: str) -> Response:
        resp: Response = self.session.get(url)
        resp.raise_for_status()
        return resp

    def __download(self) -> list[list[str]]:
        result: list[list[str]] = []

        page = self.__fetch(self.BASE_URL)
        soup = BeautifulSoup(page.content, "html.parser")

        parent_menu = next(
            (
                li for li in soup.find_all("li", class_="fusion-dropdown-menu")
                if (label := li.find("span", class_="menu-text")) and "End of Life" in label.get_text(strip=True)  # type: ignore
            ),
            None
        )

        if not parent_menu:
            return result

        submenu = parent_menu.find("ul", class_="sub-menu")  # type: ignore
        if not submenu:
            return result

        vendors = [
            (a.get_text(strip=True)
                .replace(' End of Life', '')
                .replace('End of Life for ', '')
                .replace('/', '-')
                .lower(),
                a["href"]) for a in submenu.find_all("a", href=True)]

        for vendor, url in vendors:
            print(f'Downloading data for {vendor}')
            try:

                page = self.__fetch(url)
                vendor_soup = BeautifulSoup(page.content, "html.parser")
                rows = vendor_soup.find_all("tr")
                headers = list(dict.fromkeys(
                    th.get_text(strip=True).lower() for th in vendor_soup.find_all("th")
                ))

                for row in rows:
                    cells = row.find_all(["td", "th"])  # type: ignore
                    cell_values = [c.get_text(strip=True) for c in cells]

                    # Only keep rows that look like data rows
                    if len(cell_values) == len(headers) and cells[0].name == "td":  # type: ignore
                        data = dict(zip(headers, cell_values))
                        result.append([
                            str(vendor),
                            str(data.get("model")),
                            str(data.get("end of manufacturer support (some dates may be estimated)") or
                                data.get("end-of-service-life")),
                        ])
            except Exception as ex:
                print(f"Failed for {vendor}: {ex}")
                continue

        return result
