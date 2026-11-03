"""Does the fixture itself speak the protocol correctly? Run these first."""
from hil.device import DeviceError
import pytest


def test_ping(dut):
    assert dut.ping()


def test_version_reported(dut):
    assert dut.version().startswith("fw=")


def test_unknown_command_rejected(dut):
    assert dut.raw("BOGUS") == "ERR unknown_cmd"


def test_bad_adc_channel_rejected(dut):
    assert dut.raw("ADC 9") == "ERR bad_channel"


def test_unsafe_pin_rejected(dut):
    assert dut.raw("GPIO 0 1") == "ERR bad_pin"


def test_bad_level_rejected(dut):
    assert dut.raw("GPIO 6 2") == "ERR bad_level"


def test_error_reply_raises(dut):
    with pytest.raises(DeviceError):
        dut.command("ADC 9")
