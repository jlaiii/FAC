import sys, time, os, threading, json, tkinter as tk
from tkinter import messagebox
import ctypes
import customtkinter as ctk
import pyautogui, keyboard, cv2, numpy as np
from PIL import Image, ImageGrab
import pygetwindow as gw
import traceback 

# =========================
# PATHS & CONFIG
# =========================
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "fac_settings.json")
TARGET_IMG = os.path.join(BASE_DIR, "target.png")

DEFAULT_SETTINGS = {
    "confidence": "80%", 
    "delay": "0.05s", 
    "autostart": False, 
    "restore_mouse": True,
    "last_x": 100,
    "last_y": 100,
    "target_window": "Default (Entire Screen)",
    "idle_timeout": "5 mins",
    "idle_action": "Focus + Fullscreen"
}

def save_settings(data):
    with open(CONFIG_FILE, "w") as f: json.dump(data, f)

def load_settings():
    settings = DEFAULT_SETTINGS.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: settings.update(json.load(f))
        except: pass
    return settings

# =========================
# ERROR HANDLING
# =========================
def handle_exception(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(error_msg)
        r.update()
        r.destroy()
    except: pass
    messagebox.showerror("FAC Crash Detected", f"An error occurred and was copied to your clipboard:\n\n{error_msg}")

sys.excepthook = handle_exception

# =========================
# SELECTOR TOOL
# =========================
class RegionSelector(tk.Toplevel):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.attributes("-alpha", 0.4, "-fullscreen", True, "-topmost", True)
        self.config(bg="black", cursor="cross")
        self.canvas = tk.Canvas(self, cursor="cross", bg="grey20", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.start_x = self.start_y = self.rect = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Button-3>", lambda e: self.destroy()) 
        self.bind("<Escape>", lambda e: self.destroy())

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='#00ffff', width=2)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        bbox = (min(self.start_x, event.x), min(self.start_y, event.y), 
                max(self.start_x, event.x), max(self.start_y, event.y))
        self.destroy()
        if (bbox[2] - bbox[0]) > 5: self.callback(bbox)

# =========================
# SETTINGS WINDOW
# =========================
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.attributes("-topmost", False) # Always stay on top disabled
        self.grab_set() 
        
        w, h = 320, 500 
        px = parent.winfo_x() + (parent.winfo_width() // 2) - (w // 2)
        py = parent.winfo_y() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.resizable(False, False)

        ctk.CTkLabel(self, text="PREFERENCES", font=("Arial", 14, "bold")).pack(pady=10)
        
        ctk.CTkLabel(self, text="Confidence Level:", font=("Arial", 11)).pack(pady=(2, 0))
        self.conf_box = ctk.CTkComboBox(self, values=["60%", "70%", "80%", "90%", "100%"], height=28, state="readonly")
        self.conf_box.pack(pady=2)

        ctk.CTkLabel(self, text="Scan Delay (Speed):", font=("Arial", 11)).pack(pady=(2, 0))
        self.delay_box = ctk.CTkComboBox(self, values=["0.01s", "0.05s", "0.1s", "0.5s", "1s", "5s"], height=28, state="readonly")
        self.delay_box.pack(pady=2)

        ctk.CTkLabel(self, text="Idle Re-Focus Timer:", font=("Arial", 11)).pack(pady=(2, 0))
        self.idle_box = ctk.CTkComboBox(self, values=["Off", "10 sec", "30 sec", "1 min", "5 mins", "10 mins"], height=28, state="readonly")
        self.idle_box.pack(pady=2)
        self.idle_box.set(parent.config.get("idle_timeout", "5 mins"))

        ctk.CTkLabel(self, text="Idle Action:", font=("Arial", 11)).pack(pady=(2, 0))
        self.action_box = ctk.CTkComboBox(self, values=["Focus", "Focus + Fullscreen"], height=28, state="readonly")
        self.action_box.pack(pady=2)
        self.action_box.set(parent.config.get("idle_action", "Focus + Fullscreen"))

        self.mouse_check = ctk.CTkCheckBox(self, text="Return mouse to original position", font=("Arial", 11))
        self.mouse_check.pack(pady=8, padx=20, anchor="w")
        
        self.auto_check = ctk.CTkCheckBox(self, text="Start bot automatically after capture", font=("Arial", 11))
        self.auto_check.pack(pady=5, padx=20, anchor="w")

        self.conf_box.set(parent.config.get("confidence", "80%"))
        self.delay_box.set(parent.config.get("delay", "0.05s"))
        if parent.config.get("restore_mouse"): self.mouse_check.select()
        if parent.config.get("autostart"): self.auto_check.select()

        ctk.CTkButton(self, text="SAVE SETTINGS", command=self.apply, height=35, fg_color="#1f538d").pack(pady=15)

    def apply(self):
        self.parent.config.update({
            "confidence": self.conf_box.get(),
            "delay": self.delay_box.get(),
            "idle_timeout": self.idle_box.get(),
            "idle_action": self.action_box.get(),
            "restore_mouse": self.mouse_check.get(),
            "autostart": self.auto_check.get()
        })
        save_settings(self.parent.config)
        self.destroy()

# =========================
# MAIN APP
# =========================
class FAC(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FAC")
        self.config = load_settings()
        
        # Reduced height for a more compact main window
        w, h = 280, 310
        lx, ly = self.config.get("last_x", 100), self.config.get("last_y", 100)
        self.geometry(f"{w}x{h}+{lx}+{ly}")
        self.resizable(False, False)
        self.attributes("-topmost", False) # Always stay on top disabled 
        ctk.set_appearance_mode("dark")
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.target_np = None
        self.running = False
        self.last_click_time = 0
        self.initial_force_triggered = False
        
        if os.path.exists(TARGET_IMG): self.load_target_to_memory()
        self.setup_ui()

    def load_target_to_memory(self):
        try:
            img = Image.open(TARGET_IMG).convert("RGB")
            self.target_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        except: self.target_np = None

    def get_windows(self):
        try:
            titles = [w.title for w in gw.getAllWindows() if w.title.strip()]
            return ["Default (Entire Screen)"] + sorted(list(set(titles)))
        except: return ["Default (Entire Screen)"]

    def setup_ui(self):
        # Header - reduced padding
        ctk.CTkLabel(self, text="FAC", font=("Impact", 28)).pack(pady=(10, 2))
        
        # Action Buttons - more compact
        self.btn_capture = ctk.CTkButton(self, text="SET TARGET", height=32, fg_color="#E67E22", 
                                    command=lambda: RegionSelector(self.save_capture))
        self.btn_capture.pack(pady=5, padx=35, fill="x")

        self.btn_run = ctk.CTkButton(self, text="START BOT", height=40, fg_color="#27AE60", 
                                     font=("Arial", 13, "bold"), command=self.toggle_bot)
        self.btn_run.pack(pady=5, padx=35, fill="x")
        
        # Target Window Section - reduced padding
        ctk.CTkLabel(self, text="Target Window:", font=("Arial", 10)).pack(pady=(5,0))
        self.win_select = ctk.CTkComboBox(self, values=self.get_windows(), height=26, state="readonly", font=("Arial", 11))
        self.win_select.pack(pady=(2, 10), padx=35, fill="x")
        self.win_select.set(self.config.get("target_window", "Default (Entire Screen)"))
        self.win_select.configure(command=self.update_win_config)

        # Footer - packed to the bottom with minimal height
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=(0, 10))
        
        self.btn_settings = ctk.CTkButton(footer, text="⚙ Settings", width=80, height=24, fg_color="#34495E", 
                                        command=lambda: SettingsWindow(self), font=("Arial", 10))
        self.btn_settings.pack(side="left", padx=20)
        
        self.lbl_status = ctk.CTkLabel(footer, text="● IDLE", text_color="grey", font=("Arial", 10))
        self.lbl_status.pack(side="right", padx=20)

    def update_win_config(self, choice):
        self.config["target_window"] = choice
        save_settings(self.config)

    def on_close(self):
        self.config["last_x"] = self.winfo_x()
        self.config["last_y"] = self.winfo_y()
        save_settings(self.config)
        self.destroy()

    def save_capture(self, bbox):
        ImageGrab.grab(bbox=bbox).save(TARGET_IMG)
        self.load_target_to_memory()
        if self.config.get("autostart") and not self.running: 
            self.after(200, self.toggle_bot)

    def toggle_bot(self):
        if not self.running:
            if self.target_np is None: 
                messagebox.showwarning("FAC", "Please set a target image first.")
                return
            self.running = True
            self.initial_force_triggered = False 
            self.last_click_time = time.time() 
            self.btn_run.configure(text="STOP (ESC)", fg_color="#C0392B")
            self.lbl_status.configure(text="● ACTIVE", text_color="#2ecc71")
            threading.Thread(target=self.logic_loop, daemon=True).start()
        else:
            self.running = False
            self.btn_run.configure(text="START BOT", fg_color="#27AE60")
            self.lbl_status.configure(text="● IDLE", text_color="grey")

    def logic_loop(self):
        pyautogui.PAUSE = 0
        while self.running:
            if keyboard.is_pressed("esc"):
                self.after(0, self.toggle_bot)
                break
            try:
                conf_val = float(self.config["confidence"].replace("%", "")) / 100
                delay_val = float(self.config["delay"].replace('s',''))
                target_title = self.config.get("target_window", "Default (Entire Screen)")
                idle_setting = self.config.get("idle_timeout", "5 mins")
                
                if target_title != "Default (Entire Screen)":
                    if not self.initial_force_triggered:
                        threshold = 5 
                    else:
                        if "sec" in idle_setting:
                            threshold = int(idle_setting.split()[0])
                        elif "min" in idle_setting:
                            threshold = int(idle_setting.split()[0]) * 60
                        else:
                            threshold = 9999999

                    if (time.time() - self.last_click_time) >= threshold:
                        wins = gw.getWindowsWithTitle(target_title)
                        if wins:
                            try:
                                win = wins[0]
                                win.activate()
                                if self.config.get("idle_action") == "Focus + Fullscreen":
                                    win.maximize()
                                time.sleep(0.1)
                            except: pass
                            self.last_click_time = time.time()
                            self.initial_force_triggered = True 

                screen = np.array(ImageGrab.grab().convert("RGB"))
                gray_scr = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
                res = cv2.matchTemplate(gray_scr, self.target_np, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val >= conf_val:
                    self.last_click_time = time.time()
                    self.initial_force_triggered = True 
                    h, w = self.target_np.shape
                    orig_pos = pyautogui.position()
                    pyautogui.click(max_loc[0] + w//2, max_loc[1] + h//2)
                    if self.config.get("restore_mouse"):
                        pyautogui.moveTo(orig_pos)
                    time.sleep(0.5)

                time.sleep(delay_val)
            except Exception as e:
                err_trace = traceback.format_exc()
                self.after(0, lambda t=err_trace: self.report_error(t))
                time.sleep(0.1)

    def report_error(self, trace):
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(trace)
        r.update()
        r.destroy()
        messagebox.showerror("Thread Error", f"Error copied to clipboard:\n\n{trace}")

if __name__ == "__main__":
    app = FAC()
    app.mainloop()