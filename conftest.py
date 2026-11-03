import pytest

from hil.device import SerialDevice
from hil.limits import load_limits
from hil.report import Checker, Report
from hil.sim import FAULTS, SimDevice


def pytest_addoption(parser):
    g = parser.getgroup("hil", "hardware-in-the-loop fixture")
    g.addoption("--port", default=None, help="serial port of the ESP32-S3, e.g. /dev/ttyUSB0 or COM5")
    g.addoption("--baud", type=int, default=115200)
    g.addoption("--sim", action="store_true", help="use the software simulator (no hardware)")
    g.addoption("--fault", choices=FAULTS, default=None, help="with --sim: inject a DUT fault")
    g.addoption("--serial", default="UNIT-0001", help="serial number of the unit under test")
    g.addoption("--limits", default="limits.yaml")
    g.addoption("--report-dir", default="reports")


def pytest_configure(config):
    if not config.getoption("--sim") and not config.getoption("--port"):
        raise pytest.UsageError("give --port <serial port> or --sim")
    if config.getoption("--fault") and not config.getoption("--sim"):
        raise pytest.UsageError("--fault only works with --sim")


@pytest.fixture(scope="session")
def dut(request):
    cfg = request.config
    device = SimDevice(fault=cfg.getoption("--fault")) if cfg.getoption("--sim") \
        else SerialDevice(cfg.getoption("--port"), cfg.getoption("--baud"))
    yield device
    device.close()


@pytest.fixture(scope="session")
def report(request):
    rep = Report(request.config.getoption("--serial"))
    yield rep
    path = rep.write_csv(request.config.getoption("--report-dir"))
    tr = request.config.pluginmanager.get_plugin("terminalreporter")
    msg = f"unit {rep.serial}: {'PASS' if rep.passed else 'FAIL'} -> {path}"
    if tr:
        tr.write_line(msg)
    else:
        print(msg)


@pytest.fixture(scope="session")
def limits(request):
    return load_limits(request.config.getoption("--limits"))


@pytest.fixture
def check(limits, report):
    return Checker(limits, report)
