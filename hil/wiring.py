"""Single source of truth for how the device under test is wired to the fixture.

Divider : 3V3 -- 10k -- [node A = GPIO1 / ADC ch0] -- 10k -- GND
RC node : GPIO5 -- 10k -- [node B = GPIO2 / ADC ch1];
          node B -- 10k -- GND;  node B -- 1uF -- GND   (tau ~ 5 ms)
Loopback: jumper GPIO6 <-> GPIO7
"""

DIVIDER_ADC_CH = 0
RC_ADC_CH = 1
RC_DRIVE_PIN = 5
LOOPBACK_OUT_PIN = 6
LOOPBACK_IN_PIN = 7

RC_SETTLE_S = 0.05  # ~10 time constants
