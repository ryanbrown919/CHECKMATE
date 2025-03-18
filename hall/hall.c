#include "hall.h"
#include "mux.h"

const uint32_t hall_to_board_mapping[16][8] = {
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  7 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  3 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  2 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  6 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  0 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  4 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  5 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  1 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL 10 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL 11 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL 15 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL 14 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  8 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL  9 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}, /* HALL 13 mapping */
    {0, 1,  2, 3,  4, 5,  6, 7}  /* HALL 12 mapping */
};

void hall_get_squares(uint8_t (*halls)[8]) {
    for (int i = 0; i < 16; i++) {
        uint32_t current_gray = i ^ (i >> 1);
        mux_set_pins(current_gray);
        usleep(10);

        // Get the digital outputs from the multiplexer.
        uint8_t outputs = mux_get_output();

        // Update board bits based on the digital hall effect signals
        for (uint32_t j = 0; j < 4; j++) {
            uint32_t row = hall_to_board_mapping[i][j * 2];
            uint32_t col = hall_to_board_mapping[i][j * 2 + 1];

            uint32_t bit = (outputs >> j) & 1;
            if (bit) {
                halls[row][col] = 0;
            } else {
                halls[row][col] = 1;
            }
        }

        for (int r = 0; r < 8; r++) {
            if (r == 4) {
                printf("\n");
            }

            for (int c = 0; c < 8; c++) {
                if (c == 4) {
                    printf(" ");
                }

                printf("%d ", halls[r][c]);
            }
            printf("\n");
        }  
        printf("\n");
        // usleep(1000000);
    }
}

uint32_t hall_get_square(uint8_t (*halls)[8], uint32_t x, uint32_t y) {
    return halls[7 - y][x];
}

