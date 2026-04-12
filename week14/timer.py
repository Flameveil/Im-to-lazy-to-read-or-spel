import tkinter as tk
from tkinter import messagebox
import numpy as np
import sounddevice as sd
import threading
import time

class UniversalTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Cross-Platform Precision Timer")
        self.root.geometry("350x300")
        self.root.configure(bg="#1a1a1a")

        self.running = False
        self.time_left = 0
        self.sample_rate = 44100

        self.create_widgets()

    def play_beep(self, duration=0.4, freq=1000):
        """Synthesizes a beep using math (Numpy) and plays it (Sounddevice)."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # Create a sine wave and apply a small fade-out to prevent 'clicking'
        fade_out = np.linspace(1, 0, len(t)) ** 2
        wave = (np.sin(2 * np.pi * freq * t) * 0.3 * fade_out).astype(np.float32)
        
        sd.play(wave, self.sample_rate)
        sd.wait()

    def countdown(self):
        """The background logic for the timer."""
        while self.time_left > 0 and self.running:
            mins, secs = divmod(self.time_left, 60)
            self.label_display.config(text=f"{mins:02d}:{secs:02d}")
            time.sleep(1)
            self.time_left -= 1
        
        if self.running:
            self.label_display.config(text="00:00", fg="#e74c3c")
            self.running = False
            self.btn_start.config(state="normal", text="START TIMER", bg="#27ae60")
            
            # Trigger 3 synthetic beeps
            for _ in range(3):
                self.play_beep()
                time.sleep(0.1)
                
            messagebox.showinfo("Alarm", "Time is up!")

    def start_timer_thread(self):
        """Validates input and starts the background thread."""
        if not self.running:
            try:
                seconds = int(self.entry.get())
                if seconds <= 0: raise ValueError
                
                self.time_left = seconds
                self.running = True
                self.label_display.config(fg="#ecf0f1")
                self.btn_start.config(state="disabled", text="RUNNING...", bg="#7f8c8d")
                
                thread = threading.Thread(target=self.countdown, daemon=True)
                thread.start()
            except ValueError:
                messagebox.showerror("Error", "Please enter a positive whole number.")

    def create_widgets(self):
        # UI Elements
        tk.Label(self.root, text="TIMER SECONDS", bg="#1a1a1a", fg="#95a5a6", font=("Arial", 10, "bold")).pack(pady=15)
        
        self.entry = tk.Entry(self.root, font=("Courier", 24), width=8, justify='center', bg="#2c3e50", fg="white", insertbackground="white")
        self.entry.insert(0, "10")
        self.entry.pack(pady=5)

        self.label_display = tk.Label(self.root, text="00:00", font=("Courier", 40, "bold"), bg="#1a1a1a", fg="#ecf0f1")
        self.label_display.pack(pady=20)

        self.btn_start = tk.Button(self.root, text="START TIMER", bg="#27ae60", fg="white", 
                                  font=("Arial", 12, "bold"), relief="flat", command=self.start_timer_thread)
        self.btn_start.pack(fill="x", padx=40, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalTimer(root)
    root.mainloop()