#ifndef MUX_H
#define MUX_H

#include <stdint.h>
#include <pigpio.h>

#define MUX_S0 6
#define MUX_S1 13
#define MUX_S2 19
#define MUX_S3 5

#define MUX_Y_1 26   
#define MUX_Y_2 22   
#define MUX_Y_3 27   
#define MUX_Y_4 17   

void mux_init(void);
void mux_set_pins(char nibble);
uint8_t mux_get_output(void);

#endif