"""Software stand-in for the fixture + wired DUT, so the test code runs with no hardware.

It mirrors the firmware's protocol rules (same replies, same check order).
Use --sim --fault <name> to see the tests catch a broken DUT.
"""
import random
import re

from .device import Device
from . import wiring

ALLOWED_PINS = {4, 5, 6, 7, 15, 16, 17, 18}
ALLOWED_ADC = {0, 1}
FAULTS = ("divider", "rc", "loopback")


class SimDevice(Device):
    def __init__(self, fault: str | None = None, seed: int = 1):
        if fault is not None and fault not in FAULTS:
            raise ValueError(f"unknown fault {fault!r}; choose from {FAULTS}")
        self.fault = fault
        self._rng = random.Random(seed)
        self._out = {}  # pin -> driven level

    # -- simulated analogue front end ------------------------------------
    def _adc(self, ch: int) -> int:
        if ch == wiring.DIVIDER_ADC_CH:
            r_top = 22_000 if self.fault == "divider" else 10_000
            mv = 3300 * 10_000 / (r_top + 10_000)
        else:
            driven_high = self._out.get(wiring.RC_DRIVE_PIN, 0) == 1
            if self.fault == "rc":  # open resistor: node never follows the drive pin
                mv = 4
            else:
                mv = 1650 if driven_high else 4
        mv += self._rng.randint(-3, 3)
        return max(0, int(mv))

    def _read_pin(self, pin: int) -> int:
        if pin == wiring.LOOPBACK_IN_PIN:
            if self.fault == "loopback":
                return 0  # jumper missing
            return self._out.get(wiring.LOOPBACK_OUT_PIN, 0)
        return self._out.get(pin, 0)

    # -- protocol (mirrors firmware/main/protocol.c) ---------------------
    @staticmethod
    def _int(s: str):
        # Same rules as the C parser: optional sign, ASCII digits only, must fit in int32.
        if not re.fullmatch(r"[+-]?[0-9]+", s):
            return None
        v = int(s)
        return v if -2**31 <= v < 2**31 else None

    def raw(self, line: str) -> str:
        tok = line.split()
        if len(tok) > 4:
            return "ERR bad_args"
        if not tok:
            return "ERR empty"
        cmd, args = tok[0], tok[1:]

        if cmd == "PING":
            return "OK PONG" if not args else "ERR bad_args"
        if cmd == "VER":
            return "OK fw=0.1.0" if not args else "ERR bad_args"
        if cmd == "ADC":
            ch = self._int(args[0]) if len(args) == 1 else None
            if ch is None:
                return "ERR bad_args"
            if ch not in ALLOWED_ADC:
                return "ERR bad_channel"
            return f"OK {self._adc(ch)}"
        if cmd == "GPIO":
            pin = self._int(args[0]) if len(args) == 2 else None
            level = self._int(args[1]) if len(args) == 2 else None
            if pin is None or level is None:
                return "ERR bad_args"
            if pin not in ALLOWED_PINS:
                return "ERR bad_pin"
            if level not in (0, 1):
                return "ERR bad_level"
            self._out[pin] = level
            return "OK"
        if cmd == "READ":
            pin = self._int(args[0]) if len(args) == 1 else None
            if pin is None:
                return "ERR bad_args"
            if pin not in ALLOWED_PINS:
                return "ERR bad_pin"
            return f"OK {self._read_pin(pin)}"
        return "ERR unknown_cmd"
