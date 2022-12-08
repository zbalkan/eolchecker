from dataclasses import dataclass
from typing import Any


@dataclass
class HardwareLifecycle:
    manufacturer: str
    model: str
    eol: str

    def __str__(self) -> str:
        return self.manufacturer + ", " + self.model + ": " + self.eol

    @staticmethod
    def from_dict(obj: Any) -> 'HardwareLifecycle':
        _manuf: str = str(obj.get("manuf.")).strip()
        _model: str = str(obj.get("model")).strip()
        raw_eol: str = str(
            obj.get("end of manufacturer support (some dates may be estimated)")).strip()
        if(raw_eol == "" or raw_eol == 'None'):
            raw_eol = str(obj.get("end-of-service-life")).strip()

        if(raw_eol == "unknown" or raw_eol == "noch unbekannt" or raw_eol == "unbekannt"):
            formatted_eol: str = "unknown"
        else:
            formatted_eol = raw_eol

        _eol: str = formatted_eol

        return HardwareLifecycle(_manuf, _model, _eol)
