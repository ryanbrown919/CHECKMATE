#include "mux.h"

void mux_init(void) {
    gpioSetMode(MUX_S0, PI_OUTPUT);
    gpioSetMode(MUX_S1, PI_OUTPUT);
    gpioSetMode(MUX_S2, PI_OUTPUT);
    gpioSetMode(MUX_S3, PI_OUTPUT);

    gpioSetMode(MUX_Y_1, PI_INPUT);
    gpioSetMode(MUX_Y_2, PI_INPUT);
    gpioSetMode(MUX_Y_3, PI_INPUT);
    gpioSetMode(MUX_Y_4, PI_INPUT);
}

void mux_set_pins(char nibble){
    gpioWrite(MUX_S3, (nibble >> 3) & 0x01);
    gpioWrite(MUX_S2, (nibble >> 2) & 0x01);
    gpioWrite(MUX_S1, (nibble >> 1) & 0x01);
    gpioWrite(MUX_S0, (nibble >> 0) & 0x01);

    printf(
        "S3: %d, S2: %d, S1: %d, S0: %d\n",
        (nibble >> 3) & 0x01,
        (nibble >> 2) & 0x01,
        (nibble >> 1) & 0x01,
        (nibble >> 0) & 0x01
    );
}

uint8_t mux_get_output(void){
    uint8_t output = 0;

    if (gpioRead(MUX_Y_1)) { output |= (1U << 0); }
    // if (gpioRead(MUX_Y_2)) { output |= (1U << 1); }
    // if (gpioRead(MUX_Y_3)) { output |= (1U << 2); }
    // if (gpioRead(MUX_Y_4)) { output |= (1U << 3); }

    return output;
}