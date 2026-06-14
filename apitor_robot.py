import asyncio
import threading
from enum import IntEnum
from bleak import BleakClient, BleakScanner

class ApitorProtocol(IntEnum):
    """Centralized constants for the Apitor BLE protocol."""
    SERVICE_UUID = 0x6E400001 # Base Nordic UART
    WRITE_UUID = 0x6E400002
    NOTIFY_UUID = 0x6E400003
    
    # Packets (Hex strings converted to bytes)
    AUTH_SEQ = 0x55aa112064796f7a574f50663035326757565034
    HANDSHAKE = 0xFFFE0104FDFC
    
    # Packet Headers/Footers
    HEADER = 0xFFFE
    FOOTER = 0xFDFC
    CMD_SENSOR_UPDATE = 0x06
    CMD_STATE_SYNC = 0x01
    SUB_CMD_MOTORS_LEDS = 0x02

class ApitorRobot:
    """
    Hardware abstraction layer for Apitor Robots.
    Manages a dedicated asyncio event loop in a background thread.
    """
    
    # UUIDs as strings for Bleak
    WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    RX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

    def __init__(self, address):
        self.address = address
        self.client = None
        self.connected = False
        self.on_sensor_data = None
        self.on_log = None
        
        # State
        self.m_speeds = [0, 0]
        self.led_colors = [0, 0, 0, 0]
        
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _safe_log(self, direction, message):
        if self.on_log:
            self.on_log(direction, message)

    def connect(self, callback):
        """Asynchronously connect with retry logic."""
        asyncio.run_coroutine_threadsafe(self._async_connect(callback), self.loop)

    async def _async_connect(self, callback):
        try:
            self.client = BleakClient(self.address, disconnected_callback=self._on_disconnected)
            await self.client.connect()
            
            await self.client.start_notify(self.RX_UUID, self._notification_handler)
            
            # Step 1: Authentication
            auth_bytes = bytes.fromhex("55aa112064796f7a574f50663035326757565034")
            self._safe_log("TX", auth_bytes.hex())
            await self.client.write_gatt_char(self.WRITE_UUID, auth_bytes)
            
            await asyncio.sleep(0.3)
            
            # Step 2: Protocol Handshake
            handshake = bytes.fromhex("fffe0104fdfc")
            self._safe_log("TX", handshake.hex())
            await self.client.write_gatt_char(self.WRITE_UUID, handshake)
            
            self.connected = True
            callback(True)
        except Exception as e:
            print(f"Connection Error: {e}")
            callback(False)

    def _on_disconnected(self, client):
        self.connected = False
        self._safe_log("SYS", "Disconnected from hardware")

    async def scan(self):
        """Scan for Apitor/Nordic devices."""
        devices = await BleakScanner.discover()
        for d in devices:
            if d.name and any(x in d.name for x in ["Apitor", "Nordic", "TUDAO"]):
                return d.address
        return None

    def disconnect(self):
        if self.connected:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)

    def _notification_handler(self, sender, data):
        self._safe_log("RX", data.hex())
        
        if len(data) < 6 or data[0] != 0xFF or data[1] != 0xFE:
            return

        if data[2] == 0x06: # Sensor Packet
            battery = data[5]
            ir1 = data[7] if len(data) > 7 else 0
            ir2 = data[8] if len(data) > 8 else 0
            
            if self.on_sensor_data:
                self.on_sensor_data("battery", battery)
                self.on_sensor_data("ir1", ir1)
                self.on_sensor_data("ir2", ir2)

    def set_led(self, index, color):
        if 0 <= index < 4:
            self.led_colors[index] = color
            self._sync_state()

    def set_motors(self, m1, m2):
        # M2 is inverted due to mirrored mounting
        self.m_speeds = [
            max(min(int(m1), 100), -100),
            -max(min(int(m2), 100), -100)
        ]
        self._sync_state()

    def _sync_state(self):
        if not self.connected:
            return

        # FF FE [Len] 01 02 [M1] [M2] 00 [L1] [L2] [L3] [L4] FD FC
        m1_u8 = self.m_speeds[0] & 0xFF
        m2_u8 = self.m_speeds[1] & 0xFF
        l1, l2, l3, l4 = self.led_colors
        
        packet = bytearray([0xFF, 0xFE, 0x09, 0x01, 0x02, m1_u8, m2_u8, 0x00, l1, l2, l3, l4, 0xFD, 0xFC])
        self._safe_log("TX", packet.hex())
        
        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(self.WRITE_UUID, packet), 
            self.loop
        )

    def stop(self):
        self.m_speeds = [0, 0]
        self._sync_state()
