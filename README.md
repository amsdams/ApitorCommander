# ApitorCommander

A comprehensive Python-based hardware command center for Apitor robots (SuperBot, Robot X, etc.) over Bluetooth Low Energy (BLE).

## Features
- **Modular Hardware Console:** Dedicated panels for Battery, Dual Infrared Sensors, Motors, and LEDs.
- **Visual Telemetry:** Real-time vertical bars for IR sensors and a battery fuel gauge.
- **Precision Control:** Master speed slider plus independent speed controls for each motor.
- **Granular LED Management:** Individual color selection for 4 RGB LEDs using full-label radio buttons.
- **Traffic Log:** Built-in collapsible hex-log to monitor real-time BLE packets.
- **Keyboard Mastery:** Full support for WASD/Arrows, numeric LED toggles, and system function keys.

## Setup Instructions

### 1. Prerequisites
- Python 3.9 or higher.
- Bluetooth enabled on your computer.

### 2. Installation
Open your terminal in this folder and run:
```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# .venv\Scripts\activate   # On Windows

# Install the Bluetooth library
pip install bleak
```

### 3. Usage

#### Graphical Interface (GUI)
Run the full command center:
```bash
python apitor_gui.py
```
1. Press **F1** to **SCAN** for your robot.
2. Press **F2** to **CONNECT** once found.
3. Drive using WASD or Arrows!

#### Health Check (CLI)
Run a quick automated hardware test without the UI:
```bash
python health_check.py
```

### Keyboard Shortcuts
- **W / S / A / D:** Master Drive (Forward, Backward, Left, Right)
- **Arrow Keys:** Alternative Master Drive
- **Q / E:** Motor 1 (Left) Forward / Backward
- **I / K:** Motor 2 (Right) Forward / Backward
- **1 - 4:** Toggle LED 1-4 On/Off
- **Space:** Emergency STOP ALL
- **F1 / F2 / F3:** Scan / Connect / Disconnect

## Testing & Verification
To ensure the code is stable and the logic is correct:

### Syntax Check
```bash
python check_syntax.py
```

### Logic Unit Tests
```bash
python test_apitor_robot.py
```

## Project Structure
- `apitor_robot.py`: Backend hardware abstraction and BLE protocol.
- `apitor_gui.py`: Frontend modular command center.
- `health_check.py`: CLI-based hardware verification tool.
- `AGENTS.md`: Technical reference for AI contributors.
