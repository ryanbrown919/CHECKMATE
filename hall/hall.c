#include "hall.h"
#include "mux.h"

/*
  Hard-coded hall-to-board mapping where for each hall sensor we list
  the global coordinates in the 8x8 as:
    { Q1_row, Q1_col, Q2_row, Q2_col, Q3_row, Q3_col, Q4_row, Q4_col }
  
  Assume each sensor has an original relative 4x4 coordinate (r, c) per quadrant.
  Then apply:
    Q1 (top-right) rotation 90° clockwise:   (c, 3 - r) and offset (4,4)
    Q2 (top-left)  rotation 90° counterclockwise: (3 - c, r) and offset (4,0)
    Q3 (bottom-left) rotation 90° clockwise:    (c, 3 - r) and offset (0,0)
    Q4 (bottom-right) rotation 90° counterclockwise: (3 - c, r) and offset (0,4)
  
  For example, if a sensor’s relative coordinate in every quadrant is defined as:
      Relative coordinate = { r: 1, c: 2 }
  then:
    Q1: global = ( 2 + 4, (3 - 1) + 4 ) = (6, 6)
    Q2: global = ( (3 - 2) + 4, 1 ) = (5, 1)
    Q3: global = ( 2, 3 - 1 ) = (2, 2)
    Q4: global = ( 3 - 2, 1 + 4 ) = (1, 5)
  
  You would then hard-code that sensor’s mapping as:
      { 6, 6, 5, 1, 2, 2, 1, 5 }
  
  Replace these sample values with your actual computed values.
*/  
const uint32_t hall_to_board_mapping[16][8] = {
    // Note: The following rows are sample values computed using the formulas above.
    // For each row, the eight numbers represent:
    //   Q1: (c+4, 3-r+4)
    //   Q2: (3-c+4, r)
    //   Q3: (c, 3-r)
    //   Q4: (3-c, r+4)

    // Example sensor 0 mapping (replace relative (r, c) with the actual ones):
    // If the relative coordinate for sensor 0 is (r, c) = (1, 0) in all quadrants:
    // Q1: (0 + 4, (3 - 1) + 4) = (4, 6)
    // Q2: ((3 - 0) + 4, 1) = (7, 1)
    // Q3: (0, 3 - 1) = (0, 2)
    // Q4: ((3 - 0), 1 + 4) = (3, 5)
    { 4, 6, 7, 1, 0, 2, 3, 5 },

    // Sensor 1 mapping: relative (r, c) = (2, 1)
    // Q1: (1+4, (3-2)+4) = (5, 5)
    // Q2: ((3-1)+4, 2) = (6, 2)
    // Q3: (1, 3-2) = (1, 1)
    // Q4: ((3-1), 2+4) = (2, 6)
    { 5, 5, 6, 2, 1, 1, 2, 6 },

    // Sensor 2 mapping: relative (r, c) = (0, 3)
    // Q1: (3+4, (3-0)+4) = (7, 7)
    // Q2: ((3-3)+4, 0) = (4, 0)
    // Q3: (3, 3-0) = (3, 3)
    // Q4: ((3-3), 0+4) = (0, 4)
    { 7, 7, 4, 0, 3, 3, 0, 4 },

    // ... add the remaining 13 sensor mappings here using your actual relative (r, c) values.
    // Each row has the form: { Q1_row, Q1_col, Q2_row, Q2_col, Q3_row, Q3_col, Q4_row, Q4_col }
    { 5, 3, 6, 3, 1, 5, 2, 7 },
    { 4, 7, 7, 0, 0, 4, 3, 2 },
    { 6, 4, 5, 2, 2, 6, 1, 4 },
    { 7, 5, 4, 2, 3, 7, 0, 6 },
    { 6, 7, 5, 0, 2, 4, 1, 2 },
    { 4, 5, 7, 3, 0, 7, 3, 1 },
    { 5, 1, 6, 6, 1, 0, 2, 3 },
    { 7, 2, 4, 4, 3, 1, 0, 5 },
    { 6, 6, 5, 4, 2, 1, 1, 3 },
    { 5, 7, 6, 0, 1, 4, 2, 2 },
    { 4, 4, 7, 2, 0, 1, 3, 7 },
    { 7, 6, 4, 1, 3, 0, 0, 3 },
    { 6, 0, 5, 5, 2, 2, 1, 7 },
    { 5, 2, 6, 1, 1, 7, 2, 0 }
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

        for (int r = 7; r >= 0; r--) {
            if (r == 3) {
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

