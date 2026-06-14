import unittest
from apitor_robot import ApitorRobot

class TestApitorRobot(unittest.TestCase):
    def setUp(self):
        # We use a dummy address. Since we aren't calling .connect(), 
        # it won't actually try to use Bluetooth hardware.
        self.robot = ApitorRobot("00:00:00:00:00:00")

    def test_motor_speed_clamping(self):
        """Verify that speeds are correctly clamped to -100/100."""
        # Test positive clamp (M1)
        self.robot.set_motors(150, 0)
        self.assertEqual(self.robot.m_speeds[0], 100)
        
        # Test negative clamp (M2)
        # Input -200, clamped to -100, then inverted by logic to +100
        self.robot.set_motors(0, -200)
        self.assertEqual(self.robot.m_speeds[1], 100)

    def test_motor_inversion(self):
        """Verify that Motor 2 is correctly inverted for differential drive."""
        self.robot.set_motors(50, 50)
        # m_speeds[1] should be the negative of the input
        self.assertEqual(self.robot.m_speeds[0], 50)
        self.assertEqual(self.robot.m_speeds[1], -50)

    def test_led_bounds(self):
        """Verify LED index safety."""
        self.robot.set_led(0, 1) # Red
        self.assertEqual(self.robot.led_colors[0], 1)
        
        # Should ignore invalid indices
        self.robot.set_led(5, 1)
        self.assertEqual(len(self.robot.led_colors), 4)

if __name__ == '__main__':
    unittest.main()
