#include "mux.h"

void mux_set_pins(char nibble){
    // gpio_put(MUX_S0, (nibble >> 3) & 0x01);
    // gpio_put(MUX_S1, (nibble >> 2) & 0x01);
    // gpio_put(MUX_S2, (nibble >> 1) & 0x01);
    // gpio_put(MUX_S3, (nibble >> 0) & 0x01);
}

uint8_t mux_get_output(void){
    uint8_t output = 0;
    // Read digital inputs for channels corresponding to the multiplexer outputs.
    // if (gpio_get(MUX_Y_1)) { output |= (1U << 0); }
    // if (gpio_get(MUX_Y_2)) { output |= (1U << 1); }
    // if (gpio_get(MUX_Y_3)) { output |= (1U << 2); }
    // If using a fourth channel (MUX_Y_4), read it similarly.
    
    return output;
}