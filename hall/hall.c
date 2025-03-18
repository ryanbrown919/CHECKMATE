#include "hall.h"
#include "mux.h"

const uint32_t hall_to_board_mapping[16][8] = {
    {7 - 5, 7 - 0,  7 - 2, 7 - 3,  7 - 2, 7 - 7,  7 - 5, 7 - 4}, /* HALL  7 mapping */
    {7 - 4, 7 - 0,  7 - 3, 7 - 3,  7 - 3, 7 - 7,  7 - 4, 7 - 4}, /* HALL  3 mapping */
    {7 - 4, 7 - 1,  7 - 3, 7 - 2,  7 - 3, 7 - 6,  7 - 4, 7 - 5}, /* HALL  2 mapping */
    {7 - 5, 7 - 1,  7 - 2, 7 - 2,  7 - 2, 7 - 6,  7 - 5, 7 - 5}, /* HALL  6 mapping */
    {7 - 4, 7 - 3,  7 - 3, 7 - 0,  7 - 3, 7 - 4,  7 - 4, 7 - 7}, /* HALL  0 mapping */
    {7 - 5, 7 - 3,  7 - 2, 7 - 0,  7 - 2, 7 - 4,  7 - 5, 7 - 7}, /* HALL  4 mapping */
    {7 - 5, 7 - 2,  7 - 2, 7 - 1,  7 - 2, 7 - 5,  7 - 5, 7 - 6}, /* HALL  5 mapping */
    {7 - 4, 7 - 2,  7 - 3, 7 - 1,  7 - 3, 7 - 5,  7 - 4, 7 - 6}, /* HALL  1 mapping */
    {7 - 6, 7 - 1,  7 - 1, 7 - 2,  7 - 1, 7 - 6,  7 - 6, 7 - 5}, /* HALL 10 mapping */
    {7 - 6, 7 - 0,  7 - 1, 7 - 3,  7 - 1, 7 - 7,  7 - 6, 7 - 4}, /* HALL 11 mapping */
    {7 - 7, 7 - 0,  7 - 0, 7 - 3,  7 - 0, 7 - 7,  7 - 7, 7 - 4}, /* HALL 15 mapping */
    {7 - 7, 7 - 1,  7 - 0, 7 - 2,  7 - 0, 7 - 6,  7 - 7, 7 - 5}, /* HALL 14 mapping */
    {7 - 6, 7 - 3,  7 - 1, 7 - 0,  7 - 1, 7 - 4,  7 - 6, 7 - 7}, /* HALL  8 mapping */
    {7 - 6, 7 - 2,  7 - 1, 7 - 1,  7 - 1, 7 - 5,  7 - 6, 7 - 6}, /* HALL  9 mapping */
    {7 - 7, 7 - 2,  7 - 0, 7 - 1,  7 - 0, 7 - 5,  7 - 7, 7 - 6}, /* HALL 13 mapping */
    {7 - 7, 7 - 3,  7 - 0, 7 - 0,  7 - 0, 7 - 4,  7 - 7, 7 - 7}  /* HALL 12 mapping */
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

            // if (j == 1 || j == 2 || j == 3) {
            //     continue;
            // }

            uint32_t bit = (outputs >> 0) & 1;
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

