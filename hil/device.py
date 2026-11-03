"""Transport layer for the fixture's line protocol.

Host sends "CMD args\\n"; the fixture replies with one line starting with
"OK" or "ERR". Any other line (e.g. ROM boot text) is ignored.
"""
import time


class DeviceError(Exception):
    """The fixture replied ERR (or something unusable)."""


class DeviceTimeout(DeviceError):
    """No OK/ERR reply arrived in time."""


class Device:
    """Base class: subclasses implement raw()."""

    def raw(self, line: str) -> str:
        """Send one command, return the full reply line ("OK ..." / "ERR ...")."""
        raise NotImplementedError

    def command(self, line: str) -> str:
        reply = self.raw(line)
        if reply == "OK" or reply.startswith("OK "):
            return reply[2:].strip()
        raise DeviceError(f"{line!r} -> {reply!r}")

    def ping(self) -> bool:
        return self.command("PING") == "PONG"

    def version(self) -> str:
        return self.command("VER")

    def adc_mv(self, ch: int) -> int:
        return int(self.command(f"ADC {ch}"))

    def gpio_write(self, pin: int, level: int) -> None:
        self.command(f"GPIO {pin} {int(level)}")

    def gpio_read(self, pin: int) -> int:
        return int(self.command(f"READ {pin}"))

    def close(self) -> None:
        pass


class SerialDevice(Device):
    def __init__(self, port: str, baud: int = 115200, timeout: float = 1.0):
        import serial  # imported here so --sim works without pyserial

        self._timeout = timeout
        self._ser = serial.Serial(port, baud, timeout=0.05)
        self._sync()

    def _sync(self, attempts: int = 10) -> None:
        """Opening the port resets many dev boards; wait for it to answer PING."""
        time.sleep(1.5) 
        self._ser.reset_input_buffer()
        for _ in range(attempts):
            try:
                if self.ping():
                    return
            except DeviceError:
                pass
            time.sleep(0.3)
        raise DeviceTimeout("fixture did not answer PING after reset")

    def raw(self, line: str) -> str:
        self._ser.write((line + "\n").encode("ascii"))
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            data = self._ser.readline()
            if not data:
                continue
            text = data.decode("ascii", errors="replace").strip()
            if text.startswith("OK") or text.startswith("ERR"):
                return text
        raise DeviceTimeout(f"no reply to {line!r} within {self._timeout}s")

    def close(self) -> None:
        self._ser.close()
