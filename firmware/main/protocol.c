#include "protocol.h"

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FW_VERSION "0.1.0"
#define MAX_TOKENS 4

/* Digital pins the host may drive/read. Avoids strapping, USB and flash pins. */
static const int k_allowed_pins[] = {4, 5, 6, 7, 15, 16, 17, 18};

int protocol_pin_allowed(int pin)
{
    for (size_t i = 0; i < sizeof k_allowed_pins / sizeof k_allowed_pins[0]; i++) {
        if (k_allowed_pins[i] == pin) {
            return 1;
        }
    }
    return 0;
}

/* ADC1 channel 0 = GPIO1, channel 1 = GPIO2 on the ESP32-S3. */
int protocol_adc_channel_allowed(int ch)
{
    return ch == 0 || ch == 1;
}

static int parse_int(const char *s, int *out)
{
    char *end;
    errno = 0;
    long v = strtol(s, &end, 10);
    if (errno != 0 || end == s || *end != '\0' || v < INT_MIN || v > INT_MAX) {
        return 0;
    }
    *out = (int)v;
    return 1;
}

/* Split on spaces/tabs. Returns token count, or -1 if too many/too long. */
static int split(const char *line, char tok[MAX_TOKENS][PROTOCOL_MAX_LINE])
{
    int n = 0;
    const char *p = line;
    while (*p) {
        while (*p == ' ' || *p == '\t') {
            p++;
        }
        if (!*p) {
            break;
        }
        if (n == MAX_TOKENS) {
            return -1;
        }
        size_t len = 0;
        while (p[len] && p[len] != ' ' && p[len] != '\t') {
            len++;
        }
        if (len >= PROTOCOL_MAX_LINE) {
            return -1;
        }
        memcpy(tok[n], p, len);
        tok[n][len] = '\0';
        n++;
        p += len;
    }
    return n;
}

void protocol_handle_line(const protocol_hal_t *hal, const char *line,
                          char *out, size_t out_len)
{
    char tok[MAX_TOKENS][PROTOCOL_MAX_LINE];
    int n = split(line, tok);

    if (n < 0) {
        snprintf(out, out_len, "ERR bad_args");
        return;
    }
    if (n == 0) {
        snprintf(out, out_len, "ERR empty");
        return;
    }

    const char *cmd = tok[0];

    if (strcmp(cmd, "PING") == 0) {
        if (n != 1) { snprintf(out, out_len, "ERR bad_args"); return; }
        snprintf(out, out_len, "OK PONG");
        return;
    }

    if (strcmp(cmd, "VER") == 0) {
        if (n != 1) { snprintf(out, out_len, "ERR bad_args"); return; }
        snprintf(out, out_len, "OK fw=" FW_VERSION);
        return;
    }

    if (strcmp(cmd, "ADC") == 0) {
        int ch, mv;
        if (n != 2 || !parse_int(tok[1], &ch)) { snprintf(out, out_len, "ERR bad_args"); return; }
        if (!protocol_adc_channel_allowed(ch)) { snprintf(out, out_len, "ERR bad_channel"); return; }
        if (hal->adc_read_mv(ch, &mv) != 0) { snprintf(out, out_len, "ERR hw_fault"); return; }
        snprintf(out, out_len, "OK %d", mv);
        return;
    }

    if (strcmp(cmd, "GPIO") == 0) {
        int pin, level;
        if (n != 3 || !parse_int(tok[1], &pin) || !parse_int(tok[2], &level)) {
            snprintf(out, out_len, "ERR bad_args");
            return;
        }
        if (!protocol_pin_allowed(pin)) { snprintf(out, out_len, "ERR bad_pin"); return; }
        if (level != 0 && level != 1) { snprintf(out, out_len, "ERR bad_level"); return; }
        if (hal->gpio_write(pin, level) != 0) { snprintf(out, out_len, "ERR hw_fault"); return; }
        snprintf(out, out_len, "OK");
        return;
    }

    if (strcmp(cmd, "READ") == 0) {
        int pin, level;
        if (n != 2 || !parse_int(tok[1], &pin)) { snprintf(out, out_len, "ERR bad_args"); return; }
        if (!protocol_pin_allowed(pin)) { snprintf(out, out_len, "ERR bad_pin"); return; }
        if (hal->gpio_read(pin, &level) != 0) { snprintf(out, out_len, "ERR hw_fault"); return; }
        snprintf(out, out_len, "OK %d", level);
        return;
    }

    snprintf(out, out_len, "ERR unknown_cmd");
}
