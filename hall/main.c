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
    
        for (int r = 0; r < 8; r++) {
            if (r == 4) {
                printf("\n");
            }

            for (int c = 0; c < 8; c++) {
                if (c == 4) {
                    printf(" ");
                }

                printf("%d ", (board[r] >> (7 - c)) & 1);
            }
            printf("\n");
        }  
        printf("\n");
    }
    
    return 0;
}


