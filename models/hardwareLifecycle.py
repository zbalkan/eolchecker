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
        rawEol: str = str(
            obj.get("end of manufacturer support (some dates may be estimated)")).strip()
        if(rawEol == "" or rawEol == 'None'):
            rawEol: str = str(obj.get("end-of-service-life")).strip()

        if(rawEol == "unknown" or rawEol == "noch unbekannt" or rawEol == "unbekannt"):
            formattedEol: str = "unknown"
        else:
            formattedEol: str = rawEol

        _eol: str = formattedEol

        return HardwareLifecycle(_manuf, _model, _eol)
