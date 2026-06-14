import tkinter as tk
from tkinter import messagebox, ttk
import threading
import asyncio
from datetime import datetime
from apitor_robot import ApitorRobot

class ApitorGui:
    def __init__(self, root, robot_address):
        self.root = root
        self.root.title("Apitor Hardware Command Center")
        self.root.geometry("700x900")

        # Backend Robot instance
        self.robot = ApitorRobot(robot_address)
        self.robot.on_sensor_data = self.handle_sensor_data
        self.robot.on_log = self.log_message

        # State & Settings
        self.log_visible = False
        self.pressed_keys = set()
        self.colors = ["Off", "Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Violet"]
        self.hex_colors = ["#333", "#ff0000", "#ffa500", "#ffff00", "#00ff00", "#00ffff", "#0000ff", "#ee82ee"]

        self._setup_ui()
        self._bind_keys()

    def _setup_ui(self):
        # 1. Connection & Status
        conn_frame = tk.Frame(self.root, pady=5)
        conn_frame.pack(fill="x", padx=10)
        
        self.status_lbl = tk.Label(conn_frame, text="Disconnected", font=("Arial", 12, "bold"), fg="red")
        self.status_lbl.pack(side="left")
        
        tk.Button(conn_frame, text="SCAN (F1)", command=self.start_scan).pack(side="right", padx=2)
        self.disconn_btn = tk.Button(conn_frame, text="DISCONNECT (F3)", command=self.disconnect, state="disabled")
        self.disconn_btn.pack(side="right", padx=2)
        self.conn_btn = tk.Button(conn_frame, text="CONNECT (F2)", command=self.connect, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"))
        self.conn_btn.pack(side="right", padx=2)

        # 2. Main Hardware Area
        main_hw = tk.Frame(self.root)
        main_hw.pack(fill="both", expand=True, padx=10)

        # --- LEFT COLUMN: Sensors ---
        left_col = tk.Frame(main_hw)
        left_col.pack(side="left", fill="y", padx=(0, 5))

        # Battery Panel
        batt_frame = tk.LabelFrame(left_col, text="Battery", padx=10, pady=10)
        batt_frame.pack(fill="x", pady=(0, 5))
        self.batt_bar = ttk.Progressbar(batt_frame, orient="horizontal", length=100, mode="determinate")
        self.batt_bar.pack(pady=5)
        self.batt_lbl = tk.Label(batt_frame, text="--%", font=("Courier", 9, "bold"))
        self.batt_lbl.pack()

        # IR Sensor Panel
        ir_frame = tk.LabelFrame(left_col, text="IR Sensors", padx=10, pady=10)
        ir_frame.pack(fill="y", expand=True)
        
        ir_container = tk.Frame(ir_frame)
        ir_container.pack()

        # IR1 Bar
        ir1_f = tk.Frame(ir_container)
        ir1_f.pack(side="left", padx=5)
        self.ir1_canvas = tk.Canvas(ir1_f, width=20, height=200, bg="#222", highlightthickness=0)
        self.ir1_canvas.pack()
        self.ir1_rect = self.ir1_canvas.create_rectangle(0, 200, 20, 200, fill="green")
        tk.Label(ir1_f, text="IR1", font=("Arial", 8)).pack()

        # IR2 Bar
        ir2_f = tk.Frame(ir_container)
        ir2_f.pack(side="left", padx=5)
        self.ir2_canvas = tk.Canvas(ir2_f, width=20, height=200, bg="#222", highlightthickness=0)
        self.ir2_canvas.pack()
        self.ir2_rect = self.ir2_canvas.create_rectangle(0, 200, 20, 200, fill="green")
        tk.Label(ir2_f, text="IR2", font=("Arial", 8)).pack()

        # --- CENTER COLUMN: Motors ---
        center_col = tk.Frame(main_hw)
        center_col.pack(side="left", fill="both", expand=True, padx=5)

        # Master Drive Panel
        drive_f = tk.LabelFrame(center_col, text="Master Drive (WASD / Arrows)", padx=10, pady=10)
        drive_f.pack(fill="x", pady=(0, 5))
        
        d_grid = tk.Frame(drive_f)
        d_grid.pack()
        tk.Button(d_grid, text="▲", width=6, command=lambda: self.manual_master(80, 80)).grid(row=0, column=1)
        tk.Button(d_grid, text="◀", width=6, command=lambda: self.manual_master(-60, 60)).grid(row=1, column=0)
        tk.Button(d_grid, text="STOP", width=6, bg="#f44336", fg="white", command=self.robot.stop).grid(row=1, column=1)
        tk.Button(d_grid, text="▶", width=6, command=lambda: self.manual_master(60, -60)).grid(row=1, column=2)
        tk.Button(d_grid, text="▼", width=6, command=lambda: self.manual_master(-80, -80)).grid(row=2, column=1)

        # Individual Motor Control Panels
        m_container = tk.Frame(center_col)
        m_container.pack(fill="both", expand=True)

        # Motor 1 Panel
        m1_frame = tk.LabelFrame(m_container, text="Motor 1 (Left)", padx=10, pady=10)
        m1_frame.pack(side="left", fill="both", expand=True, padx=(0, 2))
        tk.Button(m1_frame, text="FWD", command=lambda: self.robot.set_motors(self.m1_speed.get(), self.robot.m_speeds[1]), width=8).pack()
        self.m1_speed = tk.Scale(m1_frame, from_=0, to=100, orient="vertical", label="Spd")
        self.m1_speed.set(70)
        self.m1_speed.pack(fill="y", expand=True)
        tk.Button(m1_frame, text="BACK", command=lambda: self.robot.set_motors(-self.m1_speed.get(), self.robot.m_speeds[1]), width=8).pack()

        # Motor 2 Panel
        m2_frame = tk.LabelFrame(m_container, text="Motor 2 (Right)", padx=10, pady=10)
        m2_frame.pack(side="left", fill="both", expand=True, padx=(2, 0))
        tk.Button(m2_frame, text="FWD", command=lambda: self.robot.set_motors(self.robot.m_speeds[0], self.m2_speed.get()), width=8).pack()
        self.m2_speed = tk.Scale(m2_frame, from_=0, to=100, orient="vertical", label="Spd")
        self.m2_speed.set(70)
        self.m2_speed.pack(fill="y", expand=True)
        tk.Button(m2_frame, text="BACK", command=lambda: self.robot.set_motors(self.robot.m_speeds[0], -self.m2_speed.get()), width=8).pack()

        # --- RIGHT COLUMN: LEDs ---
        right_col = tk.Frame(main_hw)
        right_col.pack(side="right", fill="y", padx=(5, 0))

        led_title = tk.Label(right_col, text="LEDs", font=("Arial", 10, "bold"))
        led_title.pack()

        self.led_checks = []
        self.led_previews = []
        for i in range(4):
            lf = tk.LabelFrame(right_col, text=f"LED {i+1}", padx=5, pady=5)
            lf.pack(fill="x", pady=2)
            
            # Color Preview Circle/Box
            pre = tk.Label(lf, width=4, height=1, bg="#333", relief="sunken")
            pre.pack(pady=2)
            
            # Checkbox for ON/OFF
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(lf, text="ON", variable=var, command=lambda idx=i: self._on_led_toggle(idx))
            chk.pack()
            
            self.led_checks.append(var)
            self.led_previews.append(pre)

        # 3. Log (Hidden by default)
        self.log_frame = tk.Frame(self.root)
        self.log_text = tk.Text(self.log_frame, height=10, width=50, font=("Courier", 8), state="disabled", bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

        # 4. Footer
        footer = tk.Frame(self.root, bg="#eee", pady=2)
        footer.pack(fill="x", side="bottom")
        self.log_btn = tk.Button(footer, text="🛠️ Show Traffic Log", font=("Arial", 8), command=self.toggle_log)
        self.log_btn.pack(side="left", padx=10)
        tk.Label(footer, text="F1:Scan | F2:Connect | F3:Discon | Space:STOP", font=("Arial", 8), bg="#eee").pack(side="right", padx=10)

    def toggle_log(self):
        if not self.log_visible:
            self.log_frame.pack(fill="both", expand=True)
            self.log_btn.config(text="🙈 Hide Traffic Log")
            self.root.geometry("700x1100")
        else:
            self.log_frame.pack_forget()
            self.log_btn.config(text="🛠️ Show Traffic Log")
            self.root.geometry("700x900")
        self.log_visible = not self.log_visible

    def _bind_keys(self):
        self.root.bind("<KeyPress>", self.handle_keypress)
        self.root.bind("<KeyRelease>", self.handle_keyrelease)
        self.root.bind("<F1>", lambda e: self.start_scan())
        self.root.bind("<F2>", lambda e: self.connect())
        self.root.bind("<F3>", lambda e: self.disconnect())

    def _on_led_toggle(self, idx):
        is_on = self.led_checks[idx].get()
        color_idx = 6 if is_on else 0 # Default to Blue (index 6) when on
        self.led_previews[idx].config(bg=self.hex_colors[color_idx] if is_on else "#333")
        self.robot.set_led(idx, color_idx)

    def handle_keypress(self, event):
        key = event.keysym.lower()
        if key in self.pressed_keys: return
        self.pressed_keys.add(key)
        
        # LED Toggles (1-4)
        if key in "1234":
            idx = int(key) - 1
            self.led_checks[idx].set(not self.led_checks[idx].get())
            self._on_led_toggle(idx)

        self.update_movement()

    def handle_keyrelease(self, event):
        key = event.keysym.lower()
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        self.update_movement()

    def update_movement(self):
        if not self.robot.connected: return
        
        m1_spd = self.m1_speed.get()
        m2_spd = self.m2_speed.get()
        m1, m2 = 0, 0
        
        up = 'up' in self.pressed_keys or 'w' in self.pressed_keys
        down = 'down' in self.pressed_keys or 's' in self.pressed_keys
        left = 'left' in self.pressed_keys or 'a' in self.pressed_keys
        right = 'right' in self.pressed_keys or 'd' in self.pressed_keys

        if up: m1, m2 = m1_spd, m2_spd
        elif down: m1, m2 = -m1_spd, -m2_spd
        elif left: m1, m2 = -m1_spd, m2_spd
        elif right: m1, m2 = m1_spd, -m2_spd
        
        # Individual Overrides (Q/E for M1, I/K for M2)
        if 'q' in self.pressed_keys: m1 = m1_spd
        if 'e' in self.pressed_keys: m1 = -m1_spd
        if 'i' in self.pressed_keys: m2 = m2_spd
        if 'k' in self.pressed_keys: m2 = -m2_spd

        if 'space' in self.pressed_keys: m1, m2 = 0, 0
        self.robot.set_motors(m1, m2)

    def manual_master(self, m1, m2):
        # Use current individual speeds for the master drive buttons
        s1 = self.m1_speed.get() if m1 > 0 else -self.m1_speed.get() if m1 < 0 else 0
        s2 = self.m2_speed.get() if m2 > 0 else -self.m2_speed.get() if m2 < 0 else 0
        self.robot.set_motors(s1, s2)

    def log_message(self, direction, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {direction}: {msg}\n"
        self.root.after(0, lambda: self._write_to_log(line))

    def _write_to_log(self, line):
        self.log_text.config(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def connect(self):
        self.status_lbl.config(text="Connecting...", fg="orange")
        self.robot.connect(self.on_connection_result)

    def disconnect(self):
        self.robot.disconnect()
        self.status_lbl.config(text="Disconnected", fg="red")
        self.disconn_btn.config(state="disabled")
        self.conn_btn.config(state="normal")

    def on_connection_result(self, success):
        if success: self.root.after(0, self._conn_ok)
        else: self.root.after(0, self._conn_fail)

    def _conn_ok(self):
        self.status_lbl.config(text="CONNECTED 🤖", fg="green")
        self.disconn_btn.config(state="normal")
        self.conn_btn.config(state="disabled")

    def _conn_fail(self):
        self.status_lbl.config(text="FAILED ❌", fg="red")
        messagebox.showerror("Error", "Connect failed")

    def start_scan(self):
        self.status_lbl.config(text="Scanning...", fg="blue")
        future = asyncio.run_coroutine_threadsafe(self.robot.scan(), self.robot.loop)
        threading.Thread(target=lambda: self._scan_done(future.result()), daemon=True).start()

    def _scan_done(self, address):
        if address: 
            self.root.after(0, lambda: self.status_lbl.config(text=f"Ready: {address}", fg="green"))
            self.robot.address = address
        else:
            self.root.after(0, lambda: self.status_lbl.config(text="No robot", fg="red"))

    def handle_sensor_data(self, type, value):
        if type == "battery": 
            self.root.after(0, lambda: self._update_battery(value))
        elif type == "ir1":
            self.root.after(0, lambda: self._update_ir_bar(self.ir1_canvas, self.ir1_rect, value))
        elif type == "ir2":
            self.root.after(0, lambda: self._update_ir_bar(self.ir2_canvas, self.ir2_rect, value))

    def _update_battery(self, value):
        self.batt_bar['value'] = value
        self.batt_lbl.config(text=f"{value}%")

    def _update_ir_bar(self, canvas, rect, value):
        height = max(min(int(value), 200), 0)
        y_pos = 200 - height
        color = "red" if height < 50 else "yellow" if height < 120 else "green"
        canvas.coords(rect, 0, y_pos, 20, 200)
        canvas.itemconfig(rect, fill=color)

if __name__ == "__main__":
    root = tk.Tk()
    app = ApitorGui(root, "F9:F6:9F:FD:09:4A")
    root.mainloop()
