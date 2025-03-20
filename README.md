# Check-M.A.T.E
<p align="center">
  <img src="assets/logo.png" alt="Check-M.A.T.E Logo">
</p>
<p align="center">
  <span style="font-size:1.2em;"><em>A mechanically articulated table-top experience</em></span>
</p>

## Overview

Check-M.A.T.E is an automated chessboard that bridges the gap between online and physical chess. It is a system control and user interface solution designed to run on a Raspberry Pi 4B. This project integrates hardware monitoring and control with an intuitive UI for seamless interaction.

## Features

- Custom UI interface for system monitoring
- Real-time control of connected systems
- Data visualization capabilities
- Raspberry Pi 4B integration

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/CHECKMATE.git

# Navigate to project directory
cd CHECKMATE

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. Connect your Raspberry Pi 4B to required peripherals
2. Run the main application:
   ```bash
   python main.py
   ```
3. Access the UI through the connected display 

### Project Structure
```
CHECKMATE/
├── assets/         # Images/figures
├── bin/            # Executables
├── inc/            # Headers
├── scripts/        # Application
├── src/            # Source cde
└── test/           # Unit tests
└── main.py         # Entry Point
```

## Building the Firmware

The project includes C firmware for interfacing with a custom sense PCB.

### Prerequisites
- GCC compiler
- pigpio library (`sudo apt-get install pigpio`)

### Compiling the Firmware
To build simply run
```bash
make # binary file located in build/hall_firmware.bin
```
And to clean the build run
```bash
make clean
```
Once verified replace the binary file in the bin/ directory with the up-to-date version.

### Prerequisites
- Raspberry Pi 4B
- Python 3.7+
- Check-M.A.T.E Sense PCB

