#include <stdio.h>
#include <stdint.h>
#include <pigpio.h>
#include <unistd.h>

#include "mux.h"

int main() {
    gpioInitialise();

    while (1) {
        for (int i = 0; i < 16; i++) {
            uint32_t current_gray = i ^ (i >> 1);
            mux_set_pins(current_gray);
            usleep(10000);
        }
    }
    
    return 0;
}

