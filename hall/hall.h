#ifndef HALL_H
#define HALL_H

#include <stdint.h>

void hall_set_squares(uint8_t* halls);
uint32_t hall_get_square(uint8_t* halls, uint32_t x, uint32_t y);

#endif