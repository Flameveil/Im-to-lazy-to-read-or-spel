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
    GUI app that:
    1. Lets the user choose a PDF file
    2. Extracts text from the PDF
    3. Converts that text into speech
    4. Plays the speech with pause/resume/stop controls

    Extra features:
    - Multiple voices
    - Light/Dark mode
    - Current file display
    - Elapsed and remaining time
    - Slider to seek through audio
    """

    def __init__(self):
        super().__init__()

        self.title("Read To Me")
        self.geometry("900x650")
        self.minsize(800, 560)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        pygame.mixer.init()

        # -----------------------------
        # App state
        # -----------------------------
        self.current_pdf_path = None
        self.current_audio_path = None
        self.current_text = ""
        self.audio_length = 0.0

        self.is_generating = False
        self.is_playing = False
        self.is_paused = False

        # playback_offset stores the point in the audio where playback should begin
        # This is used for seeking and resuming
        self.playback_offset = 0.0

        # play_started_at stores the wall-clock time when playback most recently started
        # This allows us to estimate the current playback position
        self.play_started_at = None

        self.voice_map = {
            "Aria (US Female)": "en-US-AriaNeural",
            "Guy (US Male)": "en-US-GuyNeural",
            "Jenny (US Female)": "en-US-JennyNeural",
            "Davis (US Male)": "en-US-DavisNeural",
        }

        self.create_widgets()
        self.after(250, self.update_playback_ui)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        """Build all GUI widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # -----------------------------
        # Top bar
        # -----------------------------
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            top_frame,
            text="Read To Me",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=12, pady=12, sticky="w")

        self.appearance_menu = ctk.CTkOptionMenu(
            top_frame,
            values=["Dark", "Light", "System"],
            command=self.change_appearance
        )
        self.appearance_menu.set("Dark")
        self.appearance_menu.grid(row=0, column=1, padx=8, pady=12)

        self.voice_menu = ctk.CTkOptionMenu(
            top_frame,
            values=list(self.voice_map.keys())
        )
        self.voice_menu.set("Aria (US Female)")
        self.voice_menu.grid(row=0, column=2, padx=(0, 12), pady=12)

        # -----------------------------
        # Info area
        # -----------------------------
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=1, column=0, padx=14, pady=8, sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            info_frame,
            text="Current File:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=(12, 6), pady=(12, 6), sticky="w")

        self.file_label = ctk.CTkLabel(info_frame, text="No PDF loaded", anchor="w")
        self.file_label.grid(row=0, column=1, padx=(0, 12), pady=(12, 6), sticky="ew")

        ctk.CTkLabel(
            info_frame,
            text="Status:",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=1, column=0, padx=(12, 6), pady=(0, 12), sticky="w")

        self.status_label = ctk.CTkLabel(info_frame, text="Ready", anchor="w")
        self.status_label.grid(row=1, column=1, padx=(0, 12), pady=(0, 12), sticky="ew")

        # -----------------------------
        # Text preview
        # -----------------------------
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=2, column=0, padx=14, pady=8, sticky="nsew")
        preview_frame.grid_rowconfigure(1, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_frame,
            text="Extracted Text Preview",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        self.textbox = ctk.CTkTextbox(preview_frame, wrap="word")
        self.textbox.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.textbox.insert("1.0", "Load a PDF to preview extracted text...")

        # -----------------------------
        # Controls
        # -----------------------------
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=3, column=0, padx=14, pady=8, sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)

        button_row = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_row.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")

        self.load_button = ctk.CTkButton(button_row, text="Load PDF", command=self.load_pdf)
        self.load_button.pack(side="left", padx=6)

        self.play_button = ctk.CTkButton(button_row, text="Play", command=self.start_reading, state="disabled")
        self.play_button.pack(side="left", padx=6)

        self.pause_button = ctk.CTkButton(button_row, text="Pause", command=self.pause_audio, state="disabled")
        self.pause_button.pack(side="left", padx=6)

        self.resume_button = ctk.CTkButton(button_row, text="Resume", command=self.resume_audio, state="disabled")
        self.resume_button.pack(side="left", padx=6)

        self.stop_button = ctk.CTkButton(button_row, text="Stop", command=self.stop_audio, state="disabled")
        self.stop_button.pack(side="left", padx=6)

        slider_row = ctk.CTkFrame(controls_frame, fg_color="transparent")
        slider_row.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        slider_row.grid_columnconfigure(1, weight=1)

        self.elapsed_label = ctk.CTkLabel(slider_row, text="00:00")
        self.elapsed_label.grid(row=0, column=0, padx=(0, 8), pady=6)

        self.position_slider = ctk.CTkSlider(
            slider_row,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.on_slider_move
        )
        self.position_slider.grid(row=0, column=1, sticky="ew", pady=6)
        self.position_slider.set(0)

        self.remaining_label = ctk.CTkLabel(slider_row, text="-00:00")
        self.remaining_label.grid(row=0, column=2, padx=(8, 0), pady=6)

        self.tip_label = ctk.CTkLabel(
            controls_frame,
            text="Load a PDF, then press Play. You can pause, resume, stop, or drag the slider.",
            anchor="w"
        )
        self.tip_label.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")

    def change_appearance(self, mode):
        """Switch between Dark, Light, and System appearance."""
        ctk.set_appearance_mode(mode)

    def load_pdf(self):
        """Ask the user to choose a PDF file, then extract its text."""
        if self.is_generating:
            messagebox.showinfo("Busy", "Please wait until audio generation is finished.")
            return

        file_path = filedialog.askopenfilename(
            title="Choose a PDF file",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not file_path:
            return

        # Stop playback before changing files
        self.stop_audio(clear_status=False)

        try:
            extracted_text = self.extract_text_from_pdf(file_path)

            if not extracted_text.strip():
                messagebox.showwarning(
                    "No Text Found",
                    "This PDF does not appear to contain readable text."
                )
                return

            self.current_pdf_path = file_path
            self.current_text = extracted_text
            self.current_audio_path = None
            self.audio_length = 0.0
            self.playback_offset = 0.0
            self.play_started_at = None
            self.is_playing = False
            self.is_paused = False

            self.file_label.configure(text=os.path.basename(file_path))
            self.status_label.configure(text="PDF loaded. Ready to play.")
            self.play_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")

            self.textbox.delete("1.0", "end")
            preview = extracted_text[:5000]
            if len(extracted_text) > 5000:
                preview += "\n\n[Preview truncated...]"
            self.textbox.insert("1.0", preview)

            self.position_slider.set(0)
            self.elapsed_label.configure(text="00:00")
            self.remaining_label.configure(text="-00:00")

        except Exception as exc:
            messagebox.showerror("PDF Error", f"Could not read the PDF.\n\n{exc}")
            self.status_label.configure(text="Failed to load PDF.")

    def extract_text_from_pdf(self, file_path):
        """Extract text from every page in the PDF and combine it into one string."""
        reader = PdfReader(file_path)
        pages_text = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)

        return "\n\n".join(pages_text)

    def start_reading(self):
        """
        Start reading the current PDF.
        If the audio file has not been generated yet, generate it first.
        """
        if not self.current_text:
            messagebox.showwarning("No PDF Loaded", "Please load a PDF first.")
            return

        if self.is_generating:
            messagebox.showinfo("Generating", "Audio is already being generated.")
            return

        # If the MP3 already exists, just play it
        if self.current_audio_path and os.path.exists(self.current_audio_path):
            self.play_audio(start_pos=self.playback_offset)
            return

        self.is_generating = True
        self.status_label.configure(text="Generating speech audio... please wait.")
        self.set_generating_buttons()

        thread = threading.Thread(target=self.generate_audio_thread, daemon=True)
        thread.start()

    def generate_audio_thread(self):
        """Run the async TTS generator in a background thread so the GUI stays responsive."""
        try:
            voice_name = self.voice_map[self.voice_menu.get()]
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "read_to_me_output.mp3")

            asyncio.run(self.generate_tts_file(self.current_text, voice_name, output_path))

            self.current_audio_path = output_path
            self.audio_length = MP3(output_path).info.length
            self.playback_offset = 0.0

            self.after(0, lambda: self.status_label.configure(text="Audio ready. Starting playback..."))
            self.after(0, lambda: self.play_audio(start_pos=0.0))

        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("TTS Error", f"Could not generate speech.\n\n{exc}"))
            self.after(0, lambda: self.status_label.configure(text="Audio generation failed."))
            self.after(0, self.set_idle_buttons)

        finally:
            self.is_generating = False

    async def generate_tts_file(self, text, voice_name, output_path):
        """Use edge-tts to create an MP3 file from the extracted text."""
        communicate = edge_tts.Communicate(text=text, voice=voice_name)
        await communicate.save(output_path)

    def play_audio(self, start_pos=0.0):
        """Load the generated MP3 and start playback from the given position."""
        if not self.current_audio_path or not os.path.exists(self.current_audio_path):
            messagebox.showwarning("Missing Audio", "No audio file is available yet.")
            return

        try:
            pygame.mixer.music.load(self.current_audio_path)
            pygame.mixer.music.play(start=max(0.0, float(start_pos)))

            self.playback_offset = max(0.0, float(start_pos))
            self.play_started_at = time.time()
            self.is_playing = True
            self.is_paused = False

            self.status_label.configure(text="Playing audio...")
            self.play_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="normal")

        except Exception as exc:
            messagebox.showerror("Playback Error", f"Could not play audio.\n\n{exc}")
            self.status_label.configure(text="Playback failed.")
            self.set_idle_buttons()

    def pause_audio(self):
        """Pause the current audio and save the current playback position."""
        if not self.is_playing:
            return

        if self.play_started_at is not None:
            self.playback_offset += time.time() - self.play_started_at

        pygame.mixer.music.pause()

        self.play_started_at = None
        self.is_playing = False
        self.is_paused = True

        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="normal")
        self.status_label.configure(text="Paused.")

    def resume_audio(self):
        """Resume playback from the last saved playback position."""
        if not self.is_paused:
            return

        self.play_audio(start_pos=self.playback_offset)
        self.status_label.configure(text="Resumed playback.")

    def stop_audio(self, clear_status=True):
        """Stop audio playback and reset the playback position."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        self.is_playing = False
        self.is_paused = False
        self.playback_offset = 0.0
        self.play_started_at = None

        self.position_slider.set(0)
        self.elapsed_label.configure(text="00:00")
        self.remaining_label.configure(
            text=self.format_negative_time(self.audio_length) if self.audio_length > 0 else "-00:00"
        )

        if clear_status:
            self.status_label.configure(text="Stopped.")

        self.set_idle_buttons()

    def set_generating_buttons(self):
        """Disable controls while the app is generating speech."""
        self.load_button.configure(state="disabled")
        self.play_button.configure(state="disabled")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

    def set_idle_buttons(self):
        """Restore buttons to the normal ready state."""
        self.load_button.configure(state="normal")
        self.play_button.configure(state="normal" if self.current_text else "disabled")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

    def on_slider_move(self, value):
        """
        Seek to a new part of the audio.
        Slider range is 0-100, so it is converted into seconds.
        """
        if self.audio_length <= 0:
            return

        new_time = (float(value) / 100.0) * self.audio_length
        self.playback_offset = new_time

        self.elapsed_label.configure(text=self.format_time(new_time))
        self.remaining_label.configure(
            text=self.format_negative_time(max(self.audio_length - new_time, 0))
        )

        # If currently playing or paused, restart from the new location
        if self.current_audio_path and os.path.exists(self.current_audio_path) and (self.is_playing or self.is_paused):
            self.play_audio(start_pos=new_time)

    def update_playback_ui(self):
        """Refresh elapsed time, remaining time, and slider position while audio is playing."""
        if self.is_playing and self.play_started_at is not None:
            current_time = self.playback_offset + (time.time() - self.play_started_at)

            if self.audio_length > 0:
                current_time = min(current_time, self.audio_length)
                slider_value = (current_time / self.audio_length) * 100.0
                self.position_slider.set(slider_value)

            self.elapsed_label.configure(text=self.format_time(current_time))
            self.remaining_label.configure(
                text=self.format_negative_time(max(self.audio_length - current_time, 0))
            )

            # If playback has reached the end, reset controls
            if self.audio_length > 0 and current_time >= self.audio_length - 0.2:
                self.is_playing = False
                self.is_paused = False
                self.play_started_at = None
                self.playback_offset = 0.0
                self.position_slider.set(100)
                self.status_label.configure(text="Finished playing.")
                self.set_idle_buttons()

        elif self.is_paused:
            self.elapsed_label.configure(text=self.format_time(self.playback_offset))
            self.remaining_label.configure(
                text=self.format_negative_time(max(self.audio_length - self.playback_offset, 0))
            )

        self.after(250, self.update_playback_ui)

    def format_time(self, seconds):
        """Convert seconds into mm:ss format."""
        seconds = max(0, int(seconds))
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:02d}"

    def format_negative_time(self, seconds):
        """Format time as a countdown-style string."""
        return f"-{self.format_time(seconds)}"

    def on_close(self):
        """Stop playback and close the app safely."""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = ReadToMeApp()
    app.mainloop()