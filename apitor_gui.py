import tkinter as tk
from tkinter import messagebox, ttk
import threading
import asyncio
from apitor_robot import ApitorRobot

class ApitorGui:
    def __init__(self, root, robot_address):
        self.root = root
        self.root.title("Apitor Robot Controller")
        self.root.geometry("400x700")

        # Backend Robot instance
        self.robot = ApitorRobot(robot_address)
        self.robot.on_sensor_data = self.handle_sensor_data

        # Status Label
        self.status_lbl = tk.Label(root, text="Disconnected", font=("Arial", 12), fg="red")
        self.status_lbl.pack(pady=10)

        # Connection Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        
        self.conn_btn = tk.Button(btn_frame, text="CONNECT", command=self.connect, width=12, bg="#4CAF50", fg="white")
        self.conn_btn.pack(side="left", padx=2)

        self.disconn_btn = tk.Button(btn_frame, text="DISCONNECT", command=self.disconnect, width=12, state="disabled")
        self.disconn_btn.pack(side="left", padx=2)

        self.scan_btn = tk.Button(root, text="SCAN FOR ROBOT", command=self.start_scan, width=26)
        self.scan_btn.pack(pady=5)

        # Diagnostics Frame
        diag_frame = tk.LabelFrame(root, text="System Diagnostics", padx=10, pady=10)
        diag_frame.pack(pady=10, padx=20, fill="x")
        
        self.batt_lbl = tk.Label(diag_frame, text="Battery: --%", font=("Courier", 10))
        self.batt_lbl.grid(row=0, column=0, padx=5, sticky="w")
        
        self.ir1_lbl = tk.Label(diag_frame, text="IR1: --", font=("Courier", 10))
        self.ir1_lbl.grid(row=1, column=0, padx=5, sticky="w")
        
        self.ir2_lbl = tk.Label(diag_frame, text="IR2: --", font=("Courier", 10))
        self.ir2_lbl.grid(row=1, column=1, padx=5, sticky="w")

        # LED Control Frame
        led_frame = tk.LabelFrame(root, text="LED Controls", padx=10, pady=10)
        led_frame.pack(pady=5, padx=20, fill="x")
        
        colors = ["Off", "Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Violet"]
        self.led_var = tk.StringVar(value="Blue")
        ttk.OptionMenu(led_frame, self.led_var, "Blue", *colors).pack(side="left", padx=5)
        
        tk.Button(led_frame, text="Set L1", command=lambda: self.set_led(0)).pack(side="left", padx=2)
        tk.Button(led_frame, text="Set L2", command=lambda: self.set_led(1)).pack(side="left", padx=2)
        tk.Button(led_frame, text="Set ALL", command=self.set_all_leds).pack(side="left", padx=2)

        # Motor Control Frame
        ctrl_frame = tk.LabelFrame(root, text="Motor Controls", padx=10, pady=10)
        ctrl_frame.pack(pady=10, padx=20, fill="x")

        # Individual Motor Buttons
        tk.Button(ctrl_frame, text="M1 Forward", command=lambda: self.robot.set_motors(self.speed.get(), 0)).grid(row=0, column=0, sticky="ew", padx=2)
        tk.Button(ctrl_frame, text="M2 Forward", command=lambda: self.robot.set_motors(0, self.speed.get())).grid(row=0, column=1, sticky="ew", padx=2)
        tk.Button(ctrl_frame, text="M1 Back", command=lambda: self.robot.set_motors(-self.speed.get(), 0)).grid(row=1, column=0, sticky="ew", padx=2)
        tk.Button(ctrl_frame, text="M2 Back", command=lambda: self.robot.set_motors(0, -self.speed.get())).grid(row=1, column=1, sticky="ew", padx=2)

        # Combined Controls
        tk.Button(root, text="BOTH FORWARD", command=lambda: self.robot.set_motors(self.speed.get(), self.speed.get())).pack(fill="x", padx=40, pady=2)
        tk.Button(root, text="STOP ALL", bg="red", fg="white", command=self.robot.stop).pack(fill="x", padx=40, pady=5)

        # Speed Slider
        self.speed = tk.Scale(root, from_=0, to=100, orient="horizontal", label="Speed %")
        self.speed.set(60)
        self.speed.pack(fill="x", padx=40)

    def connect(self):
        self.status_lbl.config(text="Connecting...", fg="orange")
        self.conn_btn.config(state="disabled")
        self.scan_btn.config(state="disabled")
        self.robot.connect(self.on_connection_result)

    def disconnect(self):
        self.robot.disconnect()
        self.status_lbl.config(text="Disconnected", fg="red")
        self.conn_btn.config(state="normal")
        self.disconn_btn.config(state="disabled")
        self.scan_btn.config(state="normal")

    def on_connection_result(self, success):
        if success:
            self.root.after(0, self.handle_conn_success)
        else:
            self.root.after(0, self.handle_conn_fail)

    def handle_conn_success(self):
        self.status_lbl.config(text="Connected", fg="green")
        self.disconn_btn.config(state="normal")

    def handle_conn_fail(self):
        self.status_lbl.config(text="Disconnected", fg="red")
        self.conn_btn.config(state="normal")
        self.scan_btn.config(state="normal")
        messagebox.showerror("Bluetooth Error", "Could not connect to the robot.")

    def start_scan(self):
        self.status_lbl.config(text="Scanning...", fg="blue")
        self.scan_btn.config(state="disabled")
        future = asyncio.run_coroutine_threadsafe(self.robot.scan(), self.robot.loop)
        threading.Thread(target=lambda: self.on_scan_finished(future.result()), daemon=True).start()

    def on_scan_finished(self, address):
        self.root.after(0, lambda: self.update_ui_after_scan(address))

    def update_ui_after_scan(self, address):
        self.scan_btn.config(state="normal")
        if address:
            self.status_lbl.config(text=f"Found: {address}", fg="green")
            self.robot.address = address
        else:
            self.status_lbl.config(text="No robot found", fg="red")
            messagebox.showinfo("Scan", "No Apitor robot found nearby.")

    def set_led(self, idx):
        colors = ["Off", "Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Violet"]
        try:
            color_idx = colors.index(self.led_var.get())
            self.robot.set_led(idx, color_idx)
        except ValueError:
            pass

    def set_all_leds(self):
        for i in range(4):
            self.set_led(i)

    def handle_sensor_data(self, type, value):
        if type == "battery":
            self.root.after(0, lambda: self.batt_lbl.config(text=f"Battery: {value}%"))
        elif type == "ir1":
            self.root.after(0, lambda: self.ir1_lbl.config(text=f"IR1: {value}"))
        elif type == "ir2":
            self.root.after(0, lambda: self.ir2_lbl.config(text=f"IR2: {value}"))

if __name__ == "__main__":
    ROBOT_MAC = "F9:F6:9F:FD:09:4A"
    root = tk.Tk()
    app = ApitorGui(root, ROBOT_MAC)
    root.mainloop()
