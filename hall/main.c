#include <stdio.h>
#include <stdint.h>
#include <pigpio.h>
#include <unistd.h>

#include "hall.h"
#include "mux.h"

int main() {
    uint8_t board[8] = {0};
    int count = 0;

    gpioInitialise();
    mux_init();

    while (1) {
        hall_get_squares(board);
        printf("%d\n", count++);
    
        for (int r = 0; r < 8; r++) {
            for (int c = 0; c <= 7; c++) {
                printf("%d ", ((board[r]) & (1 << (7 - c))) >> (7 - c));
            }
            printf("\n");
        }  
    }
    
    return 0;
}


