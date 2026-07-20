import time
import threading
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui

# Windows: ekran kapanmasını ve uyku modunu engelle
_ES_CONTINUOUS       = 0x80000000
_ES_SYSTEM_REQUIRED  = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002

def _prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED
    )

def _allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)

class EnterPresserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Auto Sender")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self._running = False
        self._thread = None
        self._remaining = 0

        _prevent_sleep()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _build_ui(self):
        PAD = {"padx": 16, "pady": 10}
        BG = "#1e1e2e"
        FG = "#cdd6f4"
        ENTRY_BG = "#313244"
        ACCENT = "#89b4fa"
        BTN_START = "#a6e3a1"
        BTN_STOP  = "#f38ba8"

        # ── Başlık ──
        tk.Label(self.root, text="Claude Auto Sender", font=("Segoe UI", 18, "bold"),
                 bg=BG, fg=ACCENT).grid(row=0, column=0, columnspan=6, pady=(18, 4))

        # ── Zaman girişi ──
        frame = tk.Frame(self.root, bg=BG)
        frame.grid(row=1, column=0, columnspan=6, **PAD)

        for col, (label, attr, max_val) in enumerate([
            ("Saat", "hour_var", 99),
            ("Dakika", "min_var", 59),
            ("Saniye", "sec_var", 59),
        ]):
            setattr(self, attr, tk.StringVar(value="0"))
            tk.Label(frame, text=label, font=("Segoe UI", 10),
                     bg=BG, fg=FG).grid(row=0, column=col, padx=12)
            sb = tk.Spinbox(
                frame, from_=0, to=max_val, width=5,
                textvariable=getattr(self, attr),
                font=("Segoe UI", 22, "bold"),
                bg=ENTRY_BG, fg=FG, buttonbackground=ENTRY_BG,
                insertbackground=FG, relief="flat", justify="center",
            )
            sb.grid(row=1, column=col, padx=12, ipady=4)

        # ── Geri sayım göstergesi ──
        self.countdown_var = tk.StringVar(value="00:00:00")
        tk.Label(self.root, textvariable=self.countdown_var,
                 font=("Segoe UI", 36, "bold"), bg=BG, fg=ACCENT
                 ).grid(row=2, column=0, columnspan=6, pady=(4, 2))

        # ── Durum metni ──
        self.status_var = tk.StringVar(value="Hazır")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Segoe UI", 10), bg=BG, fg="#a6adc8"
                 ).grid(row=3, column=0, columnspan=6, pady=(0, 8))

        # ── Butonlar ──
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.grid(row=4, column=0, columnspan=6, pady=(4, 18))

        self.start_btn = tk.Button(
            btn_frame, text="▶  Başlat", font=("Segoe UI", 11, "bold"),
            bg=BTN_START, fg="#1e1e2e", activebackground="#94d39a",
            relief="flat", padx=20, pady=6, cursor="hand2",
            command=self.start
        )
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = tk.Button(
            btn_frame, text="■  Durdur", font=("Segoe UI", 11, "bold"),
            bg=BTN_STOP, fg="#1e1e2e", activebackground="#e07a95",
            relief="flat", padx=20, pady=6, cursor="hand2",
            state="disabled", command=self.stop
        )
        self.stop_btn.pack(side="left", padx=10)

    # ── İş mantığı ──
    def _parse_total(self):
        try:
            h = int(self.hour_var.get())
            m = int(self.min_var.get())
            s = int(self.sec_var.get())
        except ValueError:
            return 0
        return h * 3600 + m * 60 + s

    def start(self):
        total = self._parse_total()
        if total <= 0:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir süre girin.")
            return
        self._remaining = total
        self._running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Sayıyor...")
        self._thread = threading.Thread(target=self._countdown, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Durduruldu")
        self.countdown_var.set("00:00:00")

    def _countdown(self):
        while self._remaining > 0 and self._running:
            h = self._remaining // 3600
            m = (self._remaining % 3600) // 60
            s = self._remaining % 60
            self.countdown_var.set(f"{h:02}:{m:02}:{s:02}")
            time.sleep(1)
            self._remaining -= 1

        if self._running:
            self.countdown_var.set("00:00:00")
            self.status_var.set("Enter basıldı!")
            pyautogui.press("enter")
            self.root.after(0, self._reset_buttons)

    def _reset_buttons(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _on_close(self):
        self._running = False
        _allow_sleep()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = EnterPresserApp(root)
    root.mainloop()
