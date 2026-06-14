import tkinter as tk
from tkinter import messagebox, ttk
import threading
import asyncio
from datetime import datetime
from apitor_robot import ApitorRobot

class ApitorGui:
    def __init__(self, root, robot_address):
        self.root = root
        self.root.title("Apitor Master Controller")
        # Optimized geometry to prevent "hidden" content
        self.root.geometry("520x950")

        # Backend Robot instance
        self.robot = ApitorRobot(robot_address)
        self.robot.on_sensor_data = self.handle_sensor_data
        self.robot.on_log = self.log_message

        # State & Settings
        self.logging_enabled = tk.BooleanVar(value=True)
        self.log_limit = tk.IntVar(value=40)
        self.pressed_keys = set()
        self.colors = ["Off", "Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Violet"]

        self._setup_ui()
        self._bind_keys()

    def _setup_ui(self):
        # 1. Header & Connection
        header_frame = tk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_lbl = tk.Label(header_frame, text="Disconnected", font=("Arial", 12, "bold"), fg="red")
        self.status_lbl.pack(side="left")
        
        tk.Button(header_frame, text="SCAN (F1)", command=self.start_scan).pack(side="right", padx=2)
        self.disconn_btn = tk.Button(header_frame, text="DISCONN (F3)", command=self.disconnect, state="disabled")
        self.disconn_btn.pack(side="right", padx=2)
        self.conn_btn = tk.Button(header_frame, text="CONNECT (F2)", command=self.connect, bg="#4CAF50", fg="white")
        self.conn_btn.pack(side="right", padx=2)

        # 2. Telemetry
        tele_frame = tk.LabelFrame(self.root, text="Telemetry", padx=5, pady=5)
        tele_frame.pack(fill="x", padx=10, pady=5)
        self.batt_lbl = tk.Label(tele_frame, text="Batt: --%", font=("Courier", 10, "bold"))
        self.batt_lbl.pack(side="left", padx=10)
        self.ir1_lbl = tk.Label(tele_frame, text="IR1: --", font=("Courier", 10))
        self.ir1_lbl.pack(side="left", padx=10)
        self.ir2_lbl = tk.Label(tele_frame, text="IR2: --", font=("Courier", 10))
        self.ir2_lbl.pack(side="left", padx=10)

        # 3. Individual LED Controls
        led_frame = tk.LabelFrame(self.root, text="Individual LEDs (Keys 1,2,3,4 to toggle)", padx=5, pady=5)
        led_frame.pack(fill="x", padx=10, pady=5)
        
        self.led_selectors = []
        for i in range(4):
            f = tk.Frame(led_frame)
            f.pack(side="left", expand=True)
            tk.Label(f, text=f"L{i+1}", font=("Arial", 8)).pack()
            var = tk.StringVar(value="Off")
            opt = ttk.OptionMenu(f, var, "Off", *self.colors, command=lambda c, idx=i: self.robot.set_led(idx, self.colors.index(c)))
            opt.pack()
            self.led_selectors.append(var)

        # 4. Motor Controls (WASD + Individual)
        motor_frame = tk.LabelFrame(self.root, text="Motor Controls (WASD / QE / IK)", padx=5, pady=5)
        motor_frame.pack(fill="x", padx=10, pady=5)
        
        # Grid for buttons
        grid = tk.Frame(motor_frame)
        grid.pack()

        # M1 Column
        tk.Label(grid, text="Motor 1 (Q/E)").grid(row=0, column=0)
        tk.Button(grid, text="M1 Fwd", width=10, command=lambda: self.manual_motor(70, 0)).grid(row=1, column=0)
        tk.Button(grid, text="M1 Back", width=10, command=lambda: self.manual_motor(-70, 0)).grid(row=2, column=0)

        # Center Column (Combined)
        tk.Button(grid, text="BOTH FWD (W)", width=12, bg="#e1f5fe", command=lambda: self.manual_motor(70, 70)).grid(row=1, column=1, padx=10)
        tk.Button(grid, text="STOP (Space)", width=12, bg="#f44336", fg="white", command=self.robot.stop).grid(row=2, column=1, padx=10)
        tk.Button(grid, text="BOTH BK (S)", width=12, bg="#e1f5fe", command=lambda: self.manual_motor(-70, -70)).grid(row=3, column=1, padx=10)

        # M2 Column
        tk.Label(grid, text="Motor 2 (I/K)").grid(row=0, column=2)
        tk.Button(grid, text="M2 Fwd", width=10, command=lambda: self.manual_motor(0, 70)).grid(row=1, column=2)
        tk.Button(grid, text="M2 Back", width=10, command=lambda: self.manual_motor(0, -70)).grid(row=2, column=2)

        # 5. Speed Control
        spd_frame = tk.Frame(self.root, padx=10)
        spd_frame.pack(fill="x")
        tk.Label(spd_frame, text="Speed Intensity ([ / ] to adjust):").pack(side="left")
        self.speed = tk.Scale(self.root, from_=0, to=100, orient="horizontal")
        self.speed.set(70)
        self.speed.pack(fill="x", padx=20, pady=(0, 10))

        # 6. Log Console (Optimized width)
        log_frame = tk.LabelFrame(self.root, text="Traffic Log", padx=5, pady=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        log_ctrl = tk.Frame(log_frame)
        log_ctrl.pack(fill="x")
        tk.Checkbutton(log_ctrl, text="Log", variable=self.logging_enabled).pack(side="left")
        self.log_filter = tk.StringVar(value="All")
        ttk.Combobox(log_ctrl, textvariable=self.log_filter, values=["All", "TX", "RX"], width=8).pack(side="left", padx=5)
        tk.Button(log_ctrl, text="Clear", command=self.clear_log, width=6).pack(side="right")

        # Set width explicitly to prevent window stretching
        self.log_text = tk.Text(log_frame, height=12, width=50, font=("Courier", 8), state="disabled", bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.pack(fill="both", expand=True)

        # 7. Shortcut Footer
        footer = tk.Label(self.root, text="WASD:Drive | QE:M1 | IK:M2 | Space:Stop | 1-4:LEDs | []:Speed", font=("Arial", 8, "italic"), bg="#eee")
        footer.pack(fill="x", side="bottom")

    def _bind_keys(self):
        self.root.bind("<KeyPress>", self.handle_keypress)
        self.root.bind("<KeyRelease>", self.handle_keyrelease)
        self.root.bind("<F1>", lambda e: self.start_scan())
        self.root.bind("<F2>", lambda e: self.connect())
        self.root.bind("<F3>", lambda e: self.disconnect())

    def handle_keypress(self, event):
        key = event.keysym.lower()
        if key in self.pressed_keys: return
        self.pressed_keys.add(key)
        
        # LED Cycling (1-4)
        if key in "1234":
            idx = int(key) - 1
            current = self.led_selectors[idx].get()
            new_idx = (self.colors.index(current) + 1) % len(self.colors)
            new_color = self.colors[new_idx]
            self.led_selectors[idx].set(new_color)
            self.robot.set_led(idx, new_idx)

        # Speed Adjustment
        if key == "bracketright": # ]
            self.speed.set(min(self.speed.get() + 10, 100))
        if key == "bracketleft": # [
            self.speed.set(max(self.speed.get() - 10, 0))

        self.update_movement()

    def handle_keyrelease(self, event):
        key = event.keysym.lower()
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        self.update_movement()

    def update_movement(self):
        if not self.robot.connected: return
        spd = self.speed.get()
        m1, m2 = 0, 0
        
        # WASD (Global)
        if 'w' in self.pressed_keys: m1, m2 = spd, spd
        elif 's' in self.pressed_keys: m1, m2 = -spd, -spd
        elif 'a' in self.pressed_keys: m1, m2 = -spd, spd
        elif 'd' in self.pressed_keys: m1, m2 = spd, -spd
        
        # Individual Overrides
        if 'q' in self.pressed_keys: m1 = spd
        if 'e' in self.pressed_keys: m1 = -spd
        if 'i' in self.pressed_keys: m2 = spd
        if 'k' in self.pressed_keys: m2 = -spd

        if 'space' in self.pressed_keys: m1, m2 = 0, 0
        self.robot.set_motors(m1, m2)

    def log_message(self, direction, msg):
        if not self.logging_enabled.get(): return
        if self.log_filter.get() != "All" and self.log_filter.get() != direction: return
        
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] {direction}: {msg}\n"
        self.root.after(0, lambda: self._write_to_log(line))

    def _write_to_log(self, line):
        self.log_text.config(state="normal")
        self.log_text.insert("end", line)
        if "TX:" in line: self.log_text.tag_add("tx", "end-2c linestart", "end-1c")
        elif "RX:" in line: self.log_text.tag_add("rx", "end-2c linestart", "end-1c")
        self.log_text.tag_config("tx", foreground="#4ec9b0")
        self.log_text.tag_config("rx", foreground="#ce9178")
        self.log_text.see("end")
        
        limit = self.log_limit.get()
        curr = int(self.log_text.index("end-1c").split(".")[0])
        if curr > limit: self.log_text.delete("1.0", "2.0")
        self.log_text.config(state="disabled")

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def manual_motor(self, m1, m2):
        self.robot.set_motors(m1, m2)

    def connect(self):
        self.status_lbl.config(text="Connecting...", fg="orange")
        self.conn_btn.config(state="disabled")
        self.robot.connect(self.on_connection_result)

    def disconnect(self):
        self.robot.disconnect()
        self.status_lbl.config(text="Disconnected", fg="red")
        self.conn_btn.config(state="normal")
        self.disconn_btn.config(state="disabled")

    def on_connection_result(self, success):
        if success: self.root.after(0, self._conn_ok)
        else: self.root.after(0, self._conn_fail)

    def _conn_ok(self):
        self.status_lbl.config(text="Connected", fg="green")
        self.disconn_btn.config(state="normal")

    def _conn_fail(self):
        self.status_lbl.config(text="Disconnected", fg="red")
        self.conn_btn.config(state="normal")
        messagebox.showerror("Error", "Connect failed")

    def start_scan(self):
        self.status_lbl.config(text="Scanning...", fg="blue")
        future = asyncio.run_coroutine_threadsafe(self.robot.scan(), self.robot.loop)
        threading.Thread(target=lambda: self._scan_done(future.result()), daemon=True).start()

    def _scan_done(self, address):
        if address: 
            self.root.after(0, lambda: self.status_lbl.config(text=f"Found Robot!", fg="green"))
            self.robot.address = address
        else:
            self.root.after(0, lambda: self.status_lbl.config(text="No robot", fg="red"))

    def handle_sensor_data(self, type, value):
        if type == "battery": self.root.after(0, lambda: self.batt_lbl.config(text=f"Batt: {value}%"))
        elif type == "ir1": self.root.after(0, lambda: self.ir1_lbl.config(text=f"IR1: {value}"))
        elif type == "ir2": self.root.after(0, lambda: self.ir2_lbl.config(text=f"IR2: {value}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = ApitorGui(root, "F9:F6:9F:FD:09:4A")
    root.mainloop()
