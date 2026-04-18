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
    def __init__(self):
        super().__init__()

        # Set up the main window
        # These values make the app feel roomy and easier to use.
        self.title("Read To Me")
        self.geometry("1100x760")
        self.minsize(950, 650)

        # Set the app appearance
        # CustomTkinter keeps a global appearance mode, so changing it here
        # affects the whole interface.
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Start the audio system
        # Pygame's mixer is a shared audio engine. It should be initialized once
        # when the app starts, not over and over during playback.
        pygame.mixer.init()

        # Store the current PDF file path
        self.current_pdf_path = None

        # Store the full text taken from the PDF
        self.current_text = ""

        # Store the path to the current MP3 audio file
        self.current_audio_path = None

        # Store the length of the MP3 in seconds
        # This is used for slider position, elapsed time, and remaining time.
        self.audio_length = 0.0

        # Remember which voice was used to make the current audio
        # This lets us reuse matching audio instead of regenerating it.
        self.current_voice_id = None

        # Track the current playback and generation state
        # These flags help the UI know which buttons should be enabled.
        self.is_generating = False
        self.is_playing = False
        self.is_paused = False

        # Store the place where playback should begin or resume
        # We track our own playback position because pygame's MP3 timing can be
        # unreliable when seeking or restarting playback.
        self.playback_offset = 0.0

        # Store the time playback started
        # We combine this with playback_offset to estimate the current position.
        self.play_started_at = None

        # Available voices
        # The menu shows friendly labels, but Edge TTS needs the voice IDs.
        self.voice_map = {
            "Aria (US Female)": "en-US-AriaNeural",
            "Guy (US Male)": "en-US-GuyNeural",
            "Jenny (US Female)": "en-US-JennyNeural",
            "Andrew (US Male)": "en-US-AndrewNeural",
        }

        # Give each audio generation task a number
        # This is important for race-condition protection.
        # If the user changes voices quickly, older background jobs might finish
        # later than newer ones. Job IDs let us ignore stale results safely.
        self.generation_job_counter = 0
        self.active_generation_job_id = None

        # Save the newest voice request if the user changes voices during generation
        # We only keep the latest request because older pending voice changes are
        # no longer useful once the user picks a newer voice.
        self.pending_voice_label = None
        self.pending_resume_time = 0.0

        # Prevent the slider from reacting when code moves it
        # Without this guard, programmatically updating the slider would trigger
        # the same callback used for manual seeking and cause accidental jumps.
        self.ignore_slider_callback = False

        # Build the window
        self.create_widgets()

        # Start updating playback labels and slider
        # This creates a lightweight UI loop that refreshes playback info.
        self.after(250, self.update_playback_ui)

        # Run cleanup when the user closes the app
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Let the layout resize nicely
        # The left side stays a control panel, while the right side expands.
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top title section
        self.header_frame = ctk.CTkFrame(self, corner_radius=18)
        self.header_frame.grid(row=0, column=0, columnspan=2, padx=18, pady=(18, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Read To Me 📖",
            font=ctk.CTkFont(size=30, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=(20, 10), pady=(16, 4), sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Choose a PDF, pick a voice, and let the app read it out loud.",
            font=ctk.CTkFont(size=15)
        )
        self.subtitle_label.grid(row=1, column=0, padx=(20, 10), pady=(0, 16), sticky="w")

        self.appearance_menu = ctk.CTkOptionMenu(
            self.header_frame,
            values=["Dark", "Light", "System"],
            command=self.change_appearance,
            width=140
        )
        self.appearance_menu.set("Dark")
        self.appearance_menu.grid(row=0, column=1, rowspan=2, padx=18, pady=16, sticky="e")

        # Left control panel
        # We use grid_propagate(False) so the panel keeps a stable width.
        self.sidebar = ctk.CTkFrame(self, corner_radius=18, width=300)
        self.sidebar.grid(row=1, column=0, padx=(18, 10), pady=(0, 18), sticky="nsw")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # File section
        self.file_section = ctk.CTkFrame(self.sidebar, corner_radius=16)
        self.file_section.grid(row=0, column=0, padx=14, pady=(14, 10), sticky="ew")
        self.file_section.grid_columnconfigure(0, weight=1)

        self.file_section_title = ctk.CTkLabel(
            self.file_section,
            text="📂 File",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.file_section_title.grid(row=0, column=0, padx=14, pady=(12, 8), sticky="w")

        self.file_label = ctk.CTkLabel(
            self.file_section,
            text="No PDF loaded",
            wraplength=240,
            justify="left"
        )
        self.file_label.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="w")

        self.load_button = ctk.CTkButton(
            self.file_section,
            text="Load PDF 📂",
            command=self.load_pdf,
            height=40,
            corner_radius=12
        )
        self.load_button.grid(row=2, column=0, padx=14, pady=(4, 14), sticky="ew")

        # Voice section
        self.voice_section = ctk.CTkFrame(self.sidebar, corner_radius=16)
        self.voice_section.grid(row=1, column=0, padx=14, pady=10, sticky="ew")
        self.voice_section.grid_columnconfigure(0, weight=1)

        self.voice_section_title = ctk.CTkLabel(
            self.voice_section,
            text="🎤 Voice",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.voice_section_title.grid(row=0, column=0, padx=14, pady=(12, 8), sticky="w")

        self.voice_help_label = ctk.CTkLabel(
            self.voice_section,
            text="Change the voice at any time while listening.",
            wraplength=240,
            justify="left"
        )
        self.voice_help_label.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="w")

        self.voice_menu = ctk.CTkOptionMenu(
            self.voice_section,
            values=list(self.voice_map.keys()),
            command=self.on_voice_change,
            height=38,
            corner_radius=10
        )
        self.voice_menu.set("Aria (US Female)")
        self.voice_menu.grid(row=2, column=0, padx=14, pady=(4, 14), sticky="ew")

        # Status section
        self.status_section = ctk.CTkFrame(self.sidebar, corner_radius=16)
        self.status_section.grid(row=2, column=0, padx=14, pady=10, sticky="ew")
        self.status_section.grid_columnconfigure(0, weight=1)

        self.status_section_title = ctk.CTkLabel(
            self.status_section,
            text="💡 Status",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.status_section_title.grid(row=0, column=0, padx=14, pady=(12, 8), sticky="w")

        self.status_label = ctk.CTkLabel(
            self.status_section,
            text="Ready",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.status_label.grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")

        self.helper_label = ctk.CTkLabel(
            self.status_section,
            text="Tip: Load a PDF and press Play to begin.",
            wraplength=240,
            justify="left"
        )
        self.helper_label.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="w")

        # Right main content area
        self.main_area = ctk.CTkFrame(self, corner_radius=18)
        self.main_area.grid(row=1, column=1, padx=(10, 18), pady=(0, 18), sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, weight=1)

        # Playback controls section
        self.controls_section = ctk.CTkFrame(self.main_area, corner_radius=16)
        self.controls_section.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")
        self.controls_section.grid_columnconfigure(0, weight=1)

        self.controls_title = ctk.CTkLabel(
            self.controls_section,
            text="🎵 Playback Controls",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.controls_title.grid(row=0, column=0, padx=16, pady=(12, 10), sticky="w")

        self.button_row = ctk.CTkFrame(self.controls_section, fg_color="transparent")
        self.button_row.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        self.button_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.play_button = ctk.CTkButton(
            self.button_row,
            text="▶ Play",
            command=self.start_reading,
            state="disabled",
            height=42,
            corner_radius=12
        )
        self.play_button.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        self.pause_button = ctk.CTkButton(
            self.button_row,
            text="⏸ Pause",
            command=self.pause_audio,
            state="disabled",
            height=42,
            corner_radius=12
        )
        self.pause_button.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        self.resume_button = ctk.CTkButton(
            self.button_row,
            text="⏯ Resume",
            command=self.resume_audio,
            state="disabled",
            height=42,
            corner_radius=12
        )
        self.resume_button.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        self.stop_button = ctk.CTkButton(
            self.button_row,
            text="⏹ Stop",
            command=self.stop_audio,
            state="disabled",
            height=42,
            corner_radius=12
        )
        self.stop_button.grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        # Slider section
        self.slider_section = ctk.CTkFrame(self.controls_section, corner_radius=12)
        self.slider_section.grid(row=2, column=0, padx=12, pady=(0, 14), sticky="ew")
        self.slider_section.grid_columnconfigure(1, weight=1)

        self.elapsed_label = ctk.CTkLabel(
            self.slider_section,
            text="00:00",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.elapsed_label.grid(row=0, column=0, padx=(14, 8), pady=14, sticky="w")

        self.position_slider = ctk.CTkSlider(
            self.slider_section,
            from_=0,
            to=100,
            command=self.on_slider_move
        )
        self.position_slider.grid(row=0, column=1, padx=8, pady=14, sticky="ew")

        self.remaining_label = ctk.CTkLabel(
            self.slider_section,
            text="-00:00",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.remaining_label.grid(row=0, column=2, padx=(8, 14), pady=14, sticky="e")

        # Text preview section
        self.preview_section = ctk.CTkFrame(self.main_area, corner_radius=16)
        self.preview_section.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.preview_section.grid_columnconfigure(0, weight=1)
        self.preview_section.grid_rowconfigure(2, weight=1)

        self.preview_title = ctk.CTkLabel(
            self.preview_section,
            text="📄 Text Preview",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.preview_title.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        self.preview_help = ctk.CTkLabel(
            self.preview_section,
            text="This area shows the beginning of the PDF text that will be read aloud.",
            font=ctk.CTkFont(size=14)
        )
        self.preview_help.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        self.textbox = ctk.CTkTextbox(
            self.preview_section,
            corner_radius=12,
            font=ctk.CTkFont(size=15)
        )
        self.textbox.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="nsew")

    def change_appearance(self, mode):
        # Change the look of the app
        # CustomTkinter applies this globally, so the whole UI updates together.
        ctk.set_appearance_mode(mode)

    def load_pdf(self):
        # Ask the user to choose a PDF
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF Files", "*.pdf")]
        )

        # If the user picked a file, stop old audio and load the new PDF
        if file_path:
            self.stop_audio()
            self.load_file(file_path)

    def load_file(self, path):
        # Read the PDF and collect text from all pages
        try:
            reader = PdfReader(path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()

            # Warn the user if no readable text was found
            # Some PDFs are image-only, scanned, or otherwise do not contain
            # extractable text for pypdf.
            if not text:
                messagebox.showwarning(
                    "No Text Found",
                    "This PDF does not appear to contain extractable text."
                )
                return

            # Save the file and text
            self.current_pdf_path = path
            self.current_text = text

            # Remove old audio because it belongs to another file
            self.clear_audio_cache()

            # Update the file and status labels
            self.file_label.configure(text=os.path.basename(path))
            self.status_label.configure(text="PDF loaded")
            self.helper_label.configure(text="Press Play to hear the file out loud.")

            # Show part of the text in the preview box
            # Limiting preview size keeps the textbox responsive for large PDFs.
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", text[:4000])

            # Reset the slider and time labels
            self.safe_set_slider(0)
            self.elapsed_label.configure(text="00:00")
            self.remaining_label.configure(text="-00:00")

            # Enable only the buttons that should be active
            self.play_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("PDF Error", f"Could not read PDF:\n{e}")

    def on_voice_change(self, selected_voice_label):
        # Do nothing if no text is loaded yet
        if not self.current_text:
            return

        # Get the real voice ID from the chosen name
        selected_voice_id = self.voice_map[selected_voice_label]

        # If the current audio already uses this voice, do nothing
        # This avoids unnecessary online generation work.
        if (
            not self.is_generating
            and self.current_audio_path
            and os.path.exists(self.current_audio_path)
            and self.current_voice_id == selected_voice_id
        ):
            return

        # Save the current position so playback can continue near the same spot
        resume_time = self.get_current_position()

        # Stop the current playback before switching voices
        # We freeze the playback position first so it does not keep drifting while
        # a new voice is being generated.
        self.hard_stop_playback_only()

        # If generation is already happening, keep only the newest voice request
        # This is a last-write-wins model, which is usually the most user-friendly.
        if self.is_generating:
            self.pending_voice_label = selected_voice_label
            self.pending_resume_time = resume_time
            self.status_label.configure(text=f"Queued: {selected_voice_label}")
            self.helper_label.configure(text="Please wait while the new voice is prepared.")
            return

        # Start making the new voice audio
        self.begin_generation(selected_voice_label, resume_time)

    def start_reading(self):
        # Do nothing if there is no text or if audio is already being made
        if not self.current_text or self.is_generating:
            return

        # Get the selected voice
        selected_voice_label = self.voice_menu.get()
        selected_voice_id = self.voice_map[selected_voice_label]

        # Reuse existing audio if it already matches the chosen voice
        # This saves time and avoids unnecessary network requests.
        if (
            self.current_audio_path
            and os.path.exists(self.current_audio_path)
            and self.current_voice_id == selected_voice_id
        ):
            self.play_audio(0.0)
            return

        # Otherwise create a new audio file
        self.begin_generation(selected_voice_label, 0.0)

    def begin_generation(self, voice_label, resume_time):
        # Mark that audio generation is happening
        self.is_generating = True

        # Clear any older pending voice request
        self.pending_voice_label = None
        self.pending_resume_time = 0.0

        # Give this job its own number
        self.generation_job_counter += 1
        job_id = self.generation_job_counter
        self.active_generation_job_id = job_id

        # Get the text and voice for this job
        text = self.current_text
        voice_id = self.voice_map[voice_label]

        # Update the user interface while audio is being created
        self.status_label.configure(text=f"Generating: {voice_label}")
        self.helper_label.configure(text="Creating audio... this can take a moment for long PDFs.")
        self.set_buttons_disabled_for_generation()

        # Run generation in the background so the window stays responsive
        # Edge TTS is async and network-backed, so we run it off the main UI thread.
        threading.Thread(
            target=self.generate_audio_thread,
            args=(job_id, text, voice_label, voice_id, resume_time),
            daemon=True
        ).start()

    def generate_audio_thread(self, job_id, text, voice_label, voice_id, resume_time):
        # This runs in a background thread
        try:
            # Create a unique temp file name for this audio
            # Unique filenames prevent one generation job from overwriting another.
            file_name = f"read_to_me_job_{job_id}_{int(time.time() * 1000)}.mp3"
            output_path = os.path.join(tempfile.gettempdir(), file_name)

            # Generate the speech audio
            asyncio.run(self.generate_tts(text, voice_id, output_path))

            # Read the MP3 length
            audio_length = MP3(output_path).info.length if os.path.exists(output_path) else 0.0

            # Send the result back to the main thread
            # UI updates must happen on the Tkinter thread, not the worker thread.
            self.after(
                0,
                lambda: self.finish_generation(
                    job_id,
                    voice_label,
                    voice_id,
                    output_path,
                    audio_length,
                    resume_time
                )
            )

        except Exception as e:
            self.after(0, lambda: self.handle_generation_error(job_id, str(e)))

    async def generate_tts(self, text, voice_id, output_path):
        # Use Edge TTS to create the MP3 file
        communicator = edge_tts.Communicate(text, voice_id)
        await communicator.save(output_path)

    def finish_generation(self, job_id, voice_label, voice_id, output_path, audio_length, resume_time):
        # Ignore this result if a newer job already exists
        # This is the main stale-job protection check.
        if job_id != self.active_generation_job_id:
            self.delete_file_safely(output_path)
            return

        # Mark generation as finished
        self.is_generating = False

        # Delete the older MP3 if needed
        if self.current_audio_path and self.current_audio_path != output_path:
            self.delete_file_safely(self.current_audio_path)

        # Save the new audio information
        self.current_audio_path = output_path
        self.current_voice_id = voice_id
        self.audio_length = audio_length

        # Keep the resume time inside the audio range
        # The small safety gap avoids edge-case failures when trying to resume
        # too close to the very end of the MP3.
        if self.audio_length > 0:
            resume_time = max(0.0, min(resume_time, max(0.0, self.audio_length - 0.25)))
        else:
            resume_time = 0.0

        # If the user asked for another voice during generation, start that one now
        # This prevents old finished work from briefly playing when the user has
        # already moved on to a new voice choice.
        if self.pending_voice_label and self.pending_voice_label != voice_label:
            queued_voice = self.pending_voice_label
            queued_resume = self.pending_resume_time

            self.pending_voice_label = None
            self.pending_resume_time = 0.0

            self.begin_generation(queued_voice, queued_resume)
            return

        # Update the status and play the new audio
        self.status_label.configure(text=f"Ready - {voice_label}")
        self.helper_label.configure(text="Audio is ready. Enjoy listening!")
        self.play_audio(resume_time)

    def handle_generation_error(self, job_id, error_text):
        # Ignore errors from older jobs
        if job_id != self.active_generation_job_id:
            return

        # Mark generation as finished
        self.is_generating = False
        self.status_label.configure(text="Generation error")
        self.helper_label.configure(text="Something went wrong while creating the audio.")

        # Reset buttons to a safe state
        self.play_button.configure(state="normal" if self.current_text else "disabled")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

        # Show the error
        messagebox.showerror("TTS Error", error_text)

    def play_audio(self, start_time):
        # Do nothing if the MP3 file does not exist
        if not self.current_audio_path or not os.path.exists(self.current_audio_path):
            return

        try:
            # Load and play the MP3
            # pygame.mixer.music.play(start=...) supports time offsets, but MP3
            # seeking is not perfectly precise, so our UI uses estimated timing.
            pygame.mixer.music.load(self.current_audio_path)
            pygame.mixer.music.play(start=max(0.0, start_time))

            # Save playback timing
            self.playback_offset = max(0.0, start_time)
            self.play_started_at = time.time()

            # Update playback state
            self.is_playing = True
            self.is_paused = False

            # Update labels
            self.status_label.configure(text=f"Playing - {self.voice_menu.get()}")
            self.helper_label.configure(text="Use Pause, Resume, Stop, or the slider to control playback.")

            # Update buttons
            self.play_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
            self.resume_button.configure(state="disabled")
            self.stop_button.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Playback Error", f"Could not play audio:\n{e}")

    def pause_audio(self):
        # Do nothing if audio is not currently playing
        if not self.is_playing:
            return

        # Pause the music
        pygame.mixer.music.pause()

        # Save the paused location
        # We compute the new offset using wall-clock time since playback began.
        if self.play_started_at is not None:
            self.playback_offset += time.time() - self.play_started_at

        # Update playback state
        self.play_started_at = None
        self.is_playing = False
        self.is_paused = True

        # Update labels
        self.status_label.configure(text="Paused")
        self.helper_label.configure(text="Press Resume to continue from the same place.")

        # Update buttons
        self.play_button.configure(state="disabled")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="normal")
        self.stop_button.configure(state="normal")

    def resume_audio(self):
        # Do nothing if there is no audio or generation is still running
        if not self.current_audio_path or self.is_generating:
            return

        # Resume from the saved place
        self.play_audio(self.playback_offset)

    def stop_audio(self):
        # Stop the audio without deleting the MP3
        self.hard_stop_playback_only()

        # Reset the playback position
        self.playback_offset = 0.0
        self.play_started_at = None

        # Reset the slider and time labels
        self.safe_set_slider(0)
        self.elapsed_label.configure(text="00:00")
        self.remaining_label.configure(
            text=f"-{self.format_time(self.audio_length)}" if self.audio_length > 0 else "-00:00"
        )

        # Update labels
        if self.current_text:
            self.status_label.configure(text="Stopped")
            self.helper_label.configure(text="Press Play to listen again from the beginning.")
            self.play_button.configure(state="normal")
        else:
            self.status_label.configure(text="Ready")
            self.helper_label.configure(text="Load a PDF to get started.")
            self.play_button.configure(state="disabled")

        # Update buttons
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

    def hard_stop_playback_only(self):
        # Stop the music without clearing saved audio info
        # This is used during voice changes so we can preserve cached audio state
        # while still freezing playback immediately.
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        self.is_playing = False
        self.is_paused = False
        self.play_started_at = None

    def on_slider_move(self, value):
        # Ignore slider updates made by the program itself
        if self.ignore_slider_callback:
            return

        # Do nothing if audio is missing, invalid, or still being generated
        if not self.current_audio_path or self.audio_length <= 0 or self.is_generating:
            return

        # Convert the slider value into seconds
        new_time = (float(value) / 100.0) * self.audio_length
        new_time = max(0.0, min(new_time, self.audio_length))

        # Remember if playback was active
        was_active = self.is_playing or self.is_paused

        # Save the new location
        self.playback_offset = new_time
        self.play_started_at = None

        # Update time labels
        self.elapsed_label.configure(text=self.format_time(new_time))
        self.remaining_label.configure(
            text=f"-{self.format_time(max(0.0, self.audio_length - new_time))}"
        )

        # If audio was active, restart playback from the new spot
        # This keeps seeking behavior simple and consistent.
        if was_active:
            self.play_audio(new_time)

    def update_playback_ui(self):
        # Only update the slider if audio exists
        if self.audio_length > 0:
            # If audio is playing, calculate the current position
            if self.is_playing and self.play_started_at is not None:
                elapsed = self.playback_offset + (time.time() - self.play_started_at)

                # Stop if playback reached the end
                if elapsed >= self.audio_length:
                    self.stop_audio()
                    self.status_label.configure(text="Finished")
                    self.helper_label.configure(text="Playback is complete. Press Play to listen again.")
                else:
                    # Update slider and time labels
                    slider_percent = (elapsed / self.audio_length) * 100
                    self.safe_set_slider(slider_percent)
                    self.elapsed_label.configure(text=self.format_time(elapsed))
                    self.remaining_label.configure(
                        text=f"-{self.format_time(max(0.0, self.audio_length - elapsed))}"
                    )

            # If not playing, keep showing the saved position
            elif not self.is_playing:
                elapsed = self.playback_offset
                slider_percent = (elapsed / self.audio_length) * 100 if self.audio_length > 0 else 0
                self.safe_set_slider(slider_percent)
                self.elapsed_label.configure(text=self.format_time(elapsed))
                self.remaining_label.configure(
                    text=f"-{self.format_time(max(0.0, self.audio_length - elapsed))}"
                )

        # Run this again soon
        # after() is Tkinter's safe scheduling tool for periodic UI updates.
        self.after(250, self.update_playback_ui)

    def get_current_position(self):
        # Return the best current playback position
        # This helper centralizes playback timing logic so multiple methods can
        # ask for the current time without duplicating calculations.
        if self.is_playing and self.play_started_at is not None:
            return self.playback_offset + (time.time() - self.play_started_at)
        return self.playback_offset

    def format_time(self, seconds):
        # Convert seconds into MM:SS format
        seconds = max(0, int(seconds))
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02}:{secs:02}"

    def safe_set_slider(self, value):
        # Move the slider without triggering its callback
        # This prevents accidental seek loops while the UI updates playback.
        self.ignore_slider_callback = True
        try:
            self.position_slider.set(value)
        finally:
            self.ignore_slider_callback = False

    def set_buttons_disabled_for_generation(self):
        # Disable playback buttons while a new MP3 is being made
        # This prevents the user from interacting with controls that depend on
        # an audio file that does not exist yet.
        self.play_button.configure(state="disabled")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

    def clear_audio_cache(self):
        # Delete the current temp MP3 file
        self.delete_file_safely(self.current_audio_path)

        # Reset saved audio info
        self.current_audio_path = None
        self.current_voice_id = None
        self.audio_length = 0.0

        # Reset playback state
        self.is_generating = False
        self.is_playing = False
        self.is_paused = False

        self.playback_offset = 0.0
        self.play_started_at = None

        # Reset job tracking
        self.active_generation_job_id = None
        self.pending_voice_label = None
        self.pending_resume_time = 0.0

    def delete_file_safely(self, path):
        # Try to delete a file without crashing
        # Temp file cleanup should never break the app if the OS still has a
        # handle open or the file was already removed.
        if not path:
            return
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def on_close(self):
        # Stop music if possible
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        # Shut down the mixer
        try:
            pygame.mixer.quit()
        except Exception:
            pass

        # Delete the temp audio file
        self.delete_file_safely(self.current_audio_path)

        # Close the window
        self.destroy()


if __name__ == "__main__":
    app = ReadToMeApp()
    app.mainloop()