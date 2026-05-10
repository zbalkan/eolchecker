import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PACKAGE_DIR = ROOT / "eolchecker"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

if 'tabulate' not in sys.modules:
    tabulate_stub = types.SimpleNamespace(tabulate=lambda *args, **kwargs: "")
    sys.modules['tabulate'] = tabulate_stub
