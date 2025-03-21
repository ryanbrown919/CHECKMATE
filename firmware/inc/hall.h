#ifndef HALL_H
#define HALL_H

#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>

#include "mux.h"

uint32_t** hall_get_squares(void);
uint32_t hall_get_square(uint32_t x, uint32_t y);

#endif