/* ESP32-S3 production-test-fixture firmware (ESP-IDF v5.3+).
 * Line protocol over UART0: host sends "CMD args\n", fixture replies one line
 * starting with "OK" or "ERR". See README for the command list and wiring. */

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "protocol.h"

#define HOST_UART UART_NUM_0
#define HOST_BAUD 115200
#define NUM_ADC_CH 2

static adc_oneshot_unit_handle_t s_adc;
static adc_cali_handle_t s_cali[NUM_ADC_CH];
static const adc_channel_t k_adc_chan[NUM_ADC_CH] = {ADC_CHANNEL_0, ADC_CHANNEL_1};
static bool s_is_output[GPIO_NUM_MAX];

static void adc_init(void)
{
    adc_oneshot_unit_init_cfg_t unit_cfg = {.unit_id = ADC_UNIT_1};
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit_cfg, &s_adc));
    
    adc_oneshot_chan_cfg_t chan_cfg = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    for (int i = 0; i < NUM_ADC_CH; i++) {
        ESP_ERROR_CHECK(adc_oneshot_config_channel(s_adc, k_adc_chan[i], &chan_cfg));
        adc_cali_curve_fitting_config_t cali_cfg = {
            .unit_id = ADC_UNIT_1,
            .chan = k_adc_chan[i],
            .atten = ADC_ATTEN_DB_12,
            .bitwidth = ADC_BITWIDTH_DEFAULT,
        };
        ESP_ERROR_CHECK(adc_cali_create_scheme_curve_fitting(&cali_cfg, &s_cali[i]));
    }
}

static int hal_adc_read_mv(int ch, int *mv)
{
    int raw;
    if (adc_oneshot_read(s_adc, k_adc_chan[ch], &raw) != ESP_OK) {
        return 1;
    }
    return adc_cali_raw_to_voltage(s_cali[ch], raw, mv) == ESP_OK ? 0 : 1;
}

static int hal_gpio_write(int pin, int level)
{
    if (!s_is_output[pin]) {
        gpio_reset_pin(pin);
        /* INPUT_OUTPUT so READ on the same pin reflects the real pin level. */
        if (gpio_set_direction(pin, GPIO_MODE_INPUT_OUTPUT) != ESP_OK) {
            return 1;
        }
        s_is_output[pin] = true;
    }
    return gpio_set_level(pin, level) == ESP_OK ? 0 : 1;
}

static int hal_gpio_read(int pin, int *level)
{
    if (!s_is_output[pin]) {
        gpio_reset_pin(pin);
        if (gpio_set_direction(pin, GPIO_MODE_INPUT) != ESP_OK) {
            return 1;
        }
    }
    *level = gpio_get_level(pin);
    return 0;
}

static void send_line(const char *s)
{
    uart_write_bytes(HOST_UART, s, strlen(s));
    uart_write_bytes(HOST_UART, "\n", 1);
}

void app_main(void)
{
    /* Keep the UART clean for the protocol (ROM boot text still appears;
     * the host ignores any line that does not start with OK/ERR). */
    esp_log_level_set("*", ESP_LOG_NONE);

    const uart_config_t uart_cfg = {
        .baud_rate = HOST_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    ESP_ERROR_CHECK(uart_param_config(HOST_UART, &uart_cfg));
    ESP_ERROR_CHECK(uart_driver_install(HOST_UART, 512, 0, 0, NULL, 0));

    adc_init();

    const protocol_hal_t hal = {
        .adc_read_mv = hal_adc_read_mv,
        .gpio_write = hal_gpio_write,
        .gpio_read = hal_gpio_read,
    };

    char line[PROTOCOL_MAX_LINE];
    char out[PROTOCOL_MAX_LINE];
    size_t len = 0;
    bool overflow = false;

    for (;;) {
        uint8_t c;
        if (uart_read_bytes(HOST_UART, &c, 1, pdMS_TO_TICKS(100)) <= 0) {
            continue;
        }
        if (c == '\r' || c == '\n') {
            if (overflow) {
                send_line("ERR line_too_long");
            } else if (len > 0) {
                line[len] = '\0';
                protocol_handle_line(&hal, line, out, sizeof out);
                send_line(out);
            }
            len = 0;
            overflow = false;
        } else if (len < sizeof line - 1) {
            line[len++] = (char)c;
        } else {
            overflow = true;
        }
    }
}
