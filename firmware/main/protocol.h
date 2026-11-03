#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stddef.h>

/* Longest accepted command line (without newline) and longest reply. */
#define PROTOCOL_MAX_LINE 64

/* Hardware access is injected so the parser can be unit-tested on a PC.
 * Each function returns 0 on success, non-zero on a hardware fault. */
typedef struct {
    int (*adc_read_mv)(int ch, int *mv);
    int (*gpio_write)(int pin, int level);
    int (*gpio_read)(int pin, int *level);
} protocol_hal_t;

int protocol_pin_allowed(int pin);
int protocol_adc_channel_allowed(int ch);

/* Parse one command line (no trailing newline) and write one reply line
 * (no trailing newline) into out. Always writes something. */
void protocol_handle_line(const protocol_hal_t *hal, const char *line,
                          char *out, size_t out_len);

#endif
