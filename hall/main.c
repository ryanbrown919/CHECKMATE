#include <stdio.h>
#include <stdint.h>
#include <pigpio.h>
#include <unistd.h>

#include "hall.h"
#include "mux.h"

int main() {
    uint8_t board[8] = {0};

    gpioInitialise();
    mux_init();

    while (1) {
        hall_get_squares(board);
        for (int i = 0; i < 8; i++) {
            printf("%d: %d\n", i, board[i]);
        }
        fflush(stdout);
        usleep(10000);
    }
    
    return 0;
}


