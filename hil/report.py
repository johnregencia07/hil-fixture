"""Per-unit test report: every limit check is recorded, then written as CSV."""
import csv
import datetime
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Result:
    test: str
    value: float
    unit: str
    low: float
    high: float
    passed: bool


class Report:
    def __init__(self, serial: str):
        self.serial = serial
        self.started = datetime.datetime.now()
        self.results: list[Result] = []

    def add(self, result: Result) -> None:
        self.results.append(result)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    def write_csv(self, directory) -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        stamp = self.started.strftime("%Y%m%d-%H%M%S")
        path = directory / f"{self.serial}_{stamp}.csv"
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "serial", "test", "value", "unit", "low", "high", "result"])
            for r in self.results:
                w.writerow([
                    self.started.isoformat(timespec="seconds"), self.serial, r.test,
                    r.value, r.unit, r.low, r.high, "PASS" if r.passed else "FAIL",
                ])
        return path


class Checker:
    """check("name", value): record against the named limit, assert it is inside."""

    def __init__(self, limits: dict, report: Report):
        self._limits = limits
        self._report = report

    def __call__(self, name: str, value: float) -> None:
        limit = self._limits[name]
        ok = limit.low <= value <= limit.high
        self._report.add(Result(name, value, limit.unit, limit.low, limit.high, ok))
        assert ok, f"{name}: {value}{limit.unit} outside [{limit.low}, {limit.high}]{limit.unit}"
