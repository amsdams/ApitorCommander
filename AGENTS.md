# AGENTS.md

This file provides technical context and instructions for AI agents working on **ApitorCommander**.

## Project Overview
This is a professional-grade Python project for controlling Apitor robots via Bluetooth Low Energy (BLE). It features a modular architecture, real-time telemetry, and a hardware-centric GUI.

## Setup & Environment
- **Python Version:** 3.9+
- **Primary Dependency:** `bleak`
- **Installation:** `pip install bleak`
- **Entry Point:** `python apitor_gui.py`
- **CLI Health Tool:** `python health_check.py`

## Architecture & Logic
- **`apitor_robot.py`**: Hardware abstraction layer (Backend). 
    - Manages a background `asyncio` event loop in a dedicated `threading.Thread`.
    - Handles BLE discovery, authentication, and the `FF FE` state protocol.
    - **Inversion Logic:** Motor 2 speed is automatically inverted to compensate for mirrored hardware mounting.
- **`apitor_gui.py`**: Modular UI layer (Frontend).
    - Built with `tkinter`.
    - Communicates with `ApitorRobot` via async-safe method calls.
    - Uses `root.after(0, ...)` for thread-safe UI updates from BLE callbacks.
    - Implements **Dynamic Window Sizing** based on requested widget dimensions.

## BLE Protocol Reference
- **Service UUID:** `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- **Write Characteristic:** `6e400002-b5a3-f393-e0a9-e50e24dcca9e`
- **Read/Notify Characteristic:** `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- **Auth Sequence:** `55aa112064796f7a574f50663035326757565034` (Hex)
- **Handshake:** `fffe0104fdfc` (Hex)
- **State Packet (FFFE Protocol):**
  - Format: `FF FE 09 01 02 [M1] [M2] 00 [L1] [L2] [L3] [L4] FD FC`
  - `M1`/`M2`: Signed bytes (-100 to 100).
  - `L1`-`L4`: Color indices (0-7).
- **Sensor Parsing (FFFE):**
  - Prefix: `FF FE 06 01 01`
  - Battery: index 5 (Scale: ~90-130).
  - IR Sensors: index 7 and 8 (High sensitivity scale used: 0-10).

## LED Color Mapping
- 0: Off, 1: Red, 2: Orange, 3: Yellow, 4: Green, 5: Cyan, 6: Blue, 7: Violet.

## Development Standards
- **Validation:** Always run `python check_syntax.py` and `python test_apitor_robot.py` before committing.
- **Modularity:** Maintain the separation between BLE protocol (`apitor_robot.py`) and UI presentation (`apitor_gui.py`).
