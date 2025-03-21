import ctypes
from pathlib import Path
import ctypes.util
import os

# Step 1: Ensure pigpio dependency is visible to dynamic linker
pigpio_path = ctypes.util.find_library("pigpio")
if pigpio_path is None:
    raise RuntimeError("libpigpio.so not found. Set LD_LIBRARY_PATH or run ldconfig.")

# Optional: Debug print
print(f"libpigpio found at: {pigpio_path}")

# Step 2: Load your shared library
lib_path = Path(__file__).parent / "hall_firmware.so"
assert lib_path.exists(), f"{lib_path} not found"

# Step 3: Load with RTLD_GLOBAL so dependencies like pigpio can resolve
firmware = ctypes.CDLL(str(lib_path.resolve()), mode=ctypes.RTLD_GLOBAL)

print("Firmware loaded successfully!")