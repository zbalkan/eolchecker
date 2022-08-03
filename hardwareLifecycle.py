from dataclasses import dataclass
from typing import Any


@dataclass
class HardwareLifecycle:
    manufacturer: str
    model: str
    eos: str

    def __str__(self) -> str:
        return self.manufacturer + " " + self.model + ": " + self.eos

    @staticmethod
    def from_dict(obj: Any) -> 'HardwareLifecycle':
        _manuf: str = str(obj.get("manuf."))
        _model: str = str(obj.get("model"))
        rawEos: str = str(
            obj.get("end of manufacturer support (some dates may be estimated)")).strip()

        if(rawEos == "unknown" or rawEos == "noch unbekannt"):
            formattedEos: str = "unknown"
        else:
            formattedEos: str = rawEos

        _eos: str = formattedEos

        return HardwareLifecycle(_manuf, _model, _eos)

# Example Usage
# jsonstring = json.loads(myjsonstring)
# root = Root.from_dict(jsonstring)
