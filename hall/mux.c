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
    gpioWrite(MUX_S0, (nibble >> 0) & 1);
    gpioWrite(MUX_S1, (nibble >> 1) & 1);
    gpioWrite(MUX_S2, (nibble >> 2) & 1);
    gpioWrite(MUX_S3, (nibble >> 3) & 1);
}

uint8_t mux_get_output(void){
    uint8_t output = 0;

    if (gpioRead(MUX_Y_1)) { output |= (1 << 0); }
    if (gpioRead(MUX_Y_2)) { output |= (1 << 1); }
    if (gpioRead(MUX_Y_3)) { output |= (1 << 2); }
    if (gpioRead(MUX_Y_4)) { output |= (1 << 3); }

    return output;
}