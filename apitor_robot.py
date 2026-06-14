import asyncio
import threading
from bleak import BleakClient, BleakScanner

class ApitorRobot:
    """
    Controller for Apitor Robots.
    Handles BLE connectivity, authentication, and motor protocol details.
    """
    
    # Nordic UART Service UUIDs
    WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    RX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    
    # Common Authentication/Handshake Sequences
    AUTH_SEQ = bytes.fromhex("55aa112064796f7a574f50663035326757565034")
    HANDSHAKE_FFFE = bytearray([0xFF, 0xFE, 0x01, 0x04, 0xFD, 0xFC])

    def __init__(self, address):
        self.address = address
        self.client = None
        self.connected = False
        self.on_sensor_data = None  # Callback function for sensor updates
        self.loop = asyncio.new_event_loop()
        
        # Start background thread for async operations
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, callback):
        """Asynchronously connect to the robot."""
        asyncio.run_coroutine_threadsafe(self._async_connect(callback), self.loop)

    async def _async_connect(self, callback):
        try:
            self.client = BleakClient(self.address)
            await self.client.connect()
            
            # Start notifications
            await self.client.start_notify(self.RX_UUID, self._notification_handler)
            
            # Step 1: Authentication
            await self.client.write_gatt_char(self.WRITE_UUID, self.AUTH_SEQ)
            await asyncio.sleep(0.3)
            
            # Step 2: Protocol Initialization
            await self.client.write_gatt_char(self.WRITE_UUID, self.HANDSHAKE_FFFE)
            
            self.connected = True
            callback(True)
        except Exception as e:
            print(f"Connection failed: {e}")
            callback(False)

    def disconnect(self):
        if self.connected:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
            self.connected = False

    def _notification_handler(self, sender, data):
        # Parse common FFFE sensor data (e.g., distance)
        if len(data) >= 6 and data[0] == 0xFF and data[1] == 0xFE and data[2] == 0x06:
            dist = data[5]
            if self.on_sensor_data:
                self.on_sensor_data("distance", dist)

    def set_motors(self, m1_speed, m2_speed):
        """
        Set speed for both motors (-100 to 100).
        Positive = Forward, Negative = Backward.
        """
        if not self.connected:
            return

        # Ensure bounds
        m1 = max(min(int(m1_speed), 100), -100) & 0xFF
        m2 = max(min(int(m2_speed), 100), -100) & 0xFF

        # FF FE [Len] 01 02 [M1] [M2] 00 [L1] [L2] [L3] [L4] FD FC
        packet = bytearray([0xFF, 0xFE, 0x09, 0x01, 0x02, m1, m2, 0, 0, 0, 0, 0, 0xFD, 0xFC])
        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(self.WRITE_UUID, packet), 
            self.loop
        )

    def stop(self):
        self.set_motors(0, 0)
