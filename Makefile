CC = gcc
CFLAGS = 
LDFLAGS =
LIBS = -lpigpio 

SRCDIR = src
BUILDDIR = build
TARGET = $(BUILDDIR)/hall_firmware.bin

# Get list of all .c files in SRCDIR.
SRC := $(wildcard $(SRCDIR)/*.c)

# Create object files in BUILDDIR by substituting the directory prefix.
OBJ = $(patsubst $(SRCDIR)/%.c, $(BUILDDIR)/%.o, $(SRC))

all: $(TARGET)

$(TARGET): $(OBJ) | $(BUILDDIR)
	$(CC) $(LDFLAGS) -o $(TARGET) $(OBJ) $(LIBS)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

# Ensure BUILDDIR exists before compiling the source file by using an order-only prerequisite.
$(BUILDDIR)/%.o: $(SRCDIR)/%.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rf $(BUILDDIR)

.PHONY: all clean