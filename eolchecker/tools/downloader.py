from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, Final

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models import HardwareLifecycle, SoftwareLifecycle

logger = logging.getLogger(__name__)


class SourceError(RuntimeError):
    """Raised when an upstream source cannot provide a validated dataset."""


class Downloader:
    """Retrieve and validate lifecycle records from their upstream sources."""

    SOFTWARE_EOL_API: Final[str] = "https://endoflife.date/api/v1"
    HARDWARE_EOL_URL: Final[str] = "https://www.hardwarewartung.com/en"
    HARDWARE_MANUFACTURERS: Final[tuple[str, ...]] = (
        "hp-end-of-life-en",
        "ibm-end-of-life-en",
        "dell-end-of-life-en",
        "fujitsu-end-of-life-en",
        "netapp-end-of-life-en",
        "emc-end-of-life-en",
        "cisco-end-of-life-en",
        "sun-end-of-life-en",
        "hitachi-end-of-life-en",
    )
    _REQUIRED_HARDWARE_COLUMNS: Final[frozenset[str]] = frozenset({"manufacturer", "model"})

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: tuple[float, float] = (5.0, 30.0),
    ) -> None:
        self._session = session or self._new_session()
        self._owns_session = session is None
        self._timeout = timeout

    def __enter__(self) -> Downloader:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def get_eol_software(self) -> list[SoftwareLifecycle]:
        """Retrieve all release cycles from the endoflife.date v1 full-product feed."""
        payload = self._get_json(f"{self.SOFTWARE_EOL_API}/products/full")
        products = payload.get("result")
        if not isinstance(products, list):
            raise SourceError("Software source response does not contain a product result list")

        records: list[SoftwareLifecycle] = []
        for product in products:
            if not isinstance(product, Mapping):
                raise SourceError("Software source contains a non-object product")
            product_name = product.get("name")
            releases = product.get("releases")
            if not isinstance(product_name, str) or not product_name.strip():
                raise SourceError("Software source contains a product without a name")
            if not isinstance(releases, list):
                raise SourceError(f"Software source product {product_name!r} has no release list")
            for release in releases:
                if not isinstance(release, Mapping):
                    raise SourceError(f"Software source product {product_name!r} has an invalid release")
                try:
                    records.append(SoftwareLifecycle.from_v1_release(product_name, release))
                except ValueError as exception:
                    raise SourceError(
                        f"Software source product {product_name!r} contains an invalid release"
                    ) from exception

        if not records:
            raise SourceError("Software source returned no lifecycle records")
        logger.info("Retrieved %s software lifecycle records", len(records))
        return records

    def get_eol_hardware(self) -> list[HardwareLifecycle]:
        """Retrieve lifecycle records from all configured hardware source pages."""
        records: list[HardwareLifecycle] = []
        for manufacturer_path in self.HARDWARE_MANUFACTURERS:
            url = f"{self.HARDWARE_EOL_URL}/{manufacturer_path}"
            page = self._get_response(url).content
            page_records = self._parse_hardware_page(page, url)
            if not page_records:
                raise SourceError(f"Hardware source {url} returned no valid lifecycle records")
            records.extend(page_records)

        if not records:
            raise SourceError("Hardware source returned no lifecycle records")
        logger.info("Retrieved %s hardware lifecycle records", len(records))
        return records

    def html_to_json(self, content: bytes, indent: int | None = None) -> str:
        """Return validated, normalized hardware rows as JSON for compatibility."""
        rows = self._extract_hardware_rows(content, "provided HTML")
        return json.dumps(rows, indent=indent)

    def _get_json(self, url: str) -> Mapping[str, Any]:
        response = self._get_response(url)
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type.casefold():
            raise SourceError(f"Source {url} returned unexpected content type {content_type!r}")
        try:
            payload = response.json()
        except ValueError as exception:
            raise SourceError(f"Source {url} returned invalid JSON") from exception
        if not isinstance(payload, Mapping):
            raise SourceError(f"Source {url} returned a non-object JSON document")
        return payload

    def _get_response(self, url: str) -> requests.Response:
        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exception:
            raise SourceError(f"Could not retrieve source {url}: {exception}") from exception

    def _parse_hardware_page(self, content: bytes, source: str) -> list[HardwareLifecycle]:
        rows = self._extract_hardware_rows(content, source)
        records: list[HardwareLifecycle] = []
        for row in rows:
            try:
                records.append(HardwareLifecycle.from_dict(row))
            except ValueError as exception:
                logger.warning("Skipping invalid hardware row from %s: %s", source, exception)
        return records

    def _extract_hardware_rows(self, content: bytes, source: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(content, "html.parser")
        rows: list[dict[str, str]] = []
        tables = soup.find_all("table")
        if not tables:
            raise SourceError(f"Hardware source {source} contains no tables")

        for table in tables:
            if not isinstance(table, Tag):
                continue
            headers = self._headers_for_table(table)
            if not headers or not self._REQUIRED_HARDWARE_COLUMNS.issubset(headers):
                continue
            for row in table.find_all("tr"):
                if not isinstance(row, Tag):
                    continue
                cells = row.find_all("td", recursive=False)
                if not cells:
                    continue
                if len(cells) != len(headers):
                    logger.warning(
                        "Skipping malformed hardware row from %s: expected %s cells, received %s",
                        source,
                        len(headers),
                        len(cells),
                    )
                    continue
                values = {
                    header: cell.get_text(" ", strip=True)
                    for header, cell in zip(headers, cells, strict=True)
                }
                if any(not values[column] for column in self._REQUIRED_HARDWARE_COLUMNS):
                    logger.warning("Skipping hardware row from %s with blank required values", source)
                    continue
                rows.append(values)

        if not rows:
            raise SourceError(f"Hardware source {source} contains no recognized data rows")
        return rows

    @staticmethod
    def _headers_for_table(table: Tag) -> list[str]:
        header_row = table.find("thead")
        if not isinstance(header_row, Tag):
            return []
        headers = header_row.find_all("th")
        normalized_headers = [
            Downloader._normalize_hardware_header(header.get_text(" ", strip=True))
            for header in headers
        ]
        if not normalized_headers or len(set(normalized_headers)) != len(normalized_headers):
            return []
        return normalized_headers

    @staticmethod
    def _normalize_hardware_header(value: str) -> str:
        normalized = " ".join(value.casefold().split())
        aliases = {
            "manuf.": "manufacturer",
            "manufacturer": "manufacturer",
            "model": "model",
            "end of manufacturer support (some dates may be estimated)": "end_of_manufacturer_support",
            "end-of-service-life": "end_of_service_life",
        }
        return aliases.get(normalized, normalized.replace(" ", "_"))

    @staticmethod
    def _new_session() -> requests.Session:
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            allowed_methods=frozenset({"GET"}),
            status_forcelist=(429, 500, 502, 503, 504),
            backoff_factor=0.5,
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        session = requests.Session()
        session.headers.update({"User-Agent": "eolchecker/0.2.0"})
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session
