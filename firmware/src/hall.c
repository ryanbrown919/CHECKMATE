#include "../inc/hall.h"

const uint32_t hall_to_board_mapping[16][8] = {
    /* q1    q2     q3     q4*/
    {3, 5,  2, 3,  5, 0,  5, 4}, /* HALL  7 mapping */
    {3, 4,  3, 3,  4, 0,  4, 4}, /* HALL  3 mapping */
    {2, 4,  3, 2,  4, 1,  4, 5}, /* HALL  2 mapping */
    {2, 5,  2, 2,  5, 1,  5, 5}, /* HALL  6 mapping */
    {0, 4,  3, 0,  4, 3,  4, 7}, /* HALL  0 mapping */
    {0, 5,  2, 0,  5, 3,  5, 7}, /* HALL  4 mapping */
    {1, 5,  2, 1,  5, 2,  5, 6}, /* HALL  5 mapping */
    {1, 4,  3, 1,  4, 2,  4, 6}, /* HALL  1 mapping */
    {2, 6,  1, 2,  6, 1,  6, 5}, /* HALL 10 mapping */
    {3, 6,  1, 3,  6, 0,  6, 4}, /* HALL 11 mapping */
    {3, 7,  0, 3,  7, 0,  7, 4}, /* HALL 15 mapping */
    {2, 7,  0, 2,  7, 1,  7, 5}, /* HALL 14 mapping */
    {0, 6,  1, 0,  6, 3,  6, 7}, /* HALL  8 mapping */
    {1, 6,  1, 1,  6, 2,  6, 6}, /* HALL  9 mapping */
    {1, 7,  0, 1,  7, 2,  7, 6}, /* HALL 13 mapping */
    {0, 7,  0, 0,  7, 3,  7, 7}  /* HALL 12 mapping */
};

void hall_init() {
    gpioInitialise();
    mux_init();
}

uint32_t** hall_get_squares() {
    // Allocate array for 8 row pointers
    uint32_t **board = malloc(8 * sizeof(uint32_t *));
    if (board == NULL)
        return NULL;

    // Allocate each row (8 columns per row)
    for (int i = 0; i < 8; i++) {
        board[i] = malloc(8 * sizeof(uint32_t));
        if (board[i] == NULL) {
            // Free previously allocated rows on failure
            for (int j = 0; j < i; j++)
                free(board[j]);
            free(board);
            return NULL;
        }
        // Optional: initialize row to 0
        for (int j = 0; j < 8; j++)
            board[i][j] = 0;
    }

    // Update board bits based on the digital hall effect signals
    for (int i = 0; i < 16; i++) {
        uint32_t current_gray = i ^ (i >> 1);
        mux_set_pins(current_gray);
        usleep(10);

        uint8_t outputs = mux_get_output();

        // Update board bits based on the digital hall effect signals
        for (uint32_t j = 0; j < 4; j++) {
            uint32_t col = hall_to_board_mapping[i][j * 2];
            uint32_t row = hall_to_board_mapping[i][j * 2 + 1];

            if ((outputs >> j) & 1) {
                board[row][col] = 0;
            } else {
                board[row][col] = 1;
            }
        }
    }
    return board;
}

uint32_t hall_get_square(uint32_t x, uint32_t y) {
    for (uint32_t i = 0; i < 16; i++) {
        for (uint32_t j = 0; j < 4; j++) {
            if (hall_to_board_mapping[i][j * 2] != y || hall_to_board_mapping[i][j * 2 + 1] != x) 
                continue;

            uint32_t current_gray = i ^ (i >> 1);
            mux_set_pins(current_gray);
            usleep(10); 
            uint8_t outputs = mux_get_output();
            return ((outputs >> j) & 1) ? 0 : 1;
        }
    }

    return 0;
}

