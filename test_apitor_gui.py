import unittest
from apitor_gui import ApitorGui
import tkinter as tk
from unittest.mock import MagicMock

class TestApitorGuiConsistency(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        # Mocking ApitorRobot to avoid Bluetooth/BLE dependencies
        with unittest.mock.patch('apitor_gui.ApitorRobot') as MockRobot:
            self.app = ApitorGui(self.root, "00:00:00:00:00:00")

    def tearDown(self):
        self.root.destroy()

    def test_manual_master_exists(self):
        """Regression test for 'manual_master' removal."""
        self.assertTrue(hasattr(self.app, 'manual_master'), "ApitorGui is missing 'manual_master' method")
        self.assertTrue(callable(getattr(self.app, 'manual_master')), "'manual_master' is not a callable method")

    def test_move_one_exists(self):
        """Ensure '_move_one' helper exists."""
        self.assertTrue(hasattr(self.app, '_move_one'), "ApitorGui is missing '_move_one' method")

if __name__ == '__main__':
    unittest.main()
