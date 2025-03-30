#ifndef MUX_H
#define MUX_H

#include <stdint.h>
#include <pigpio.h>

#define MUX_S0 6
#define MUX_S1 13
#define MUX_S2 19
#define MUX_S3 26

#define MUX_Y_1 16  
#define MUX_Y_2 12   
#define MUX_Y_3 21   
#define MUX_Y_4 20

void mux_init(void);
void mux_set_pins(char nibble);
uint8_t mux_get_output(void);

#endif