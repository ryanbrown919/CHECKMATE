#include <stdio.h>
#include <stdint.h>
#include <pigpio.h>
#include <unistd.h>

#include "hall.h"

int main() {
    gpioInitialise();
    uint8_t board[8] = {0};

    while (1) {
        hall_get_squares(board);
        usleep(10000);
    }
    
    return 0;
}

