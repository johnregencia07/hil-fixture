"""Pass/fail limits live in limits.yaml, not in test code (as on a production line)."""
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Limit:
    low: float
    high: float
    unit: str = ""


def load_limits(path) -> dict:
    data = yaml.safe_load(Path(path).read_text())
    return {
        name: Limit(float(v["low"]), float(v["high"]), v.get("unit", ""))
        for name, v in data.items()
    }
