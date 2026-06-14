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
        self.on_sensor_data = None  # Callback function for sensor updates (type, value)
        
        # State tracking
        self.m_speeds = [0, 0] # M1, M2
        self.led_colors = [0, 0, 0, 0] # LED 1, 2, 3, 4
        self.battery = 0
        
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, callback):
        """Asynchronously connect to the robot."""
        asyncio.run_coroutine_threadsafe(self._async_connect(callback), self.loop)

    async def scan(self):
        """Scan for nearby Apitor robots and return the address of the first one found."""
        print("Scanning for Apitor robots...")
        devices = await BleakScanner.discover()
        for d in devices:
            # Look for common names used by Apitor modules
            if d.name and any(x in d.name for x in ["Apitor", "Nordic", "TUDAO"]):
                return d.address
        return None

    async def _async_connect(self, callback):
        try:
            self.client = BleakClient(self.address)
            await self.client.connect()
            
            await self.client.start_notify(self.RX_UUID, self._notification_handler)
            await self.client.write_gatt_char(self.WRITE_UUID, self.AUTH_SEQ)
            await asyncio.sleep(0.3)
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
        """
        Parses incoming data packets from the robot.
        Standard frame: FF FE [Len] [Cmd] ... FD FC
        """
        if len(data) < 6 or data[0] != 0xFF or data[1] != 0xFE:
            return

        cmd_type = data[2]
        
        if cmd_type == 0x06: # Sensor update
            # Index 5: Battery level
            # Index 7: IR Sensor 1
            # Index 8: IR Sensor 2
            self.battery = data[5]
            ir1 = data[7] if len(data) > 7 else 0
            ir2 = data[8] if len(data) > 8 else 0
            
            if self.on_sensor_data:
                self.on_sensor_data("battery", self.battery)
                self.on_sensor_data("ir1", ir1)
                self.on_sensor_data("ir2", ir2)

    def set_led(self, led_index, color_index):
        """
        Set color for an LED (0-3). Colors: 0:Off, 1:Red, 2:Orange, 3:Yellow, 4:Green, 5:Cyan, 6:Blue, 7:Violet.
        """
        if 0 <= led_index < 4:
            self.led_colors[led_index] = color_index
            self._sync_state()

    def set_motors(self, m1_speed, m2_speed):
        """
        Set speed for both motors (-100 to 100).
        Note: Motor 2 is inverted to account for mirrored physical mounting
        in standard differential drive builds.
        """
        self.m_speeds[0] = max(min(int(m1_speed), 100), -100)
        self.m_speeds[1] = -max(min(int(m2_speed), 100), -100) # Inverted for M2
        self._sync_state()

    def _sync_state(self):
        """Sends the full state (motors + LEDs) to the robot."""
        if not self.connected:
            return

        m1 = self.m_speeds[0] & 0xFF
        m2 = self.m_speeds[1] & 0xFF
        l1, l2, l3, l4 = self.led_colors

        # Packet: FF FE [Len] 01 02 [M1] [M2] 00 [L1] [L2] [L3] [L4] FD FC
        packet = bytearray([0xFF, 0xFE, 0x09, 0x01, 0x02, m1, m2, 0, l1, l2, l3, l4, 0xFD, 0xFC])
        asyncio.run_coroutine_threadsafe(
            self.client.write_gatt_char(self.WRITE_UUID, packet), 
            self.loop
        )

    def stop(self):
        self.m_speeds = [0, 0]
        self._sync_state()
