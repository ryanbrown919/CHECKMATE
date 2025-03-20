CC = gcc
CFLAGS = -O3
LDFLAGS =
LIBS = -lpigpio 

SRCDIR = src
BUILDDIR = build
TARGET = $(BUILDDIR)/hall_firmware.bin

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