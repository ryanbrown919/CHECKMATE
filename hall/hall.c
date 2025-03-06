#include "hall.h"
#include "mux.h"

const uint32_t hall_to_board_mapping[16][8] = {
    {4, 2, 0, 2, 3, 5, 7, 5}, /* HALL  7 mapping */
    {4, 3, 0, 3, 3, 4, 7, 4}, /* HALL  3 mapping */
    {5, 3, 1, 3, 2, 4, 6, 4}, /* HALL  2 mapping */
    {5, 2, 1, 2, 2, 5, 6, 5}, /* HALL  6 mapping */
    {7, 3, 3, 3, 0, 4, 4, 4}, /* HALL  0 mapping */
    {7, 2, 3, 2, 0, 5, 4, 5}, /* HALL  4 mapping */
    {6, 2, 2, 2, 1, 5, 5, 5}, /* HALL  5 mapping */
    {6, 3, 2, 3, 1, 4, 5, 4}, /* HALL  1 mapping */
    {5, 1, 1, 1, 2, 6, 6, 6}, /* HALL 10 mapping */
    {4, 1, 0, 1, 3, 6, 7, 6}, /* HALL 11 mapping */
    {4, 0, 0, 0, 3, 7, 7, 7}, /* HALL 15 mapping */
    {5, 0, 1, 0, 2, 7, 6, 7}, /* HALL 14 mapping */
    {7, 1, 3, 1, 0, 6, 4, 6}, /* HALL  8 mapping */
    {6, 1, 2, 1, 1, 6, 5, 6}, /* HALL  9 mapping */
    {6, 0, 2, 0, 1, 7, 5, 7}, /* HALL 13 mapping */
    {7, 0, 3, 0, 0, 7, 4, 7}  /* HALL 12 mapping */
};

void hall_get_squares(uint8_t* halls) {
    for (int i = 0; i < 16; i++) {
        uint32_t current_gray = i ^ (i >> 1);
        mux_set_pins(current_gray);
        usleep(10000);

        // Get the digital outputs from the multiplexer.
        uint8_t outputs = mux_get_output();

        // Update board bits based on the digital hall effect signals.
        for (uint32_t j = 0; j < 4; j++) {
            uint32_t col = hall_to_board_mapping[i][j * 2];
            uint32_t row = hall_to_board_mapping[i][j * 2 + 1];

            // halls[row] ^= (1U << col);
            int bit = (outputs >> j) & 0x01;
            if (bit) {
                halls[row] |= (1U << col);
            } else {
                halls[row] &= ~(1U << col);
            }
        }
    }
}

uint32_t hall_get_square(uint8_t* board, uint32_t x, uint32_t y) {
    return ((board[y] >> x) & 1);
}

