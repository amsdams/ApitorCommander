import asyncio
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from apitor_robot import ApitorRobot

class ApitorGui:
    """
    User Interface for the Apitor Master Hardware Controller.
    Displays keyboard shortcuts directly next to each control.
    """
    
    def __init__(self, root, robot_address):
        self.root = root
        self.root.title("Apitor Master Hardware Controller")
        
        # Initialize Backend
        self.robot = ApitorRobot(robot_address)
        self.robot.on_sensor_data = self._on_sensor_update
        self.robot.on_log = self._on_traffic_log

        # Local UI State
        self.log_visible = False
        self.pressed_keys = set()
        self.colors = ["Off", "Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Violet"]
        self.hex_colors = ["#333", "#ff0000", "#ffa500", "#ffff00", "#00ff00", "#00ffff", "#0000ff", "#ee82ee"]
        self.led_labels = ["Front Left", "Front Right", "Back Left", "Back Right"]
        
        # UI Button References for highlighting
        self.btn_map = {} # Maps keysym or logic-key to tk.Button
        # Capture default background to avoid platform-specific color name errors
        self.default_btn_bg = root.cget("bg")

        self._setup_ui()
        self._bind_keys()
        
        # Finalize and show
        self.root.update_idletasks()
        self._resize_to_fit()

    def _setup_ui(self):
        """Builds all UI panels in a vertical stack."""
        self._setup_connection_panel()
        self._setup_battery_panel()
        self._setup_sensor_panel()
        self._setup_drive_panel()
        self._setup_motor_panel()
        self._setup_led_panel()
        self._setup_log_panel()
        self._setup_footer()

    def _setup_connection_panel(self):
        f = tk.LabelFrame(self.root, text="System Connection", padx=10, pady=5)
        f.pack(fill="x", padx=15, pady=5)
        self.status_lbl = tk.Label(f, text="Status: Disconnected", font=("Arial", 10, "bold"), fg="red")
        self.status_lbl.pack(side="left")
        tk.Button(f, text="Scan [F1]", command=self.start_scan, width=12).pack(side="right", padx=5)
        self.disconn_btn = tk.Button(f, text="Disconnect [F3]", command=self.disconnect, state="disabled", width=12).pack(side="right", padx=5)
        self.conn_btn = tk.Button(f, text="Connect [F2]", command=self.connect, bg="#4CAF50", fg="white", width=12)
        self.conn_btn.pack(side="right", padx=5)

    def _setup_battery_panel(self):
        f = tk.LabelFrame(self.root, text="Battery Status", padx=10, pady=5)
        f.pack(fill="x", padx=15, pady=5)
        self.batt_bar = ttk.Progressbar(f, orient="horizontal", mode="determinate", maximum=130)
        self.batt_bar.pack(side="left", fill="x", expand=True, padx=10)
        self.batt_lbl = tk.Label(f, text="-- (raw)", font=("Courier", 10, "bold"), width=12)
        self.batt_lbl.pack(side="right")

    def _setup_sensor_panel(self):
        outer = tk.Frame(self.root)
        outer.pack(fill="x", padx=15, pady=2)
        self.ir_bars = []; self.ir_rects = []; self.ir_vals = []
        for i, side in enumerate(["Left", "Right"]):
            f = tk.LabelFrame(outer, text=f"Infrared Sensor ({side})", padx=10, pady=5)
            f.pack(side="left", fill="both", expand=True, padx=2)
            canv = tk.Canvas(f, width=50, height=100, bg="#111", highlightthickness=1, highlightbackground="#444")
            canv.pack(pady=5)
            canv.create_rectangle(0, 0, 50, 100, fill="#222", outline="")
            rect = canv.create_rectangle(0, 100, 50, 100, fill="green", outline="")
            self.ir_bars.append(canv); self.ir_rects.append(rect)
            v_lbl = tk.Label(f, text="Value: --", font=("Courier", 10, "bold"))
            v_lbl.pack()
            self.ir_vals.append(v_lbl)

    def _setup_drive_panel(self):
        f = tk.LabelFrame(self.root, text="Master Drive Control [Arrows]", padx=10, pady=10)
        f.pack(fill="x", padx=15, pady=5)
        inner = tk.Frame(f); inner.pack()
        d_grid = tk.Frame(inner); d_grid.pack(side="left", padx=30)
        self.btn_map['up'] = tk.Button(d_grid, text="Both Fwd [▲]", width=12, height=2, command=lambda: self.manual_master(1))
        self.btn_map['up'].grid(row=0, column=1, pady=2)
        self.btn_map['left'] = tk.Button(d_grid, text="Spin Left [◀]", width=12, height=2, command=lambda: self.manual_master(-1, 1))
        self.btn_map['left'].grid(row=1, column=0, padx=2)
        self.btn_map['space'] = tk.Button(d_grid, text="STOP [Space]", width=12, height=2, bg="#f44336", fg="white", font=("Arial", 9, "bold"), command=self.robot.stop)
        self.btn_map['space'].grid(row=1, column=1)
        self.btn_map['right'] = tk.Button(d_grid, text="Spin Right [▶]", width=12, height=2, command=lambda: self.manual_master(1, -1))
        self.btn_map['right'].grid(row=1, column=2, padx=2)
        self.btn_map['down'] = tk.Button(d_grid, text="Both Back [▼]", width=12, height=2, command=lambda: self.manual_master(-1))
        self.btn_map['down'].grid(row=2, column=1, pady=2)
        
        spd_f = tk.Frame(inner); spd_f.pack(side="right", padx=30)
        tk.Label(spd_f, text="Master Speed\nAdjust [ / ] or R / F", font=("Arial", 9, "bold")).pack()
        self.speed_master = tk.Scale(spd_f, from_=100, to=0, orient="vertical", length=140); self.speed_master.set(70); self.speed_master.pack()

    def _setup_motor_panel(self):
        area = tk.Frame(self.root); area.pack(fill="x", padx=15, pady=5)
        # Motor 1 (Left Track)
        m1_f = tk.LabelFrame(area, text="Left Track Control", padx=10, pady=5); m1_f.pack(side="left", fill="both", expand=True, padx=(0, 5))
        m1_btns = tk.Frame(m1_f); m1_btns.pack(side="left", fill="y", padx=10)
        self.btn_map['q'] = tk.Button(m1_btns, text="Forward [Q]", command=lambda: self._move_one(0, 1), width=12)
        self.btn_map['q'].pack(pady=2)
        self.btn_map['z'] = tk.Button(m1_btns, text="STOP [Z]", command=lambda: self._move_one(0, 0), width=12, bg="#ffcdd2")
        self.btn_map['z'].pack(pady=2)
        self.btn_map['a'] = tk.Button(m1_btns, text="Backward [A]", command=lambda: self._move_one(0, -1), width=12)
        self.btn_map['a'].pack(pady=2)
        self.speed_m1 = tk.Scale(m1_f, from_=100, to=0, orient="vertical", length=100, label="Speed [O/K]"); self.speed_m1.set(70); self.speed_m1.pack(side="right", padx=5)
        
        # Motor 2 (Right Track)
        m2_f = tk.LabelFrame(area, text="Right Track Control", padx=10, pady=5); m2_f.pack(side="left", fill="both", expand=True, padx=(5, 0))
        m2_btns = tk.Frame(m2_f); m2_btns.pack(side="left", fill="y", padx=10)
        self.btn_map['w'] = tk.Button(m2_btns, text="Forward [W]", command=lambda: self._move_one(1, 1), width=12)
        self.btn_map['w'].pack(pady=2)
        self.btn_map['x'] = tk.Button(m2_btns, text="STOP [X]", command=lambda: self._move_one(1, 0), width=12, bg="#ffcdd2")
        self.btn_map['x'].pack(pady=2)
        self.btn_map['s'] = tk.Button(m2_btns, text="Backward [S]", command=lambda: self._move_one(1, -1), width=12)
        self.btn_map['s'].pack(pady=2)
        self.speed_m2 = tk.Scale(m2_f, from_=100, to=0, orient="vertical", length=100, label="Speed [P/L]"); self.speed_m2.set(70); self.speed_m2.pack(side="right", padx=5)

    def _setup_led_panel(self):
        f = tk.LabelFrame(self.root, text="Light Emitting Diode (LED) Control", padx=10, pady=5); f.pack(fill="x", padx=15, pady=5)
        self.led_vars = []; self.led_previews = []
        for i in range(4):
            lf = tk.Frame(f); lf.pack(fill="x", pady=4)
            tk.Label(lf, text=f"{self.led_labels[i]} [{i+1}]:", width=18, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
            pre = tk.Label(lf, width=3, height=1, bg="#333", relief="sunken"); pre.pack(side="left", padx=10)
            self.led_previews.append(pre)
            v = tk.IntVar(value=0); self.led_vars.append(v)
            for c_idx, c_name in enumerate(self.colors):
                tk.Radiobutton(lf, text=c_name, variable=v, value=c_idx, command=lambda idx=i: self._on_led_radio_change(idx), font=("Arial", 8)).pack(side="left", padx=4)

    def _setup_log_panel(self):
        self.log_frame = tk.Frame(self.root)
        self.log_text = tk.Text(self.log_frame, height=12, font=("Courier", 8), state="disabled", bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.pack(fill="both", expand=True, padx=15, pady=5)

    def _setup_footer(self):
        f = tk.Frame(self.root, bg="#eee", pady=5); f.pack(fill="x", side="bottom")
        self.log_btn = tk.Button(f, text="Show Traffic Log [Ctrl+L]", font=("Arial", 8), command=self.toggle_log); self.log_btn.pack(side="left", padx=20)
        tk.Label(f, text="Active: Arrows (Master) | QAZ / WSX (Tracks) | OK/PL (Track Spd) | 1-4 | RF | Space", font=("Arial", 8, "bold"), bg="#eee").pack(side="right", padx=20)

    # --- Core Logic & Handlers ---

    def _resize_to_fit(self):
        req_w, req_h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        self.root.geometry(f"{req_w + 40}x{req_h + 40}")

    def toggle_log(self):
        if not self.log_visible:
            self.log_frame.pack(fill="both", expand=True)
            self.log_btn.config(text="Hide Traffic Log [Ctrl+L]")
        else:
            self.log_frame.pack_forget()
            self.log_btn.config(text="Show Traffic Log [Ctrl+L]")
        self.log_visible = not self.log_visible
        self.root.update_idletasks(); self._resize_to_fit()

    def _bind_keys(self):
        self.root.bind("<KeyPress>", self._handle_keypress)
        self.root.bind("<KeyRelease>", self._handle_keyrelease)
        self.root.bind("<F1>", lambda e: self.start_scan())
        self.root.bind("<F2>", lambda e: self.connect())
        self.root.bind("<F3>", lambda e: self.disconnect())

    def _handle_keypress(self, event):
        key = event.keysym.lower()
        if key not in self.pressed_keys:
            self.pressed_keys.add(key)
            
            # Visual Feedback: Highlight Button
            if key in self.btn_map:
                self.btn_map[key].config(relief="sunken", bg="#90caf9")
            
            # 1-4: Cycle Colors
            if key in "1234":
                idx = int(key) - 1
                new_idx = (self.led_vars[idx].get() + 1) % len(self.colors)
                self.led_vars[idx].set(new_idx)
                self._on_led_radio_change(idx)
            
            # [ / ] or R / F: Adjust Speed
            if key in ["bracketright", "r"]: self.speed_master.set(min(self.speed_master.get() + 10, 100))
            if key in ["bracketleft", "f"]: self.speed_master.set(max(self.speed_master.get() - 10, 0))
            
            # O / K: Adjust Left Track Speed
            if key == "o": self.speed_m1.set(min(self.speed_m1.get() + 10, 100))
            if key == "k": self.speed_m1.set(max(self.speed_m1.get() - 10, 0))

            # P / L: Adjust Right Track Speed
            if key == "p": self.speed_m2.set(min(self.speed_m2.get() + 10, 100))
            if key == "l": self.speed_m2.set(max(self.speed_m2.get() - 10, 0))

            # Ctrl+L: Toggle Log
            if key == "l" and (event.state & 0x4):
                self.toggle_log()
            
            self._update_movement()

    def _handle_keyrelease(self, event):
        key = event.keysym.lower()
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
            
            # Visual Feedback: Reset Button
            if key in self.btn_map:
                # Restore original style
                if key == "space": 
                    self.btn_map[key].config(relief="raised", bg="#f44336")
                elif key in ["z", "x"]:
                    self.btn_map[key].config(relief="raised", bg="#ffcdd2")
                else:
                    self.btn_map[key].config(relief="raised", bg=self.default_btn_bg)
                
        self._update_movement()

    def _update_movement(self):
        if not self.robot.connected: return
        ms = self.speed_master.get()
        m1_s, m2_s = self.speed_m1.get(), self.speed_m2.get()
        pk = self.pressed_keys
        m1, m2 = 0, 0
        
        # 1. Pro Tank Layout (QA for Left, WS for Right)
        if 'q' in pk: m1 = m1_s
        elif 'a' in pk: m1 = -m1_s
        
        if 'w' in pk: m2 = m2_s
        elif 's' in pk: m2 = -m2_s
        
        # Independent Brakes (Z for Left, X for Right)
        if 'z' in pk: m1 = 0
        if 'x' in pk: m2 = 0
        
        # 2. Master Overrides (Arrows) - Only if not using independent track controls
        if not (m1 or m2 or 'z' in pk or 'x' in pk):
            up = 'up' in pk
            down = 'down' in pk
            left = 'left' in pk
            right = 'right' in pk
            
            if up: m1, m2 = ms, ms
            elif down: m1, m2 = -ms, -ms
            elif left: m1, m2 = -ms, ms
            elif right: m1, m2 = ms, -ms
        
        if 'space' in pk: m1, m2 = 0, 0
        self.robot.set_motors(m1, m2)

    def manual_master(self, dir1, dir2=None):
        if dir2 is None: dir2 = dir1
        s = self.speed_master.get()
        self.robot.set_motors(dir1 * s, dir2 * s)

    def _move_one(self, motor_idx, direction):
        spd = self.speed_m1.get() if motor_idx == 0 else self.speed_m2.get()
        if motor_idx == 0: self.robot.set_motors(direction * spd, self.robot.m_speeds[1])
        else: self.robot.set_motors(self.robot.m_speeds[0], direction * spd)

    def _on_led_radio_change(self, idx):
        c_idx = self.led_vars[idx].get()
        self.led_previews[idx].config(bg=self.hex_colors[c_idx])
        self.robot.set_led(idx, c_idx)

    # --- Callbacks ---
    def _on_sensor_update(self, data_type, value):
        if data_type == "battery": self.root.after(0, lambda: self._update_battery_ui(value))
        elif data_type.startswith("ir"):
            idx = 0 if data_type == "ir1" else 1
            self.root.after(0, lambda: self._update_ir_ui(idx, value))

    def _on_traffic_log(self, direction, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {direction}: {msg}\n"
        self.root.after(0, lambda: self._write_to_log_ui(line))

    def _update_battery_ui(self, value):
        self.batt_bar['value'] = value
        self.batt_lbl.config(text=f"{value} (raw)")

    def _update_ir_ui(self, idx, value):
        canv, rect, v_lbl = self.ir_bars[idx], self.ir_rects[idx], self.ir_vals[idx]
        v_lbl.config(text=f"Value: {value}")
        scaled_val = max(min(int(value), 10), 0)
        height = (scaled_val / 10) * 100
        color = "red" if scaled_val > 7 else "yellow" if scaled_val > 3 else "green"
        canv.coords(rect, 0, 100 - height, 50, 100)
        canv.itemconfig(rect, fill=color)

    def _write_to_log_ui(self, line):
        self.log_text.config(state="normal"); self.log_text.insert("end", line); self.log_text.see("end"); self.log_text.config(state="disabled")

    def connect(self):
        self.status_lbl.config(text="Status: Connecting...", fg="orange"); self.robot.connect(self._on_connection_result)

    def disconnect(self):
        self.robot.disconnect(); self.status_lbl.config(text="Status: Disconnected", fg="red")
        self.disconn_btn.config(state="disabled"); self.conn_btn.config(state="normal")

    def _on_connection_result(self, success):
        self.root.after(0, lambda: self._handle_conn_result_ui(success))

    def _handle_conn_result_ui(self, success):
        if success:
            self.status_lbl.config(text="Status: Connected", fg="green")
            self.disconn_btn.config(state="normal"); self.conn_btn.config(state="disabled")
        else:
            self.status_lbl.config(text="Status: Failed", fg="red"); messagebox.showerror("Error", "Connect failed")

    def start_scan(self):
        self.status_lbl.config(text="Status: Scanning...", fg="blue")
        future = asyncio.run_coroutine_threadsafe(self.robot.scan(), self.robot.loop)
        threading.Thread(target=lambda: self._handle_scan_result(future.result()), daemon=True).start()

    def _handle_scan_result(self, address):
        msg = f"Status: Found {address}" if address else "Status: No robot found"
        color = "green" if address else "red"
        self.root.after(0, lambda: self.status_lbl.config(text=msg, fg=color))
        if address: self.robot.address = address

if __name__ == "__main__":
    root = tk.Tk()
    app = ApitorGui(root, "F9:F6:9F:FD:09:4A")
    root.mainloop()
