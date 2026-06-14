import asyncio
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from apitor_robot import ApitorRobot

class ApitorGui:
    def __init__(self, root, robot_address):
        self.root = root
        self.root.title("Apitor Master Hardware Controller")
        
        # Backend Robot instance
        self.robot = ApitorRobot(robot_address)
        self.robot.on_sensor_data = self.handle_sensor_data
        self.robot.on_log = self.log_message

        # State & Settings
        self.log_visible = False
        self.pressed_keys = set()
        self.colors = ["Off", "Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Violet"]
        self.hex_colors = ["#333", "#ff0000", "#ffa500", "#ffff00", "#00ff00", "#00ffff", "#0000ff", "#ee82ee"]
        self.led_labels = ["Front Left", "Front Right", "Back Left", "Back Right"]

        self._setup_ui()
        self._bind_keys()
        
        # DYNAMIC SIZING
        self.root.update_idletasks()
        self._resize_to_fit()

    def _resize_to_fit(self):
        req_w = self.root.winfo_reqwidth()
        req_h = self.root.winfo_reqheight()
        # Add a comfortable buffer
        self.root.geometry(f"{req_w + 40}x{req_h + 40}")

    def _setup_ui(self):
        # 1. Connection Panel
        conn_frame = tk.LabelFrame(self.root, text="System Connection", padx=10, pady=5)
        conn_frame.pack(fill="x", padx=15, pady=5)
        
        self.status_lbl = tk.Label(conn_frame, text="Status: Disconnected", font=("Arial", 10, "bold"), fg="red")
        self.status_lbl.pack(side="left")
        
        tk.Button(conn_frame, text="Scan (F1)", command=self.start_scan, width=12).pack(side="right", padx=5)
        self.disconn_btn = tk.Button(conn_frame, text="Disconnect (F3)", command=self.disconnect, state="disabled", width=12)
        self.disconn_btn.pack(side="right", padx=5)
        self.conn_btn = tk.Button(conn_frame, text="Connect (F2)", command=self.connect, bg="#4CAF50", fg="white", width=12)
        self.conn_btn.pack(side="right", padx=5)

        # 2. Battery Status Panel
        batt_frame = tk.LabelFrame(self.root, text="Battery Status", padx=10, pady=5)
        batt_frame.pack(fill="x", padx=15, pady=5)
        # Using maximum 130 since raw values are around 110-120
        self.batt_bar = ttk.Progressbar(batt_frame, orient="horizontal", mode="determinate", maximum=130)
        self.batt_bar.pack(side="left", fill="x", expand=True, padx=10)
        self.batt_lbl = tk.Label(batt_frame, text="-- (raw)", font=("Courier", 10, "bold"), width=12)
        self.batt_lbl.pack(side="right")

        # 3. Infrared Sensors Area
        ir_outer = tk.Frame(self.root)
        ir_outer.pack(fill="x", padx=15, pady=2)
        self.ir_bars = []; self.ir_rects = []; self.ir_vals = []
        
        for i, side in enumerate(["Left", "Right"]):
            f = tk.LabelFrame(ir_outer, text=f"Infrared Sensor ({side})", padx=10, pady=5)
            f.pack(side="left", fill="both", expand=True, padx=2)
            
            canv = tk.Canvas(f, width=50, height=100, bg="#111", highlightthickness=1, highlightbackground="#444")
            canv.pack(pady=5)
            # Full height background rect
            canv.create_rectangle(0, 0, 50, 100, fill="#222", outline="")
            # Responsive rect
            rect = canv.create_rectangle(0, 100, 50, 100, fill="green", outline="")
            self.ir_bars.append(canv); self.ir_rects.append(rect)
            
            # Value Label
            v_lbl = tk.Label(f, text="Value: --", font=("Courier", 10, "bold"))
            v_lbl.pack()
            self.ir_vals.append(v_lbl)

        # 4. Master Drive Panel
        master_frame = tk.LabelFrame(self.root, text="Master Drive Control (WASD / Arrows)", padx=10, pady=10)
        master_frame.pack(fill="x", padx=15, pady=5)
        master_inner = tk.Frame(master_frame)
        master_inner.pack()

        d_grid = tk.Frame(master_inner)
        d_grid.pack(side="left", padx=30)
        tk.Button(d_grid, text="Forward", width=10, height=2, command=lambda: self.manual_master(1)).grid(row=0, column=1, pady=2)
        tk.Button(d_grid, text="Turn Left", width=10, height=2, command=lambda: self.manual_master(-1, 1)).grid(row=1, column=0, padx=2)
        tk.Button(d_grid, text="STOP", width=10, height=2, bg="#f44336", fg="white", font=("Arial", 9, "bold"), command=self.robot.stop).grid(row=1, column=1)
        tk.Button(d_grid, text="Turn Right", width=10, height=2, command=lambda: self.manual_master(1, -1)).grid(row=1, column=2, padx=2)
        tk.Button(d_grid, text="Backward", width=10, height=2, command=lambda: self.manual_master(-1)).grid(row=2, column=1, pady=2)

        spd_master_f = tk.Frame(master_inner)
        spd_master_f.pack(side="right", padx=30)
        tk.Label(spd_master_f, text="Master Speed", font=("Arial", 9, "bold")).pack()
        self.speed_master = tk.Scale(spd_master_f, from_=100, to=0, orient="vertical", length=140)
        self.speed_master.set(70)
        self.speed_master.pack()

        # 5. Individual Motor Control Area
        motor_area = tk.Frame(self.root)
        motor_area.pack(fill="x", padx=15, pady=5)

        # Motor 1
        m1_f = tk.LabelFrame(motor_area, text="Motor 1 (Left Side)", padx=10, pady=5)
        m1_f.pack(side="left", fill="both", expand=True, padx=(0, 5))
        m1_btns = tk.Frame(m1_f)
        m1_btns.pack(side="left", fill="y", padx=10)
        tk.Button(m1_btns, text="Forward", command=lambda: self.robot.set_motors(self.speed_m1.get(), self.robot.m_speeds[1]), width=12).pack(pady=2)
        tk.Button(m1_btns, text="STOP", command=lambda: self.robot.set_motors(0, self.robot.m_speeds[1]), width=12, bg="#ffcdd2").pack(pady=2)
        tk.Button(m1_btns, text="Backward", command=lambda: self.robot.set_motors(-self.speed_m1.get(), self.robot.m_speeds[1]), width=12).pack(pady=2)
        self.speed_m1 = tk.Scale(m1_f, from_=100, to=0, orient="vertical", length=100, label="Speed")
        self.speed_m1.set(70); self.speed_m1.pack(side="right", padx=5)

        # Motor 2
        m2_f = tk.LabelFrame(motor_area, text="Motor 2 (Right Side)", padx=10, pady=5)
        m2_f.pack(side="left", fill="both", expand=True, padx=(5, 0))
        m2_btns = tk.Frame(m2_f)
        m2_btns.pack(side="left", fill="y", padx=10)
        tk.Button(m2_btns, text="Forward", command=lambda: self.robot.set_motors(self.robot.m_speeds[0], self.speed_m2.get()), width=12).pack(pady=2)
        tk.Button(m2_btns, text="STOP", command=lambda: self.robot.set_motors(self.robot.m_speeds[0], 0), width=12, bg="#ffcdd2").pack(pady=2)
        tk.Button(m2_btns, text="Backward", command=lambda: self.robot.set_motors(self.robot.m_speeds[0], -self.speed_m2.get()), width=12).pack(pady=2)
        self.speed_m2 = tk.Scale(m2_f, from_=100, to=0, orient="vertical", length=100, label="Speed")
        self.speed_m2.set(70); self.speed_m2.pack(side="right", padx=5)

        # 6. LED Control Area
        led_master = tk.LabelFrame(self.root, text="Light Emitting Diode (LED) Control", padx=10, pady=5)
        led_master.pack(fill="x", padx=15, pady=5)
        self.led_vars = []; self.led_previews = []
        for i in range(4):
            lf = tk.Frame(led_master); lf.pack(fill="x", pady=4)
            tk.Label(lf, text=f"{self.led_labels[i]}:", width=12, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
            pre = tk.Label(lf, width=3, height=1, bg="#333", relief="sunken"); pre.pack(side="left", padx=10)
            self.led_previews.append(pre)
            v = tk.IntVar(value=0); self.led_vars.append(v)
            for c_idx, c_name in enumerate(self.colors):
                tk.Radiobutton(lf, text=c_name, variable=v, value=c_idx, command=lambda idx=i: self._on_led_radio_change(idx), font=("Arial", 8)).pack(side="left", padx=4)

        # 7. Traffic Log
        self.log_frame = tk.Frame(self.root)
        self.log_text = tk.Text(self.log_frame, height=12, font=("Courier", 8), state="disabled", bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.pack(fill="both", expand=True, padx=15, pady=5)

        # 8. Footer
        footer = tk.Frame(self.root, bg="#eee", pady=5); footer.pack(fill="x", side="bottom")
        self.log_btn = tk.Button(footer, text="Show Traffic Log", font=("Arial", 8), command=self.toggle_log); self.log_btn.pack(side="left", padx=20)
        tk.Label(footer, text="WASD: Drive | Space: STOP ALL | F1-F3: System", font=("Arial", 8, "bold"), bg="#eee").pack(side="right", padx=20)

    def toggle_log(self):
        if not self.log_visible:
            self.log_frame.pack(fill="both", expand=True)
            self.log_btn.config(text="Hide Traffic Log")
        else:
            self.log_frame.pack_forget()
            self.log_btn.config(text="Show Traffic Log")
        self.log_visible = not self.log_visible
        self.root.update_idletasks(); self._resize_to_fit()

    def _bind_keys(self):
        self.root.bind("<KeyPress>", self.handle_keypress)
        self.root.bind("<KeyRelease>", self.handle_keyrelease)
        self.root.bind("<F1>", lambda e: self.start_scan())
        self.root.bind("<F2>", lambda e: self.connect())
        self.root.bind("<F3>", lambda e: self.disconnect())

    def _on_led_radio_change(self, idx):
        c_idx = self.led_vars[idx].get()
        self.led_previews[idx].config(bg=self.hex_colors[c_idx])
        self.robot.set_led(idx, c_idx)

    def handle_keypress(self, event):
        key = event.keysym.lower()
        if key in self.pressed_keys: return
        self.pressed_keys.add(key); self.update_movement()

    def handle_keyrelease(self, event):
        key = event.keysym.lower()
        if key in self.pressed_keys: self.pressed_keys.remove(key)
        self.update_movement()

    def update_movement(self):
        if not self.robot.connected: return
        ms = self.speed_master.get(); m1, m2 = 0, 0
        up = 'up' in self.pressed_keys or 'w' in self.pressed_keys
        down = 'down' in self.pressed_keys or 's' in self.pressed_keys
        left = 'left' in self.pressed_keys or 'a' in self.pressed_keys
        right = 'right' in self.pressed_keys or 'd' in self.pressed_keys
        if up: m1, m2 = ms, ms
        elif down: m1, m2 = -ms, -ms
        elif left: m1, m2 = -ms, ms
        elif right: m1, m2 = ms, -ms
        if 'space' in self.pressed_keys: m1, m2 = 0, 0
        self.robot.set_motors(m1, m2)

    def manual_master(self, dir1, dir2=None):
        if dir2 is None: dir2 = dir1
        s = self.speed_master.get(); self.robot.set_motors(dir1 * s, dir2 * s)

    def log_message(self, direction, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {direction}: {msg}\n"
        self.root.after(0, lambda: self._write_to_log(line))

    def _write_to_log(self, line):
        self.log_text.config(state="normal"); self.log_text.insert("end", line); self.log_text.see("end"); self.log_text.config(state="disabled")

    def connect(self):
        self.status_lbl.config(text="Status: Connecting...", fg="orange"); self.robot.connect(self.on_connection_result)

    def disconnect(self):
        self.robot.disconnect(); self.status_lbl.config(text="Status: Disconnected", fg="red")
        self.disconn_btn.config(state="disabled"); self.conn_btn.config(state="normal")

    def on_connection_result(self, success):
        if success: self.root.after(0, self._conn_ok)
        else: self.root.after(0, self._conn_fail)

    def _conn_ok(self):
        self.status_lbl.config(text="Status: Connected", fg="green")
        self.disconn_btn.config(state="normal"); self.conn_btn.config(state="disabled")

    def _conn_fail(self):
        self.status_lbl.config(text="Status: Failed", fg="red"); messagebox.showerror("Error", "Connect failed")

    def start_scan(self):
        self.status_lbl.config(text="Status: Scanning...", fg="blue")
        future = asyncio.run_coroutine_threadsafe(self.robot.scan(), self.robot.loop)
        threading.Thread(target=lambda: self._scan_done(future.result()), daemon=True).start()

    def _scan_done(self, address):
        if address: 
            self.root.after(0, lambda: self.status_lbl.config(text=f"Status: Found {address}", fg="green"))
            self.robot.address = address
        else: self.root.after(0, lambda: self.status_lbl.config(text="Status: No robot found", fg="red"))

    def handle_sensor_data(self, type, value):
        if type == "battery": self.root.after(0, lambda: self._update_battery(value))
        elif type == "ir1": self.root.after(0, lambda: self._update_ir_bar(0, value))
        elif type == "ir2": self.root.after(0, lambda: self._update_ir_bar(1, value))

    def _update_battery(self, value):
        # Handle raw battery values above 100
        self.batt_bar['value'] = value
        self.batt_lbl.config(text=f"{value} (raw)")

    def _update_ir_bar(self, idx, value):
        canv = self.ir_bars[idx]; rect = self.ir_rects[idx]; v_lbl = self.ir_vals[idx]
        v_lbl.config(text=f"Value: {value}")
        
        # SENSITIVITY FIX: If the user says they only see max 6, we use a much smaller scale.
        # Assume 10 is the maximum for a "high sensitivity" view.
        max_expected = 10
        scaled_val = max(min(int(value), max_expected), 0)
        
        bar_height = (scaled_val / max_expected) * 100
        y_top = 100 - bar_height
        
        color = "red" if scaled_val > 7 else "yellow" if scaled_val > 3 else "green"
        canv.coords(rect, 0, y_top, 50, 100)
        canv.itemconfig(rect, fill=color)

if __name__ == "__main__":
    root = tk.Tk()
    app = ApitorGui(root, "F9:F6:9F:FD:09:4A")
    root.mainloop()
