from __future__ import annotations

import json
from typing import Any

import pytest

from eolchecker.models import HardwareLifecycle, SoftwareLifecycle
from eolchecker.tools.downloader import Downloader, SourceError


class FakeResponse:
    def __init__(self, payload: object, content_type: str = "application/json") -> None:
        self._payload = payload
        self.headers = {"Content-Type": content_type}
        self.content = b"unused"

    def json(self) -> object:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.urls: list[str] = []

    def get(self, url: str, timeout: tuple[float, float]) -> FakeResponse:
        self.urls.append(url)
        return self.response


def test_software_download_maps_v1_product_releases() -> None:
    session = FakeSession(
        FakeResponse(
            {
                "schema_version": "1.2.1",
                "result": [
                    {
                        "name": "nginx",
                        "releases": [
                            {"name": "1.26", "eolFrom": "2026-04-23"},
                            {"name": "1.25", "eolFrom": None},
                        ],
                    }
                ],
            }
        )
    )
    downloader = Downloader(session=session)  # type: ignore[arg-type]

    records = downloader.get_eol_software()

    assert session.urls == ["https://endoflife.date/api/v1/products/full"]
    assert records == [
        SoftwareLifecycle(name="nginx", version="1.26", eol="2026-04-23"),
        SoftwareLifecycle(name="nginx", version="1.25", eol="unknown"),
    ]


def test_software_download_rejects_non_json_responses() -> None:
    downloader = Downloader(session=FakeSession(FakeResponse({}, "text/html")))  # type: ignore[arg-type]

    with pytest.raises(SourceError, match="unexpected content type"):
        downloader.get_eol_software()


def test_hardware_parser_skips_short_and_invalid_rows() -> None:
    html = b"""
        <table>
          <thead><tr>
            <th>Manuf.</th><th>Model</th>
            <th>End of manufacturer support (some dates may be estimated)</th>
          </tr></thead>
          <tbody>
            <tr><td>Dell</td><td>PowerEdge R740</td><td>2030-01-01</td></tr>
            <tr><td>Dell</td><td>short row</td></tr>
            <tr><td>Dell</td><td></td><td>2030-01-01</td></tr>
          </tbody>
        </table>
    """
    downloader = Downloader(session=FakeSession(FakeResponse({})))  # type: ignore[arg-type]

    records = downloader._parse_hardware_page(html, "fixture")
    serialized = json.loads(downloader.html_to_json(html))

    assert records == [
        HardwareLifecycle(manufacturer="Dell", model="PowerEdge R740", eol="2030-01-01")
    ]
    assert serialized == [
        {
            "manufacturer": "Dell",
            "model": "PowerEdge R740",
            "end_of_manufacturer_support": "2030-01-01",
        }
    ]


def test_software_download_rejects_products_without_releases() -> None:
    payload: dict[str, Any] = {"result": [{"name": "nginx", "releases": "not-a-list"}]}
    downloader = Downloader(session=FakeSession(FakeResponse(payload)))  # type: ignore[arg-type]

    with pytest.raises(SourceError, match="no release list"):
        downloader.get_eol_software()
