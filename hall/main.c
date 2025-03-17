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
        // Print the board all in one go
        for (int r = 0; r < 8; r++) {
            for (int c = 7; c >= 0; c--) {  // Assuming bit 7 is the leftmost column
            printf("%d", (board[r] >> c) & 1);
            }
            printf("\n");
        }
        fflush(stdout);
        usleep(10000);
    }
    
    return 0;
}


