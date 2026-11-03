# ESP32-S3 Production Test Fixture (prototype)

A small automated test fixture in the style of a factory test jig. An ESP32-S3 runs C
firmware that exposes a simple UART command interface; Python/pytest scripts on a PC drive
it, measure a breadboard device under test (DUT), compare readings against limits in
`limits.yaml`, and write a per-unit CSV report.

```
PC (pytest) --UART--> ESP32-S3 (fixture firmware) --wires--> breadboard DUT
```

## Device under test (wiring)

| Circuit  | Wiring | Expected |
|----------|--------|----------|
| Divider  | 3V3 - 10k - **GPIO1 (ADC ch0)** - 10k - GND | ~1650 mV |
| RC node  | GPIO5 - 10k - **GPIO2 (ADC ch1)**; GPIO2 - 10k - GND; GPIO2 - 1 uF - GND | ~0 mV driven low, ~1650 mV driven high (tau ~5 ms) |
| Loopback | jumper GPIO6 to GPIO7 | GPIO7 follows GPIO6 |

## Command protocol (UART0, 115200 8N1, one line each way)

| Command | Reply |
|---|---|
| `PING` | `OK PONG` |
| `VER` | `OK fw=0.1.0` |
| `ADC <0\|1>` | `OK <millivolts>` (calibrated) |
| `GPIO <pin> <0\|1>` | `OK` (drives pin) |
| `READ <pin>` | `OK <0\|1>` |
| invalid input | `ERR <bad_args\|bad_channel\|bad_pin\|bad_level\|unknown_cmd\|empty\|hw_fault\|line_too_long>` |

Allowed digital pins: 4, 5, 6, 7, 15, 16, 17, 18 (strapping, USB and flash pins are refused).
Commands are uppercase.

## Running the program

```bash
pip install -r requirements.txt

# No hardware: simulator
pytest --sim --serial UNIT-0001

# Prove the tests catch faults (each one should fail exactly one test)
pytest --sim --fault divider
pytest --sim --fault rc
pytest --sim --fault loopback

# Real fixture
cd firmware && idf.py set-target esp32s3 && idf.py build flash && cd ..
pytest --port /dev/ttyUSB0 --serial UNIT-0001      # COM5 on Windows
```

Each run writes `reports/<serial>_<timestamp>.csv`:
`timestamp, serial, test, value, unit, low, high, result`.

Firmware parser unit tests (run on the PC, no board needed):

```bash
cd firmware/test && make
```

## Layout

```
firmware/main/protocol.c   command parser, no hardware dependencies (unit-tested)
firmware/main/main.c       ESP-IDF: UART loop, ADC (calibrated), GPIO
firmware/test/             host-side C tests for the parser
hil/device.py              serial transport + typed helpers (adc_mv, gpio_write, ...)
hil/sim.py                 simulator mirroring the protocol, with fault injection
hil/limits.py, report.py   limits loading, per-unit CSV report
limits.yaml                pass/fail limits (kept out of the test code)
tests/                     protocol, ADC and GPIO tests
```

## Design notes

- **Limits are data, not code.** Changing a tolerance does not touch any test.
- **Hardware is injected into the parser**, so it is tested on a PC without a board.
- **ADC accuracy:** the ESP32-S3 ADC is only good to roughly +/-50-100 mV even calibrated,
  and is poor near 0 V, so limits are sized for the instrument, not the resistors. A
  production fixture would use an external ADC or reference.
- Opening the serial port resets many dev boards, so the host retries `PING` until the
  fixture answers, and ignores any line that is not `OK`/`ERR` (boot text).
- Tests leave the DUT in a safe state (drive pin low) even when a check fails.

## Status

Work in progress.

- Simulator (`pytest --sim`): all tests pass. With `--fault divider` the divider test fails and
  the rest pass; sample reports are in `docs/sample_reports/`.
- Firmware parser unit tests (`firmware/test`, run with `make`): pass on a PC.
- Real hardware: in progress. `firmware/main/main.c` has not been
  verified on a board until this line says so.

Known limitations: the ESP32-S3 ADC accuracy limits the tolerances (see Design notes);
a dropped serial link is not recorded as an ERROR row in the report; one fixture and one DUT
at a time.

## AI acknowledgement

The firmware, the Python host library, the pytest tests and the first draft of this README were generated with AI assistance (Claude, by Anthropic, through Claude Code). The project was created as an exercise in reading and extending embedded C and in learning test automation with Python. AI handled most of the initial programming and boilerplate configuration.