from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SoftwareLifecycle:
    """A validated software release lifecycle record."""

    name: str
    version: str
    eol: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Software lifecycle name must not be empty")
        if not self.version.strip():
            raise ValueError("Software lifecycle version must not be empty")
        if not self.eol.strip():
            raise ValueError("Software lifecycle EOL value must not be empty")

    def __str__(self) -> str:
        return f"{self.name}, {self.version}: {self.eol}"

    @classmethod
    def from_v1_release(
        cls, product_name: str, release: Mapping[str, Any]
    ) -> SoftwareLifecycle:
        """Create a lifecycle record from an endoflife.date v1 release object."""
        version = str(release.get("name") or release.get("label") or "").strip()
        eol_value = release.get("eolFrom")
        eol = "unknown" if eol_value in (None, "") else str(eol_value).strip()
        return cls(name=product_name.strip(), version=version, eol=eol)
