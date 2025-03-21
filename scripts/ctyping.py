import ctypes
from pathlib import Path

lib_path = Path(__file__).parent / "hall_firmware.so"
print(f"Resolved path: {lib_path.resolve()}")

assert lib_path.exists(), f"{lib_path} does not exist!"

try:
    firmware = ctypes.CDLL(str(lib_path.resolve()), mode=ctypes.RTLD_GLOBAL)
    print("Shared library loaded successfully!")
except OSError as e:
    print(f"Failed to load shared library: {e}")
