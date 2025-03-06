#ifndef MUX_H
#define MUX_H

#include <stdint.h>

#define MUX_S0 1
#define MUX_S1 2
#define MUX_S2 3
#define MUX_S3 

// Map the multiplexer output pins to digital GPIO numbers.
#define MUX_Y_1 26   // Digital input on GPIO26
#define MUX_Y_2 27   // Digital input on GPIO27
#define MUX_Y_3 28   // Digital input on GPIO28
#define MUX_Y_4 29   // Optional digital input if available

void mux_set_pins(char nibble);
uint8_t mux_get_output(void);

#endif