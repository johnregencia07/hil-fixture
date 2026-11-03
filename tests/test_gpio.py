"""Digital loopback: GPIO6 is jumpered to GPIO7."""
from hil import wiring


def test_loopback_high(dut, check):
    dut.gpio_write(wiring.LOOPBACK_OUT_PIN, 1)
    check("loopback_high", dut.gpio_read(wiring.LOOPBACK_IN_PIN))


def test_loopback_low(dut, check):
    dut.gpio_write(wiring.LOOPBACK_OUT_PIN, 0)
    check("loopback_low", dut.gpio_read(wiring.LOOPBACK_IN_PIN))
