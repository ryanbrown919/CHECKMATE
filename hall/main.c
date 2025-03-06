#include <stdio.h>
#include <stdint.h>
#include "hall.h"

int main() {
    // Each bit in board[row] represents the status of the column.
    uint8_t board[8] = {0};
    
    hall_set_squares(board);

    // Print the board matrix.
    printf("Board matrix:\n");
    for (uint32_t row = 0; row < 8; row++) {
        for (uint32_t col = 0; col < 8; col++) {
            printf("%d ", (board[row] >> col) & 0x01);
        }
        printf("\n");
    }
    printf("\n");
    
    
    return 0;
}

