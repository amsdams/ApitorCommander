import asyncio
import sys
import time
from apitor_robot import ApitorRobot

# Constants
ROBOT_MAC = "F9:F6:9F:FD:09:4A"

async def run_health_check():
    print(f"--- Apitor Hardware Health Check ---")
    print(f"Target Robot: {ROBOT_MAC}")
    
    robot = ApitorRobot(ROBOT_MAC)
    connection_event = asyncio.Event()
    
    def on_connection(success):
        if success:
            print("[OK] Connected to robot.")
            connection_event.set()
        else:
            print("[FAIL] Could not connect.")
            sys.exit(1)

    # 1. Connect
    print("Connecting...")
    robot.connect(on_connection)
    
    # Wait for connection (timeout 10s)
    try:
        await asyncio.wait_for(connection_event.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        print("[FAIL] Connection timed out.")
        return

    # 2. Test LEDs
    print("Testing LEDs (Blue)...")
    for i in range(4):
        robot.set_led(i, 6) # Blue
    await asyncio.sleep(1)
    
    print("Testing LEDs (Red)...")
    for i in range(4):
        robot.set_led(i, 1) # Red
    await asyncio.sleep(1)

    print("Turning LEDs Off...")
    for i in range(4):
        robot.set_led(i, 0) # Off

    # 3. Test Motors
    print("Testing Motors (Forward 50%)...")
    robot.set_motors(50, 50)
    await asyncio.sleep(2)

    print("Stopping Motors...")
    robot.stop()
    await asyncio.sleep(1)

    print("Testing Motors (Backward 50%)...")
    robot.set_motors(-50, -50)
    await asyncio.sleep(2)

    print("Final Stop...")
    robot.stop()
    
    # 4. Disconnect
    print("Disconnecting...")
    robot.disconnect()
    print("--- Health Check Complete ---")

if __name__ == "__main__":
    try:
        asyncio.run(run_health_check())
    except KeyboardInterrupt:
        print("\nHealth check cancelled by user.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
