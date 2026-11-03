"""Analogue measurements on the DUT, checked against limits.yaml."""
import time

from hil import wiring


def _mean(values):
    return sum(values) / len(values)


def test_divider_voltage(dut, check):
    samples = [dut.adc_mv(wiring.DIVIDER_ADC_CH) for _ in range(16)]
    check("divider_mv", _mean(samples))


def test_divider_noise(dut, check):
    samples = [dut.adc_mv(wiring.DIVIDER_ADC_CH) for _ in range(16)]
    check("divider_noise_mv", max(samples) - min(samples))


def test_rc_node_low(dut, check):
    dut.gpio_write(wiring.RC_DRIVE_PIN, 0)
    time.sleep(wiring.RC_SETTLE_S)
    check("rc_low_mv", _mean([dut.adc_mv(wiring.RC_ADC_CH) for _ in range(8)]))


def test_rc_node_high(dut, check):
    dut.gpio_write(wiring.RC_DRIVE_PIN, 1)
    time.sleep(wiring.RC_SETTLE_S)
    try:
        check("rc_high_mv", _mean([dut.adc_mv(wiring.RC_ADC_CH) for _ in range(8)]))
    finally:
        dut.gpio_write(wiring.RC_DRIVE_PIN, 0)  # leave the DUT in a safe state
