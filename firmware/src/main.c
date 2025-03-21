#include <stdio.h>
#include <stdint.h>
#include "../inc/hall.h"
#include "../inc/mux.h"

int main() {
    uint8_t board[8][8] = {0};

    gpioInitialise();
    mux_init();

    hall_get_squares(board);

    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            printf("%d ", board[row][col]);
        }
        printf("\n");
    }  
    printf("\n");
    
    return 0;
}


