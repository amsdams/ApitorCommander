import tkinter as tk
from tkinter import messagebox
from apitor_robot import ApitorRobot

class ApitorGui:
    def __init__(self, root, robot_address):
        self.root = root
        self.root.title("Apitor Robot Controller")
        self.root.geometry("350x450")

        # Backend Robot instance
        self.robot = ApitorRobot(robot_address)
        self.robot.on_sensor_data = self.handle_sensor_data

        # Status Label
        self.status_lbl = tk.Label(root, text="Disconnected", font=("Arial", 12), fg="red")
        self.status_lbl.pack(pady=10)

        # Connect Button
        self.conn_btn = tk.Button(root, text="CONNECT", command=self.connect, width=20, bg="#4CAF50", fg="white")
        self.conn_btn.pack(pady=5)

        # Distance Sensor Display
        self.dist_lbl = tk.Label(root, text="Distance: --", font=("Courier", 14))
        self.dist_lbl.pack(pady=20)

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
        self.robot.connect(self.on_connection_result)

    def on_connection_result(self, success):
        if success:
            self.root.after(0, lambda: self.status_lbl.config(text="Connected", fg="green"))
        else:
            self.root.after(0, self.handle_conn_fail)

    def handle_conn_fail(self):
        self.status_lbl.config(text="Disconnected", fg="red")
        self.conn_btn.config(state="normal")
        messagebox.showerror("Bluetooth Error", "Could not connect to the robot.")

    def handle_sensor_data(self, type, value):
        if type == "distance":
            self.root.after(0, lambda: self.dist_lbl.config(text=f"Distance: {value}"))

if __name__ == "__main__":
    # Change the address below if your robot's MAC address is different
    ROBOT_MAC = "F9:F6:9F:FD:09:4A"
    
    root = tk.Tk()
    app = ApitorGui(root, ROBOT_MAC)
    root.mainloop()
