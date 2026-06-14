# AGENTS.md

This file provides technical context and instructions for AI agents working on the Apitor Robot project.

## Project Overview
This is a Python project for controlling Apitor robots via Bluetooth Low Energy (BLE). It uses the `bleak` library for communication and `tkinter` for the GUI.

## Setup & Environment
- **Python Version:** 3.9+
- **Primary Dependency:** `bleak`
- **Installation:** `pip install bleak`
- **Entry Point:** `python apitor_gui.py`

## Architecture & Logic
- **`apitor_robot.py`**: Hardware abstraction layer. Handles async BLE loops in a separate thread.
- **`apitor_gui.py`**: UI layer. Communicates with `ApitorRobot` via method calls.
- **Thread Safety:** All UI updates from BLE callbacks must use `root.after(0, ...)` to avoid Tkinter thread collisions.

## BLE Protocol Reference
- **Service UUID:** `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- **Write Characteristic:** `6e400002-b5a3-f393-e0a9-e50e24dcca9e`
- **Read/Notify Characteristic:** `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- **Auth Sequence:** `55aa112064796f7a574f50663035326757565034` (Hex)
- **Init Handshake:** `fffe0104fdfc` (Hex)
- **Motor Command (FFFE Protocol):**
  - Packet: `FF FE 09 01 02 [M1] [M2] 00 00 00 00 00 FD FC`
  - `M1`/`M2` are signed bytes (-100 to 100).
- **Sensor Notification (FFFE):**
  - Prefix: `FF FE 06 01 01`
  - Distance value: index 5.

## Code Conventions
- **Asynchronous Code:** BLE operations must be run in the robot's dedicated event loop using `asyncio.run_coroutine_threadsafe`.
- **Modularity:** Keep hardware-specific logic in `apitor_robot.py`.
- **Documentation:** Use docstrings for public methods in the robot class.
