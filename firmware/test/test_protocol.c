/* Host-side unit tests for the command parser (no ESP32 needed). */
#include <stdio.h>
#include <string.h>

#include "protocol.h"

static int g_fail;
static int g_pin_level[64];
static int g_hw_fail;

static int fake_adc(int ch, int *mv) { if (g_hw_fail) return 1; *mv = 1000 + ch; return 0; }
static int fake_write(int pin, int level) { if (g_hw_fail) return 1; g_pin_level[pin] = level; return 0; }
static int fake_read(int pin, int *level) { if (g_hw_fail) return 1; *level = g_pin_level[pin]; return 0; }

static const protocol_hal_t HAL = {fake_adc, fake_write, fake_read};

static void expect(const char *line, const char *want)
{
    char out[PROTOCOL_MAX_LINE];
    protocol_handle_line(&HAL, line, out, sizeof out);
    if (strcmp(out, want) != 0) {
        printf("FAIL: \"%s\" -> \"%s\" (wanted \"%s\")\n", line, out, want);
        g_fail++;
    }
}

int main(void)
{
    expect("PING", "OK PONG");
    expect("VER", "OK fw=0.1.0");
    expect("  PING  ", "OK PONG");
    expect("PING extra", "ERR bad_args");

    expect("ADC 0", "OK 1000");
    expect("ADC 1", "OK 1001");
    expect("ADC 2", "ERR bad_channel");
    expect("ADC -1", "ERR bad_channel");
    expect("ADC x", "ERR bad_args");
    expect("ADC", "ERR bad_args");
    expect("ADC 12abc", "ERR bad_args");
    expect("ADC 4294967296", "ERR bad_args");   /* would wrap to 0 if cast blindly */
    expect("GPIO 4294967300 1", "ERR bad_args"); /* would wrap to pin 4 */

    expect("GPIO 6 1", "OK");
    expect("READ 6", "OK 1");
    expect("GPIO 6 0", "OK");
    expect("READ 6", "OK 0");
    expect("GPIO 0 1", "ERR bad_pin");
    expect("GPIO 6 2", "ERR bad_level");
    expect("GPIO 6", "ERR bad_args");
    expect("READ 99", "ERR bad_pin");

    expect("", "ERR empty");
    expect("BOGUS", "ERR unknown_cmd");
    expect("ping", "ERR unknown_cmd");
    expect("A B C D E", "ERR bad_args");

    g_hw_fail = 1;
    expect("ADC 0", "ERR hw_fault");
    expect("GPIO 6 1", "ERR hw_fault");
    expect("READ 6", "ERR hw_fault");

    if (g_fail == 0) {
        printf("all protocol tests passed\n");
    }
    return g_fail != 0;
}
