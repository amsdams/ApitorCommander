# Apitor Robot Controller (Python)

A simple, modular Python application to control Apitor robots (like Robot X or SuperBot) over Bluetooth Low Energy (BLE).

## Features
- **Modular Design:** Split into a hardware controller (`apitor_robot.py`) and a graphical interface (`apitor_gui.py`).
- **Real-time Sensors:** Displays distance sensor data directly in the GUI.
- **Full Motor Control:** Individual and combined motor controls with adjustable speed.
- **Auto-Handshake:** Handles the mandatory Apitor authentication and protocol initialization.

## Setup Instructions

### 1. Prerequisites
- Python 3.9 or higher.
- Bluetooth enabled on your computer.

### 2. Installation
Open your terminal in this folder and run:
```bash
# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# .venv\Scripts\activate   # On Windows

# Install the Bluetooth library
pip install bleak
```

## Usage
1. Turn on your Apitor robot (ensure the blue LED is flashing).
2. Run the application:
   ```bash
   python apitor_gui.py
   ```
3. Click **SCAN FOR ROBOT** to find your device, then **CONNECT**.

### Keyboard Shortcuts
- **W / S:** Move Forward / Backward
- **A / D:** Turn Left / Right
- **Space:** Stop All Motors
- **1 - 8:** Quick Change LED Colors (Off, Red, Orange, etc.)


## Testing
To ensure the code is not broken, you can run the following checks:

### 1. Syntax Check
Verifies that the code is free of Python syntax errors:
```bash
python check_syntax.py
```

### 2. Unit Tests
Verifies the robot logic (speed clamping, inversion, etc.):
```bash
python test_apitor_robot.py
```

## Troubleshooting
- **Connection Failed:** Ensure no other app (like the official Apitor app) is currently connected to the robot.
- **Permissions:** On Linux, you may need to add your user to the `bluetooth` group or run with `sudo`.
- **Wrong Robot:** If you have multiple robots, change the `ROBOT_MAC` address at the bottom of `apitor_gui.py`.

## Project Structure
- `apitor_robot.py`: Core logic for Bluetooth communication and protocol.
- `apitor_gui.py`: The user interface and event handling.
