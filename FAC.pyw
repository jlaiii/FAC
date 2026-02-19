import sys
import subprocess
import time
import os
import threading
import json
import tkinter as tk
from tkinter import messagebox

# =========================
# AUTO-INSTALL (SAFE)
# =========================
def install_requirements():
    packages = ["customtkinter", "pyautogui", "keyboard", "pillow", "opencv-python", "numpy"]
    for package in packages:
        try:
            module = "cv2" if package == "opencv-python" else package
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

import customtkinter as ctk
import pyautogui
import keyboard
import cv2
import numpy as np
from PIL import Image, ImageGrab

# =========================
# PATHS & CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "fac_settings.json")
TARGET_IMG = os.path.join(BASE_DIR, "target.png")

DEFAULT_SETTINGS = {
    "confidence": "80%", 
    "delay": "0.05s", 
    "autostart": False, 
    "restore_mouse": True
}

def save_settings(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def load_settings():
    settings = DEFAULT_SETTINGS.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                settings.update(loaded)
        except: pass
    return settings

# =========================
# SELECTOR TOOL
# =========================
class RegionSelector(tk.Toplevel):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.attributes("-alpha", 0.4)
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.config(bg="black", cursor="cross")
        self.canvas = tk.Canvas(self, cursor="cross", bg="grey20", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.start_x = self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='#00ffff', width=2)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        bbox = (min(self.start_x, event.x), min(self.start_y, event.y), 
                max(self.start_x, event.x), max(self.start_y, event.y))
        self.destroy()
        if (bbox[2] - bbox[0]) > 5:
            self.callback(bbox)

# =========================
# SETTINGS MODAL
# =========================
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("FAC Settings")
        self.geometry("320x540")
        self.parent = parent
        self.attributes("-topmost", True)
        self.resizable(False, False)

        ctk.CTkLabel(self, text="PREFERENCES", font=("Arial", 16, "bold")).pack(pady=15)

        ctk.CTkLabel(self, text="Confidence Level:").pack()
        self.conf_box = ctk.CTkComboBox(self, values=["60%", "70%", "80%", "90%", "100%"])
        self.conf_box.pack(pady=5)

        ctk.CTkLabel(self, text="Scan Delay:").pack()
        self.delay_options = ["0.01s", "0.05s", "0.1s", "0.5s", "1s", "2s", "5s", "10s", "30s", "1m", "2m", "5m"]
        self.delay_box = ctk.CTkComboBox(self, values=self.delay_options)
        self.delay_box.pack(pady=5)

        self.mouse_check = ctk.CTkCheckBox(self, text="Restore mouse position after click")
        self.mouse_check.pack(pady=(20, 10), padx=20, anchor="w")

        self.auto_check = ctk.CTkCheckBox(self, text="Auto-start after capture")
        self.auto_check.pack(pady=10, padx=20, anchor="w")

        self.set_ui_from_config(parent.config)

        # Buttons
        ctk.CTkButton(self, text="SAVE CONFIGURATION", command=self.apply, fg_color="#1f538d").pack(pady=(20, 10))
        ctk.CTkButton(self, text="RESET TO DEFAULT", command=self.reset_to_default, fg_color="#444444", hover_color="#660000").pack(pady=10)

    def set_ui_from_config(self, config_data):
        self.conf_box.set(config_data["confidence"])
        self.delay_box.set(config_data["delay"])
        
        if config_data["restore_mouse"]: self.mouse_check.select()
        else: self.mouse_check.deselect()
            
        if config_data["autostart"]: self.auto_check.select()
        else: self.auto_check.deselect()

    def reset_to_default(self):
        if messagebox.askyesno("Reset", "Restore all settings to default values?"):
            self.set_ui_from_config(DEFAULT_SETTINGS)

    def apply(self):
        self.parent.config["confidence"] = self.conf_box.get()
        self.parent.config["delay"] = self.delay_box.get()
        self.parent.config["autostart"] = self.auto_check.get()
        self.parent.config["restore_mouse"] = self.mouse_check.get()
        save_settings(self.parent.config)
        self.destroy()

# =========================
# MAIN APP
# =========================
class FAC(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FAC")
        self.geometry("340x420")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        
        self.config = load_settings()
        self.target_np = None
        self.running = False

        if os.path.exists(TARGET_IMG):
            self.load_target_to_memory()

        self.setup_ui()

    def load_target_to_memory(self):
        try:
            img = Image.open(TARGET_IMG).convert("RGB")
            self.target_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        except:
            self.target_np = None

    def setup_ui(self):
        ctk.CTkLabel(self, text="FAC", font=("Impact", 42)).pack(pady=(25, 5))
        ctk.CTkLabel(self, text="Find And Click", font=("Arial", 14, "italic"), text_color="#aaaaaa").pack(pady=(0, 25))

        self.btn_capture = ctk.CTkButton(self, text="SET TARGET AREA", height=45, fg_color="#E67E22", hover_color="#D35400", font=("Arial", 14, "bold"), command=self.trigger_capture)
        self.btn_capture.pack(pady=10, padx=50, fill="x")

        self.btn_run = ctk.CTkButton(self, text="START BOT", height=60, fg_color="#27AE60", hover_color="#219150", font=("Arial", 16, "bold"), command=self.toggle_bot)
        self.btn_run.pack(pady=10, padx=50, fill="x")

        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(side="bottom", fill="x", pady=20)

        ctk.CTkButton(self.footer, text="Settings", width=80, fg_color="#34495E", command=lambda: SettingsWindow(self)).pack(side="left", padx=30)
        self.lbl_status = ctk.CTkLabel(self.footer, text="● IDLE", text_color="grey")
        self.lbl_status.pack(side="right", padx=30)

    def trigger_capture(self):
        RegionSelector(self.save_capture)

    def save_capture(self, bbox):
        img = ImageGrab.grab(bbox=bbox)
        img.save(TARGET_IMG)
        self.load_target_to_memory()
        
        if self.config.get("autostart"):
            if not self.running: 
                self.after(200, self.toggle_bot)

    def toggle_bot(self):
        if not self.running:
            if self.target_np is None:
                return messagebox.showwarning("FAC", "No target image found! Set a target area first.")
            
            self.running = True
            self.btn_run.configure(text="STOP (ESC)", fg_color="#C0392B")
            self.lbl_status.configure(text="● ACTIVE", text_color="#2ecc71")
            threading.Thread(target=self.logic_loop, daemon=True).start()
        else:
            self.running = False
            self.btn_run.configure(text="START BOT", fg_color="#27AE60")
            self.lbl_status.configure(text="● IDLE", text_color="grey")

    def parse_delay(self, delay_str):
        if 'm' in delay_str:
            return float(delay_str.replace('m', '')) * 60
        return float(delay_str.replace('s', ''))

    def logic_loop(self):
        pyautogui.PAUSE = 0
        
        while self.running:
            if keyboard.is_pressed("esc"):
                self.after(0, self.toggle_bot)
                break
            try:
                c_val = float(self.config["confidence"].replace("%", "")) / 100
                d_val = self.parse_delay(self.config["delay"])

                screen = np.array(ImageGrab.grab().convert("RGB"))
                gray_scr = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
                res = cv2.matchTemplate(gray_scr, self.target_np, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val >= c_val:
                    h, w = self.target_np.shape
                    orig_pos = pyautogui.position()
                    pyautogui.click(max_loc[0] + w//2, max_loc[1] + h//2)
                    
                    if self.config.get("restore_mouse"):
                        pyautogui.moveTo(orig_pos) 
                    
                    time.sleep(0.5) 

                time.sleep(d_val)
            except: 
                time.sleep(0.1)

if __name__ == "__main__":
    app = FAC()
    app.mainloop()