from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class HardwareLifecycle:
    """A validated hardware lifecycle record."""

    manufacturer: str
    model: str
    eol: str

    def __post_init__(self) -> None:
        if not self.manufacturer.strip():
            raise ValueError("Hardware manufacturer must not be empty")
        if not self.model.strip():
            raise ValueError("Hardware model must not be empty")
        if not self.eol.strip():
            raise ValueError("Hardware EOL value must not be empty")

    def __str__(self) -> str:
        return f"{self.manufacturer}, {self.model}: {self.eol}"

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> HardwareLifecycle:
        """Create a record from normalized or legacy hardware source columns."""
        manufacturer = cls._required_value(values, "manufacturer", "manuf.")
        model = cls._required_value(values, "model")
        raw_eol = cls._optional_value(
            values,
            "end_of_manufacturer_support",
            "end of manufacturer support (some dates may be estimated)",
            "end_of_service_life",
            "end-of-service-life",
        )
        eol = "unknown" if raw_eol.casefold() in {"unknown", "noch unbekannt", "unbekannt"} else raw_eol
        return cls(manufacturer=manufacturer, model=model, eol=eol)

    @staticmethod
    def _required_value(values: Mapping[str, Any], *keys: str) -> str:
        value = HardwareLifecycle._optional_value(values, *keys)
        if value == "unknown":
            raise ValueError(f"Hardware source is missing required field {keys[0]!r}")
        return value

    @staticmethod
    def _optional_value(values: Mapping[str, Any], *keys: str) -> str:
        for key in keys:
            value = values.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return "unknown"
