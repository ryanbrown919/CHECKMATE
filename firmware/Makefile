CC = gcc
CFLAGS = -O3 -fPIC -Wall -Wextra -Werror -std=c11 -D_DEFAULT_SOURCE -D_POSIX_C_SOURCE=200809L
LDFLAGS = -shared
LIBS = -lpigpio # only compatible with pi 4B+

SRCDIR = src
BUILDDIR = build
TARGET = $(BUILDDIR)/hall_firmware.so

SRC := $(wildcard $(SRCDIR)/*.c)
OBJ = $(patsubst $(SRCDIR)/%.c, $(BUILDDIR)/%.o, $(SRC))

all: $(TARGET)

$(TARGET): $(OBJ) | $(BUILDDIR)
	$(CC) $(LDFLAGS) -o $(TARGET) $(OBJ) $(LIBS)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(BUILDDIR)/%.o: $(SRCDIR)/%.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(BUILDDIR)

.PHONY: all clean