import os
import time
import threading
import asyncio
import tempfile

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pypdf import PdfReader
import edge_tts
import pygame
from mutagen.mp3 import MP3


class ReadToMeApp(ctk.CTk):
    """
    Main application class.

    Responsibility:
    - PDF ingestion (file selection + drag/drop if extended)
    - Text extraction
    - Text-to-speech generation (Edge TTS)
    - Audio playback control (pygame)
    - UI state management (play/pause/seek)
    """

    def __init__(self):
        super().__init__()

        # -----------------------------
        # Window configuration
        # -----------------------------
        self.title("Read To Me")
        self.geometry("900x650")
        self.minsize(800, 560)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Audio engine initialization (global mixer state)
        pygame.mixer.init()

        # -----------------------------
        # Application state
        # -----------------------------
        # PDF/text state
        self.current_pdf_path = None
        self.current_text = ""

        # Generated audio output file path
        self.current_audio_path = None

        # Audio metadata
        self.audio_length = 0.0

        # Generation state (prevents duplicate TTS jobs)
        self.is_generating = False

        # Playback state machine
        self.is_playing = False
        self.is_paused = False

        # SEEKING MODEL:
        # playback_offset = where playback should start/resume in seconds
        self.playback_offset = 0.0

        # Timestamp used to compute live playback position
        self.play_started_at = None

        # Voice selection mapping (UI label -> Edge TTS voice id)
        self.voice_map = {
            "Aria (US Female)": "en-US-AriaNeural",
            "Guy (US Male)": "en-US-GuyNeural",
            "Jenny (US Female)": "en-US-JennyNeural",
            "Davis (US Male)": "en-US-DavisNeural",
        }

        # Build UI and start update loop
        self.create_widgets()
        self.after(250, self.update_playback_ui)

        # Graceful shutdown hook
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================
    def create_widgets(self):
        """
        Builds the full interface:
        - Top bar (title, settings, voice selection)
        - File info panel
        - Text preview area
        - Playback controls
        - Seek slider + time display
        """

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---------------- Top bar ----------------
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")

        ctk.CTkLabel(
            top_frame,
            text="Read To Me",
            font=ctk.CTkFont(size=28, weight="bold")
        ).grid(row=0, column=0, padx=12, pady=12, sticky="w")

        # Appearance mode switch (dark/light/system)
        self.appearance_menu = ctk.CTkOptionMenu(
            top_frame,
            values=["Dark", "Light", "System"],
            command=self.change_appearance
        )
        self.appearance_menu.set("Dark")
        self.appearance_menu.grid(row=0, column=1, padx=8)

        # Voice selector
        self.voice_menu = ctk.CTkOptionMenu(
            top_frame,
            values=list(self.voice_map.keys())
        )
        self.voice_menu.set("Aria (US Female)")
        self.voice_menu.grid(row=0, column=2, padx=(0, 12))

        # ---------------- File info panel ----------------
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=1, column=0, padx=14, pady=8, sticky="ew")

        ctk.CTkLabel(info_frame, text="Current File:", font=ctk.CTkFont(weight="bold"))\
            .grid(row=0, column=0, padx=12)

        self.file_label = ctk.CTkLabel(info_frame, text="No PDF loaded")
        self.file_label.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(info_frame, text="Status:", font=ctk.CTkFont(weight="bold"))\
            .grid(row=1, column=0, padx=12)

        self.status_label = ctk.CTkLabel(info_frame, text="Ready")
        self.status_label.grid(row=1, column=1, sticky="w")

        # ---------------- Text preview ----------------
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=2, column=0, sticky="nsew", padx=14, pady=8)

        self.textbox = ctk.CTkTextbox(preview_frame)
        self.textbox.pack(expand=True, fill="both")

        # ---------------- Controls ----------------
        controls = ctk.CTkFrame(self)
        controls.grid(row=3, column=0, sticky="ew", padx=14, pady=8)

        # Load PDF button
        self.load_button = ctk.CTkButton(controls, text="Load PDF", command=self.load_pdf)
        self.load_button.pack(side="left", padx=5)

        # Playback controls
        self.play_button = ctk.CTkButton(controls, text="Play", command=self.start_reading, state="disabled")
        self.play_button.pack(side="left")

        self.pause_button = ctk.CTkButton(controls, text="Pause", command=self.pause_audio, state="disabled")
        self.pause_button.pack(side="left")

        self.resume_button = ctk.CTkButton(controls, text="Resume", command=self.resume_audio, state="disabled")
        self.resume_button.pack(side="left")

        self.stop_button = ctk.CTkButton(controls, text="Stop", command=self.stop_audio, state="disabled")
        self.stop_button.pack(side="left")

        # ---------------- Seek + time display ----------------
        slider_frame = ctk.CTkFrame(controls)
        slider_frame.pack(fill="x", pady=5)

        self.elapsed_label = ctk.CTkLabel(slider_frame, text="00:00")
        self.elapsed_label.pack(side="left")

        # Slider maps 0–100% of audio duration
        self.position_slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=100,
            command=self.on_slider_move
        )
        self.position_slider.pack(side="left", fill="x", expand=True)

        self.remaining_label = ctk.CTkLabel(slider_frame, text="-00:00")
        self.remaining_label.pack(side="right")

    # ============================================================
    # APPEARANCE
    # ============================================================
    def change_appearance(self, mode):
        """Switch UI theme (Dark/Light/System)."""
        ctk.set_appearance_mode(mode)

    # ============================================================
    # PDF LOADING + TEXT EXTRACTION
    # ============================================================
    def load_pdf(self):
        """Open file dialog and load selected PDF."""
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.stop_audio()
            self.load_file(file_path)

    def load_file(self, path):
        """
        Extract text from PDF and update UI.
        Also resets playback state.
        """
        reader = PdfReader(path)
        text = "\n".join(p.extract_text() or "" for p in reader.pages)

        self.current_text = text
        self.file_label.configure(text=os.path.basename(path))

        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text[:4000])

        # Enable playback
        self.play_button.configure(state="normal")

    # ============================================================
    # TEXT TO SPEECH GENERATION
    # ============================================================
    def start_reading(self):
        """
        Entry point for TTS generation + playback.
        If audio exists, reuse it; otherwise generate it.
        """
        if not self.current_text:
            return

        if self.current_audio_path and os.path.exists(self.current_audio_path):
            self.play_audio(0)
            return

        self.status_label.configure(text="Generating audio...")
        self.set_buttons_disabled()

        threading.Thread(target=self.generate_audio_thread, daemon=True).start()

    def generate_audio_thread(self):
        """Background thread wrapper for async Edge TTS."""
        try:
            voice = self.voice_map[self.voice_menu.get()]
            tmp = os.path.join(tempfile.gettempdir(), "read_to_me.mp3")

            asyncio.run(self.generate_tts(self.current_text, voice, tmp))

            self.current_audio_path = tmp
            self.audio_length = MP3(tmp).info.length

            self.after(0, lambda: self.play_audio(0))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("TTS Error", str(e)))

    async def generate_tts(self, text, voice, out):
        """Edge TTS async generation."""
        tts = edge_tts.Communicate(text, voice)
        await tts.save(out)

    # ============================================================
    # AUDIO PLAYBACK ENGINE
    # ============================================================
    def play_audio(self, start):
        """Play MP3 from a given offset."""
        pygame.mixer.music.load(self.current_audio_path)
        pygame.mixer.music.play(start=start)

        self.playback_offset = start
        self.play_started_at = time.time()

        self.is_playing = True
        self.is_paused = False

    def pause_audio(self):
        """Pause playback and store position."""
        pygame.mixer.music.pause()

        if self.play_started_at:
            self.playback_offset += time.time() - self.play_started_at

        self.is_playing = False
        self.is_paused = True

    def resume_audio(self):
        """Resume from stored offset."""
        self.play_audio(self.playback_offset)

    def stop_audio(self):
        """Fully reset playback state."""
        pygame.mixer.music.stop()

        self.is_playing = False
        self.is_paused = False
        self.playback_offset = 0

    # ============================================================
    # SEEKING
    # ============================================================
    def on_slider_move(self, value):
        """Jump playback to a new position in audio."""
        if not self.current_audio_path:
            return

        new_time = (float(value) / 100) * self.audio_length
        self.play_audio(new_time)

    # ============================================================
    # UI UPDATE LOOP
    # ============================================================
    def update_playback_ui(self):
        """Continuously updates slider + timestamps."""
        if self.is_playing and self.play_started_at:
            elapsed = self.playback_offset + (time.time() - self.play_started_at)

            self.position_slider.set((elapsed / self.audio_length) * 100)

            self.elapsed_label.configure(text=self.format_time(elapsed))
            self.remaining_label.configure(
                text=self.format_time(self.audio_length - elapsed)
            )

        self.after(250, self.update_playback_ui)

    def format_time(self, seconds):
        """Convert seconds → MM:SS."""
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02}:{s:02}"

    # ============================================================
    # BUTTON STATE HELPERS
    # ============================================================
    def set_buttons_disabled(self):
        self.play_button.configure(state="disabled")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

    # ============================================================
    # CLEAN EXIT
    # ============================================================
    def on_close(self):
        pygame.mixer.quit()
        self.destroy()


if __name__ == "__main__":
    app = ReadToMeApp()
    app.mainloop()