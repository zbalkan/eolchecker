from dataclasses import dataclass
from typing import Any


@dataclass
class SoftwareLifecycle:
    name: str
    version: str
    eol: str

    def __init__(self, name: str = '') -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name + ", " + self.version + ": " + self.eol

    @staticmethod
    def from_dict(obj: Any) -> 'SoftwareLifecycle':
        temp: SoftwareLifecycle = SoftwareLifecycle('')
        temp.version = str(obj.get("cycle")).strip()
        temp.eol = str(obj.get("eol")).strip()
        return temp
