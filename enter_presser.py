import ctypes
import json
import threading
import time
import winsound
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui

# ── Windows: ekran kapanmasını ve uyku modunu engelle ──
_ES_CONTINUOUS       = 0x80000000
_ES_SYSTEM_REQUIRED  = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002


def _prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED
    )


def _allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)


def _get_foreground_title():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "(algılanamadı)"
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value or "(başlıksız pencere)"


CONFIG_PATH = Path.home() / ".claude_auto_sender.json"


class Colors:
    BG = "#1e1e2e"
    CARD = "#232634"
    ENTRY = "#313244"
    FG = "#cdd6f4"
    MUTED = "#a6adc8"
    ACCENT = "#89b4fa"
    ACCENT_2 = "#cba6f7"
    GREEN = "#a6e3a1"
    RED = "#f38ba8"
    YELLOW = "#f9e2af"
    BORDER = "#313244"


class EnterPresserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Auto Sender")
        self.root.resizable(False, False)
        self.root.configure(bg=Colors.BG)

        self._running = False
        self._paused = False
        self._thread = None
        self._total = 0
        self._remaining = 0
        self._sent_count = 0

        self._config = self._load_config()

        _prevent_sleep()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Return>", self._on_return_key)
        self.root.bind("<Escape>", lambda e: self.stop())

        self._build_style()
        self._build_ui()
        self._apply_config(self._config)

        self._poll_foreground_window()

    # ── Görsel stil ──
    def _build_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=Colors.ENTRY, background=Colors.ACCENT,
            bordercolor=Colors.CARD, lightcolor=Colors.ACCENT,
            darkcolor=Colors.ACCENT, thickness=12,
        )
        style.configure(
            "Dark.TCheckbutton",
            background=Colors.CARD, foreground=Colors.FG,
            font=("Segoe UI", 10),
        )
        style.map(
            "Dark.TCheckbutton",
            background=[("active", Colors.CARD)],
            foreground=[("active", Colors.ACCENT)],
        )

    def _card(self, parent, title=None):
        outer = tk.Frame(parent, bg=Colors.CARD, highlightbackground=Colors.BORDER,
                          highlightthickness=1)
        if title:
            tk.Label(outer, text=title, font=("Segoe UI", 10, "bold"),
                      bg=Colors.CARD, fg=Colors.ACCENT_2, anchor="w"
                      ).pack(fill="x", padx=14, pady=(10, 0))
        return outer

    def _mini_button(self, parent, text, command):
        return tk.Button(
            parent, text=text, font=("Segoe UI", 9), bg=Colors.ENTRY, fg=Colors.FG,
            activebackground=Colors.ACCENT, activeforeground=Colors.BG,
            relief="flat", padx=8, pady=4, cursor="hand2", command=command,
        )

    # ── Arayüz ──
    def _build_ui(self):
        BG = Colors.BG
        FG = Colors.FG

        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True, padx=18, pady=16)

        # Başlık
        tk.Label(container, text="Claude Auto Sender", font=("Segoe UI", 18, "bold"),
                  bg=BG, fg=Colors.ACCENT).pack(pady=(0, 2))
        tk.Label(container, text="Süre dolunca otomatik Enter gönderir",
                  font=("Segoe UI", 9), bg=BG, fg=Colors.MUTED).pack(pady=(0, 12))

        # ── Süre kartı ──
        time_card = self._card(container, "⏱  Süre")
        time_card.pack(fill="x", pady=(0, 10))

        spin_frame = tk.Frame(time_card, bg=Colors.CARD)
        spin_frame.pack(pady=(6, 4))
        for col, (label, attr, max_val) in enumerate([
            ("Saat", "hour_var", 99),
            ("Dakika", "min_var", 59),
            ("Saniye", "sec_var", 59),
        ]):
            setattr(self, attr, tk.StringVar(value="0"))
            tk.Label(spin_frame, text=label, font=("Segoe UI", 9),
                      bg=Colors.CARD, fg=Colors.MUTED).grid(row=0, column=col, padx=12)
            sb = tk.Spinbox(
                spin_frame, from_=0, to=max_val, width=4,
                textvariable=getattr(self, attr),
                font=("Segoe UI", 20, "bold"),
                bg=Colors.ENTRY, fg=FG, buttonbackground=Colors.ENTRY,
                insertbackground=FG, relief="flat", justify="center",
            )
            sb.grid(row=1, column=col, padx=12, ipady=4)
            setattr(self, attr.replace("_var", "_box"), sb)

        preset_frame = tk.Frame(time_card, bg=Colors.CARD)
        preset_frame.pack(pady=(6, 12))
        presets = [
            ("+30sn", 30), ("+1dk", 60), ("+5dk", 300),
            ("+10dk", 600), ("+30dk", 1800), ("+1sa", 3600),
        ]
        for text, seconds in presets:
            self._mini_button(preset_frame, text, lambda s=seconds: self._add_seconds(s)
                               ).pack(side="left", padx=3)
        self._mini_button(preset_frame, "Temizle", lambda: self._add_seconds(None)
                           ).pack(side="left", padx=(10, 3))

        # ── Seçenekler kartı ──
        opt_card = self._card(container, "⚙  Seçenekler")
        opt_card.pack(fill="x", pady=(0, 10))
        opt_row = tk.Frame(opt_card, bg=Colors.CARD)
        opt_row.pack(fill="x", padx=14, pady=(6, 4))

        self.repeat_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_row, text="Tekrarla", variable=self.repeat_var,
                         style="Dark.TCheckbutton").pack(side="left")
        tk.Label(opt_row, text="  Kaç kez (0=sınırsız):", font=("Segoe UI", 9),
                  bg=Colors.CARD, fg=Colors.MUTED).pack(side="left")
        self.repeat_count_var = tk.StringVar(value="0")
        tk.Spinbox(opt_row, from_=0, to=999, width=4, textvariable=self.repeat_count_var,
                    font=("Segoe UI", 10), bg=Colors.ENTRY, fg=FG,
                    buttonbackground=Colors.ENTRY, insertbackground=FG,
                    relief="flat", justify="center").pack(side="left", padx=6)

        opt_row2 = tk.Frame(opt_card, bg=Colors.CARD)
        opt_row2.pack(fill="x", padx=14, pady=(2, 12))
        self.topmost_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_row2, text="Pencereyi her zaman üstte tut",
                         variable=self.topmost_var, style="Dark.TCheckbutton",
                         command=self._apply_topmost).pack(side="left")

        # ── Hedef pencere kartı ──
        target_card = self._card(container, "🎯  Hedef pencere (Enter buraya gönderilecek)")
        target_card.pack(fill="x", pady=(0, 10))
        self.target_var = tk.StringVar(value="…")
        tk.Label(target_card, textvariable=self.target_var, font=("Segoe UI", 10, "bold"),
                  bg=Colors.CARD, fg=Colors.GREEN, anchor="w", wraplength=380
                  ).pack(fill="x", padx=14, pady=(4, 2))
        tk.Label(target_card, text="Geri sayım bitmeden bu pencerenin aktif olduğundan emin olun.",
                  font=("Segoe UI", 8), bg=Colors.CARD, fg=Colors.MUTED, anchor="w"
                  ).pack(fill="x", padx=14, pady=(0, 10))

        # ── Geri sayım ──
        self.countdown_var = tk.StringVar(value="00:00:00")
        self.countdown_lbl = tk.Label(container, textvariable=self.countdown_var,
                 font=("Segoe UI", 34, "bold"), bg=BG, fg=Colors.ACCENT)
        self.countdown_lbl.pack(pady=(4, 2))

        self.progress = ttk.Progressbar(container, style="Accent.Horizontal.TProgressbar",
                                         maximum=100, value=0)
        self.progress.pack(fill="x", pady=(0, 6))

        status_row = tk.Frame(container, bg=BG)
        status_row.pack(fill="x", pady=(0, 10))
        self.status_var = tk.StringVar(value="Hazır")
        tk.Label(status_row, textvariable=self.status_var, font=("Segoe UI", 10),
                  bg=BG, fg=Colors.MUTED).pack(side="left")
        self.sent_var = tk.StringVar(value="Gönderim: 0")
        tk.Label(status_row, textvariable=self.sent_var, font=("Segoe UI", 9),
                  bg=BG, fg=Colors.MUTED).pack(side="right")

        # ── Butonlar ──
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(2, 6))

        self.start_btn = tk.Button(
            btn_frame, text="▶  Başlat", font=("Segoe UI", 11, "bold"),
            bg=Colors.GREEN, fg="#1e1e2e", activebackground="#94d39a",
            relief="flat", padx=16, pady=6, cursor="hand2", command=self.start,
        )
        self.start_btn.pack(side="left", padx=6)

        self.pause_btn = tk.Button(
            btn_frame, text="⏸  Duraklat", font=("Segoe UI", 11, "bold"),
            bg=Colors.ACCENT, fg="#1e1e2e", activebackground="#a5c6fb",
            relief="flat", padx=16, pady=6, cursor="hand2",
            state="disabled", command=self.toggle_pause,
        )
        self.pause_btn.pack(side="left", padx=6)

        self.stop_btn = tk.Button(
            btn_frame, text="■  Durdur", font=("Segoe UI", 11, "bold"),
            bg=Colors.RED, fg="#1e1e2e", activebackground="#e07a95",
            relief="flat", padx=16, pady=6, cursor="hand2",
            state="disabled", command=self.stop,
        )
        self.stop_btn.pack(side="left", padx=6)

        self.reset_btn = tk.Button(
            btn_frame, text="↺  Sıfırla", font=("Segoe UI", 11, "bold"),
            bg=Colors.ENTRY, fg=FG, activebackground=Colors.BORDER,
            relief="flat", padx=16, pady=6, cursor="hand2", command=self.reset,
        )
        self.reset_btn.pack(side="left", padx=6)

        tk.Label(container, text="İpucu: Enter tuşu ile başlat, Esc ile durdur. Ayarlar otomatik kaydedilir.",
                  font=("Segoe UI", 8), bg=BG, fg=Colors.MUTED).pack(pady=(4, 0))

    # ── Yardımcılar ──
    def _time_fields(self):
        return [self.hour_box, self.min_box, self.sec_box]

    def _set_inputs_state(self, state):
        for box in self._time_fields():
            box.config(state=state)
        self.reset_btn.config(state=state)

    def _parse_total(self):
        try:
            h = int(self.hour_var.get())
            m = int(self.min_var.get())
            s = int(self.sec_var.get())
        except ValueError:
            return 0
        return max(0, h * 3600 + m * 60 + s)

    def _parse_repeat_limit(self):
        try:
            return max(0, int(self.repeat_count_var.get()))
        except ValueError:
            return 0

    def _add_seconds(self, delta):
        if self._running:
            return
        total = 0 if delta is None else self._parse_total() + delta
        total = max(0, total)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        self.hour_var.set(str(h))
        self.min_var.set(str(m))
        self.sec_var.set(str(s))

    def _apply_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    def _on_return_key(self, event):
        if not self._running:
            self.start()

    # ── Hedef pencere ──
    def _poll_foreground_window(self):
        try:
            title = _get_foreground_title()
        except Exception:
            title = "(algılanamadı)"
        self.target_var.set(title)
        self.root.after(500, self._poll_foreground_window)

    # ── İş mantığı ──
    def start(self):
        total = self._parse_total()
        if total <= 0:
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir süre girin.")
            return
        self._total = total
        self._remaining = total
        self._running = True
        self._paused = False
        self._sent_count = 0
        self.sent_var.set("Gönderim: 0")
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="⏸  Duraklat")
        self.stop_btn.config(state="normal")
        self._set_inputs_state("disabled")
        self.status_var.set("Sayıyor...")
        self._save_config()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def toggle_pause(self):
        if not self._running:
            return
        self._paused = not self._paused
        if self._paused:
            self.pause_btn.config(text="▶  Devam Et")
            self.status_var.set("Duraklatıldı")
        else:
            self.pause_btn.config(text="⏸  Duraklat")
            self.status_var.set("Sayıyor...")

    def stop(self):
        if not self._running:
            return
        self._running = False
        self._paused = False
        self.status_var.set("Durduruldu")
        self.countdown_var.set("00:00:00")
        self.progress.config(value=0)
        self._reset_buttons()

    def reset(self):
        if self._running:
            return
        self.hour_var.set("0")
        self.min_var.set("0")
        self.sec_var.set("0")
        self.countdown_var.set("00:00:00")
        self.progress.config(value=0)
        self.status_var.set("Hazır")
        self.sent_var.set("Gönderim: 0")
        self._sent_count = 0

    def _worker(self):
        limit = self._parse_repeat_limit()
        repeat = self.repeat_var.get()

        while self._running:
            self._remaining = self._total
            tick_accum = 0.0
            last = time.time()

            while self._running and self._remaining > 0:
                time.sleep(0.1)
                now = time.time()
                dt, last = now - last, now
                if self._paused:
                    continue
                tick_accum += dt
                while tick_accum >= 1 and self._remaining > 0:
                    self._remaining -= 1
                    tick_accum -= 1
                    self.root.after(0, self._update_countdown_ui)

            if not self._running:
                return

            self._sent_count += 1
            pyautogui.press("enter")
            try:
                winsound.Beep(880, 150)
            except Exception:
                pass
            self.root.after(0, self._on_cycle_sent)

            if not repeat or (limit and self._sent_count >= limit):
                self._running = False
                self.root.after(0, self._reset_buttons)
                return

            self.root.after(0, lambda: self.status_var.set("Sonraki gönderim hazırlanıyor..."))
            time.sleep(1)

    def _update_countdown_ui(self):
        h = self._remaining // 3600
        m = (self._remaining % 3600) // 60
        s = self._remaining % 60
        self.countdown_var.set(f"{h:02}:{m:02}:{s:02}")
        if self._total > 0:
            done = (self._total - self._remaining) / self._total * 100
            self.progress.config(value=done)
        self.countdown_lbl.config(
            fg=Colors.YELLOW if 0 < self._remaining <= 10 else Colors.ACCENT
        )

    def _on_cycle_sent(self):
        self.countdown_var.set("00:00:00")
        self.progress.config(value=100)
        self.status_var.set("Enter gönderildi!")
        self.sent_var.set(f"Gönderim: {self._sent_count}")

    def _reset_buttons(self):
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="⏸  Duraklat")
        self.stop_btn.config(state="disabled")
        self._set_inputs_state("normal")
        if self.status_var.get() not in ("Durduruldu",):
            self.status_var.set("Tamamlandı")

    # ── Ayarları kaydet/yükle ──
    def _load_config(self):
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _apply_config(self, cfg):
        self.hour_var.set(str(cfg.get("hour", 0)))
        self.min_var.set(str(cfg.get("min", 0)))
        self.sec_var.set(str(cfg.get("sec", 0)))
        self.repeat_var.set(bool(cfg.get("repeat", False)))
        self.repeat_count_var.set(str(cfg.get("repeat_count", 0)))
        self.topmost_var.set(bool(cfg.get("topmost", False)))
        self._apply_topmost()

    def _save_config(self):
        cfg = {
            "hour": self.hour_var.get(),
            "min": self.min_var.get(),
            "sec": self.sec_var.get(),
            "repeat": self.repeat_var.get(),
            "repeat_count": self.repeat_count_var.get(),
            "topmost": self.topmost_var.get(),
        }
        try:
            CONFIG_PATH.write_text(json.dumps(cfg), encoding="utf-8")
        except OSError:
            pass

    def _on_close(self):
        self._running = False
        self._save_config()
        _allow_sleep()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = EnterPresserApp(root)
    root.mainloop()
