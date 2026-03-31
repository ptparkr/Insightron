"""
Insightron GUI - Refactored with modular components

Features:
- Lazy-loaded services
- New pipeline integration
- Reduced LOC via component extraction
"""

import customtkinter as ctk
import threading
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class InsightronGUI:
    """
    Refactored GUI with lazy-loaded services.
    Reduced from 754 LOC to ~300 LOC.
    """

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Insightron v4.1.0")
        self.root.geometry("1100x900")
        self.root.minsize(520, 600)

        # State
        self.selected_file: Optional[str] = None
        self.is_transcribing = False
        self._pipeline = None

        # Setup
        self._setup_grid()
        self._setup_ui()
        self._init_async()

        logger.info("GUI initialized")

    def _setup_grid(self):
        """Configure grid layout."""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _setup_ui(self):
        """Build UI components."""
        # Colors
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # Main container
        self.main = ctk.CTkFrame(self.root)
        self.main.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Header
        self.header = ctk.CTkLabel(
            self.main,
            text="Insightron v4.1.0",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.header.pack(pady=10)

        # File selection
        self.file_frame = ctk.CTkFrame(self.main)
        self.file_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(self.file_frame, text="Audio File:").pack(side="left", padx=5)

        self.file_entry = ctk.CTkEntry(self.file_frame, width=400)
        self.file_entry.pack(side="left", padx=5)

        ctk.CTkButton(self.file_frame, text="Browse", command=self._browse_file).pack(
            side="left", padx=5
        )

        # Settings
        self.settings_frame = ctk.CTkFrame(self.main)
        self.settings_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(self.settings_frame, text="Model:").pack(side="left", padx=5)
        self.model_var = ctk.StringVar(value="medium")
        self.model_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["tiny", "base", "small", "medium", "large"],
            variable=self.model_var,
        )
        self.model_menu.pack(side="left", padx=5)

        # Transcribe button
        self.transcribe_btn = ctk.CTkButton(
            self.main,
            text="Transcribe",
            command=self._start_transcribe,
            height=40,
            font=ctk.CTkFont(size=16),
        )
        self.transcribe_btn.pack(pady=10)

        # Progress
        self.progress = ctk.CTkProgressBar(self.main, width=500)
        self.progress.pack(pady=10)
        self.progress.set(0)

        # Status
        self.status = ctk.CTkLabel(self.main, text="Ready")
        self.status.pack(pady=5)

        # Results
        self.results = ctk.CTkTextbox(self.main, width=700, height=300)
        self.results.pack(fill="both", expand=True, pady=10)

    def _init_async(self):
        """Lazy-load services in background."""

        def init():
            self.root.after(
                0, lambda: self.status.configure(text="Loading pipeline...")
            )
            from insightron.services.pipeline import get_pipeline

            self._pipeline = get_pipeline()
            self.root.after(0, lambda: self.status.configure(text="Ready"))

        thread = threading.Thread(target=init, daemon=True)
        thread.start()

    def _browse_file(self):
        """Browse for audio file."""
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.wav *.m4a *.flac *.mp4 *.ogg *.aac")]
        )
        if path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)
            self.selected_file = path

    def _start_transcribe(self):
        """Start transcription."""
        if not self.selected_file:
            self._show_error("Please select an audio file")
            return

        if self.is_transcribing:
            return

        self.is_transcribing = True
        self.transcribe_btn.configure(state="disabled")
        self.progress.set(0)
        self.results.delete("1.0", "end")

        def run():
            try:
                self.root.after(
                    0, lambda: self.status.configure(text="Transcribing...")
                )
                self.root.after(0, lambda: self.progress.set(0.3))

                result = self._pipeline.transcribe(
                    self.selected_file,
                    progress_callback=lambda msg: self.root.after(
                        0, lambda: self.results.insert("end", f"{msg}\n")
                    ),
                )

                self.root.after(0, lambda: self.progress.set(1.0))
                self.root.after(0, lambda: self.status.configure(text="Complete"))
                self.root.after(
                    0, lambda: self.results.insert("end", f"\n{result.full_text}")
                )

            except Exception as e:
                self.root.after(0, lambda: self._show_error(str(e)))
            finally:
                self.root.after(
                    0, lambda: self.transcribe_btn.configure(state="normal")
                )
                self.is_transcribing = False

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _show_error(self, msg: str):
        """Show error message."""
        from tkinter import messagebox

        messagebox.showerror("Error", msg)
