#include <stdio.h>
#include <stdint.h>
// #include "pico/stdlib.h"

#define MUX_S0 1
#define MUX_S1 2
#define MUX_S2 3
#define MUX_S3 4

// Map the multiplexer output pins to digital GPIO numbers.
#define MUX_Y_1 26   // Digital input on GPIO26
#define MUX_Y_2 27   // Digital input on GPIO27
#define MUX_Y_3 28   // Digital input on GPIO28
#define MUX_Y_4 29   // Optional digital input if available

// Mapping between the multiplexer and hall sensor positions.
const uint32_t mux_to_hall_mapping[16] = {
    7, 3, 2, 6, 0, 4, 5, 1, 10, 11, 15, 14, 10, 9, 13, 12
};

const uint32_t mux_mapping[16][8] = {
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

// Each bit in board[row] represents the status of the column.
uint8_t board[8] = {0};

void mux_set_pins(int gray_code);
uint8_t mux_get_output(void);

int main() {
    // stdio_init_all();
    
    // Initialize the multiplexer selector GPIO pins here...
    // (Replace with your board-specific initialization code.)
    
    // Initialize digital inputs for the multiplexer outputs.
    // gpio_init(MUX_Y_1);
    // gpio_set_dir(MUX_Y_1, GPIO_IN);
    // gpio_init(MUX_Y_2);
    // gpio_set_dir(MUX_Y_2, GPIO_IN);
    // gpio_init(MUX_Y_3);
    // gpio_set_dir(MUX_Y_3, GPIO_IN);
    // If using a fourth channel, initialize MUX_Y_4 similarly.
    
    for (int i = 0; i < 16; i++) {
        uint32_t current_gray = i ^ (i >> 1);
        mux_set_pins(current_gray);

        // Get the digital outputs from the multiplexer.
        uint8_t outputs = mux_get_output();

        // Update board bits based on the digital hall effect signals.
        for (uint32_t j = 0; j < 4; j++) {
            uint32_t col = mux_mapping[i][j * 2];
            uint32_t row = mux_mapping[i][j * 2 + 1];

            board[row] ^= (1U << col);
            // int bit = (outputs >> j) & 0x01;
            // if (bit) {
            //     board[row] |= (1U << col);
            // } else {
            //     board[row] &= ~(1U << col);
            // }
        }

        // Print the board matrix.
        printf("Board matrix:\n");
        for (uint32_t row = 0; row < 8; row++) {
            for (uint32_t col = 0; col < 8; col++) {
                printf("%d ", (board[row] >> col) & 0x01);
            }
            printf("\n");
        }
        printf("\n");
    }
    
    return 0;
}

void mux_set_pins(int gray_code) {
    // Set the multiplexer control signals using bit extraction.
    // Replace these with your actual digital write code.
    // For example:
    // gpio_put(MUX_S0, (gray_code >> 3) & 0x01);
    // gpio_put(MUX_S1, (gray_code >> 2) & 0x01);
    // gpio_put(MUX_S2, (gray_code >> 1) & 0x01);
    // gpio_put(MUX_S3, (gray_code >> 0) & 0x01);
    printf("Setting MUX pins with gray code: %d\n", gray_code);
}

uint8_t mux_get_output(void) {
    uint8_t output = 0;
    // Read digital inputs for channels corresponding to the multiplexer outputs.
    // if (gpio_get(MUX_Y_1)) { output |= (1U << 0); }
    // if (gpio_get(MUX_Y_2)) { output |= (1U << 1); }
    // if (gpio_get(MUX_Y_3)) { output |= (1U << 2); }
    // If using a fourth channel (MUX_Y_4), read it similarly.
    
    return output;
}