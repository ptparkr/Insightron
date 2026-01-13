"""
Main GUI Window for Insightron.

Modern, modular GUI application using component-based architecture.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from insightron.ui.components import Header, SettingsPanel, ProgressPanel, ResultsPanel, FileSelector
from insightron.ui.themes.theme_manager import ThemeManager
from insightron.core.config import (
    APP_VERSION,
    TRANSCRIPTION_FOLDER,
    RECORDINGS_FOLDER,
    WHISPER_MODEL,
    DEFAULT_LANGUAGE
)
from insightron.core.settings_manager import SettingsManager
from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.batch.batch_processor import batch_transcribe_files
from insightron.services.realtime.realtime_transcriber import RealtimeTranscriber
from insightron.core.utils import create_realtime_note

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsightronGUI:
    """
    Modern GUI application for Insightron.
    
    Features:
    - Component-based architecture
    - Modular UI components
    - Clean separation of concerns
    - Professional appearance
    """
    
    def __init__(self, root: ctk.CTk):
        """
        Initialize the Insightron GUI application.
        
        Args:
            root: CustomTkinter root window
        """
        self.root = root
        self.root.title(f"Insightron v{APP_VERSION}")
        self.root.geometry("1000x850")
        
        # Initialize managers
        self.settings_manager = SettingsManager()
        self.theme = ThemeManager.get_theme()
        
        # Application state
        self.selected_file: Optional[str] = None
        self.selected_batch_files: list = []
        self.is_transcribing = False
        self.is_recording = False
        self.realtime_transcriber: Optional[RealtimeTranscriber] = None
        
        # Setup UI
        self._setup_ui()
        self._center_window()
        self._load_settings()
        
        logger.info("Insightron GUI initialized")
    
    def _setup_ui(self):
        """Setup the main UI components."""
        # Main container
        self.content = ctk.CTkFrame(self.root, fg_color=self.theme.background)
        self.content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_component = Header(self.content)
        header_component.get_widget().pack(fill="x", pady=(0, 20))
        
        # Tab view
        self.tab_view = ctk.CTkTabview(
            self.content,
            corner_radius=12,
            fg_color=self.theme.surface,
            segmented_button_fg_color=self.theme.surface_light,
            segmented_button_selected_color=self.theme.primary,
            segmented_button_selected_hover_color=self.theme.primary_hover,
            text_color=self.theme.text_secondary,
            segmented_button_unselected_hover_color=self.theme.border
        )
        self.tab_view.pack(fill="both", expand=True, pady=(0, 15))
        
        # Create tabs
        self.tab_single = self.tab_view.add("Single File")
        self.tab_batch = self.tab_view.add("Batch Mode")
        self.tab_realtime = self.tab_view.add("Realtime")
        
        # Configure tab colors
        for tab in [self.tab_single, self.tab_batch, self.tab_realtime]:
            tab.configure(fg_color=self.theme.background)
        
        # Setup tabs
        self._setup_single_file_tab()
        self._setup_batch_tab()
        self._setup_realtime_tab()
        
        # Settings Panel
        self.settings_panel = SettingsPanel(
            self.content,
            on_change=self._save_settings
        )
        self.settings_panel.get_widget().pack(fill="x", pady=(0, 15))
        
        # Progress Panel
        self.progress_panel = ProgressPanel(self.content)
        self.progress_panel.get_widget().pack(fill="x", pady=(0, 15))
        
        # Results Panel
        self.results_panel = ResultsPanel(self.content)
        self.results_panel.get_widget().pack(fill="both", expand=True)
    
    def _setup_single_file_tab(self):
        """Setup single file transcription tab."""
        # File selector
        self.single_file_selector = FileSelector(
            self.tab_single,
            mode="single",
            on_select=lambda files: setattr(self, 'selected_file', files[0] if files else None)
        )
        self.single_file_selector.get_widget().pack(fill="x", pady=20, padx=20)
        
        # Transcribe button
        self.transcribe_btn = ctk.CTkButton(
            self.tab_single,
            text="⚡ Start Transcription",
            command=self._start_transcription,
            font=('Segoe UI', 18, 'bold'),
            height=56,
            corner_radius=12,
            fg_color=self.theme.accent,
            hover_color=self.theme.accent_hover
        )
        self.transcribe_btn.pack(fill="x", padx=20, pady=(10, 20))
    
    def _setup_batch_tab(self):
        """Setup batch processing tab."""
        # File selector
        self.batch_file_selector = FileSelector(
            self.tab_batch,
            mode="multiple",
            on_select=lambda files: setattr(self, 'selected_batch_files', files)
        )
        self.batch_file_selector.get_widget().pack(fill="x", pady=20, padx=20)
        
        # Batch transcribe button
        self.batch_transcribe_btn = ctk.CTkButton(
            self.tab_batch,
            text="⚡ Process All Files",
            command=self._start_batch_transcription,
            font=('Segoe UI', 18, 'bold'),
            height=56,
            corner_radius=12,
            fg_color=self.theme.accent,
            hover_color=self.theme.accent_hover
        )
        self.batch_transcribe_btn.pack(fill="x", padx=20, pady=(10, 20))
    
    def _setup_realtime_tab(self):
        """Setup realtime transcription tab."""
        rt_card = ctk.CTkFrame(
            self.tab_realtime,
            corner_radius=12,
            border_width=1,
            border_color=self.theme.border,
            fg_color=self.theme.surface,
        )
        rt_card.pack(fill="x", pady=20, padx=20)
        
        inner = ctk.CTkFrame(rt_card, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=30)
        
        # Microphone selection
        ctk.CTkLabel(
            inner,
            text="Select Microphone",
            font=('Segoe UI', 14, 'bold'),
            text_color=self.theme.text_secondary
        ).pack(pady=(0, 5))
        
        self.mic_var = ctk.StringVar(value="Loading...")
        self.mic_combo = ctk.CTkComboBox(
            inner,
            variable=self.mic_var,
            values=["Loading..."],
            font=('Segoe UI', 14),
            width=300,
            height=40,
            corner_radius=8
        )
        self.mic_combo.pack(pady=(0, 20))
        
        # Refresh button
        ctk.CTkButton(
            inner,
            text="🔄 Refresh",
            command=self._refresh_microphones,
            width=80,
            height=24,
            font=('Segoe UI', 11),
            fg_color="transparent",
            border_width=1,
            border_color=self.theme.border
        ).pack(pady=(0, 20))
        
        # Audio level indicator
        ctk.CTkLabel(
            inner,
            text="Audio Level",
            font=('Segoe UI', 12, 'bold'),
            text_color=self.theme.text_secondary
        ).pack(pady=(10, 5))
        
        self.audio_level_bar = ctk.CTkProgressBar(
            inner,
            width=300,
            height=20,
            progress_color=self.theme.success
        )
        self.audio_level_bar.pack(pady=(0, 20))
        self.audio_level_bar.set(0)
        
        # Record button
        self.record_btn = ctk.CTkButton(
            self.tab_realtime,
            text="🔴 Start Recording",
            command=self._toggle_recording,
            font=('Segoe UI', 18, 'bold'),
            height=56,
            corner_radius=12,
            fg_color=self.theme.error,
            hover_color='#DC2626'
        )
        self.record_btn.pack(fill="x", padx=20, pady=(10, 20))
        
        # Initialize realtime transcriber
        self.root.after(100, self._init_realtime)
    
    def _init_realtime(self):
        """Initialize realtime transcriber."""
        try:
            self.realtime_transcriber = RealtimeTranscriber()
            self._refresh_microphones()
        except Exception as e:
            logger.error(f"Failed to init realtime: {e}")
            self.mic_var.set("Error loading devices")
    
    def _refresh_microphones(self):
        """Refresh microphone list."""
        if not self.realtime_transcriber:
            return
        devices = self.realtime_transcriber.get_microphones()
        self.mic_devices = devices
        names = [d['name'] for d in devices] or ["No microphones found"]
        self.mic_combo.configure(values=names)
        if names:
            self.mic_combo.set(names[0])
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start realtime recording."""
        try:
            name = self.mic_var.get()
            idx = -1
            for d in self.mic_devices:
                if d['name'] == name:
                    idx = d['index']
                    break
            
            self.is_recording = True
            self.record_btn.configure(text="⬛ Stop Recording", fg_color=self.theme.primary)
            self.progress_panel.update_status("🎙️ Listening...")
            self.results_panel.append(f"--- Recording Started ({name}) ---")
            
            self.realtime_transcriber.model_size = self.settings_panel.get_model()
            lang = self.settings_panel.get_language()
            self.realtime_transcriber.language = lang
            self.realtime_transcriber.start_transcription(
                idx,
                self._on_realtime_text,
                self._on_audio_level
            )
        except Exception as e:
            self._handle_error(e)
            self._stop_recording()
    
    def _stop_recording(self):
        """Stop realtime recording."""
        self.is_recording = False
        self.record_btn.configure(text="🔴 Start Recording", fg_color=self.theme.error)
        if self.realtime_transcriber:
            self.realtime_transcriber.stop_transcription()
        
        # Save recording
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            save_path = RECORDINGS_FOLDER / filename
            
            saved_file = self.realtime_transcriber.save_recording(str(save_path))
            if saved_file:
                self.results_panel.append(f"⏹ Stopped recording - Saved to {filename}")
                
                # Save transcription note
                try:
                    data = self.realtime_transcriber.get_transcription_data()
                    text_content = data['text'] or "(No speech detected or transcription failed)"
                    note_filename = f"recording_{timestamp}"
                    
                    duration_seconds = 0
                    if self.realtime_transcriber.full_audio_buffer:
                        total_samples = sum(len(chunk) for chunk in self.realtime_transcriber.full_audio_buffer)
                        duration_seconds = total_samples / self.realtime_transcriber.sample_rate
                    
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    duration_str = f"{minutes}:{seconds:02d}"
                    
                    note_content = create_realtime_note(
                        filename=note_filename,
                        text=text_content,
                        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        duration=duration_str,
                        file_size_mb=save_path.stat().st_size / (1024 * 1024) if save_path.exists() else 0,
                        model=self.realtime_transcriber.model_size,
                        language=data['language'],
                        formatting_style=self.settings_panel.get_formatting(),
                        duration_seconds=duration_seconds,
                        segments=data['segments'],
                        folder_path=str(TRANSCRIPTION_FOLDER)
                    )
                    
                    note_path = TRANSCRIPTION_FOLDER / f"{note_filename}.md"
                    note_path.write_text(note_content, encoding='utf-8')
                    self.results_panel.append(f"📝 Saved note to Notes: {note_filename}.md")
                except Exception as e:
                    logger.error(f"Failed to save note: {e}")
                    self.results_panel.append(f"❌ Failed to save note: {e}")
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")
            self.results_panel.append(f"⏹ Stopped recording - Save failed: {e}")
        
        self.progress_panel.update_status("✅ Stopped")
        self.audio_level_bar.set(0)
    
    def _on_realtime_text(self, text: str):
        """Callback for realtime text."""
        self.results_panel.append(f"🗣️ {text}")
    
    def _on_audio_level(self, level: float):
        """Update audio level indicator."""
        self.root.after(0, lambda: self._update_audio_level(level))
    
    def _update_audio_level(self, level: float):
        """Update progress bar with color coding."""
        self.audio_level_bar.set(level)
        
        if level < 0.5:
            color = self.theme.success
        elif level < 0.8:
            color = '#F59E0B'
        else:
            color = self.theme.error
        
        self.audio_level_bar.configure(progress_color=color)
    
    def _start_transcription(self):
        """Start single file transcription."""
        if not self.selected_file:
            messagebox.showerror("No File", "Please select an audio file.")
            return
        
        if self.is_transcribing:
            return
        
        self.is_transcribing = True
        self._disable_controls()
        self.progress_panel.start_indeterminate()
        
        threading.Thread(target=self._transcribe_audio, daemon=True).start()
    
    def _start_batch_transcription(self):
        """Start batch transcription."""
        if not self.selected_batch_files:
            messagebox.showerror("No Files", "Please select files or folder.")
            return
        
        if self.is_transcribing:
            return
        
        self.is_transcribing = True
        self._disable_controls()
        self.progress_panel.start_indeterminate()
        
        threading.Thread(target=self._transcribe_batch, daemon=True).start()
    
    def _transcribe_audio(self):
        """Single file transcription worker."""
        try:
            self.progress_panel.update_status("🔄 Loading model...")
            model_size = self.settings_panel.get_model()
            lang = self.settings_panel.get_language()
            
            transcriber = AudioTranscriber(model_size, lang)
            
            def callback(msg):
                self.progress_panel.update_status(f"🎙️ {msg}")
            
            output, data = transcriber.transcribe_file(
                self.selected_file,
                progress_callback=callback,
                formatting_style=self.settings_panel.get_formatting(),
                language=lang
            )
            
            self.progress_panel.update_status("✅ Transcription Complete!")
            self.results_panel.append(f"Completed: {output.name} ({data.get('duration', '?')})")
            self.root.after(0, lambda: self._show_success_dialog(output))
        except Exception as e:
            self._handle_error(e)
        finally:
            self.root.after(0, self._reset_ui)
    
    def _transcribe_batch(self):
        """Batch transcription worker."""
        try:
            from insightron.services.batch.batch_processor import batch_transcribe_files
            
            self.progress_panel.update_status("🔄 Starting batch...")
            model_size = self.settings_panel.get_model()
            lang = self.settings_panel.get_language()
            
            transcriber = AudioTranscriber(model_size, lang)
            
            def callback(completed, total, filename):
                self.progress_panel.update_status(f"📦 [{completed}/{total}] {filename}")
                self.results_panel.append(f"Processed: {filename}")
            
            results = batch_transcribe_files(
                self.selected_batch_files,
                model_size=model_size,
                language=lang,
                progress_callback=callback,
                transcriber=transcriber
            )
            
            self.progress_panel.update_status("✅ Batch Complete!")
            summary = f"Batch Results: {results['completed']} OK, {results['failed_count']} Failed"
            self.results_panel.append(summary)
        except Exception as e:
            self._handle_error(e)
        finally:
            self.root.after(0, self._reset_ui)
    
    def _handle_error(self, e: Exception):
        """Handle errors."""
        logger.error(f"Error: {e}")
        self.progress_panel.update_status("❌ Error")
        self.results_panel.append(f"ERROR: {str(e)}")
        messagebox.showerror("Error", str(e))
    
    def _reset_ui(self):
        """Reset UI after transcription."""
        self.progress_panel.stop_indeterminate()
        self._enable_controls()
        self.is_transcribing = False
    
    def _disable_controls(self):
        """Disable UI controls during transcription."""
        for btn in [self.transcribe_btn, self.batch_transcribe_btn]:
            btn.configure(state="disabled")
    
    def _enable_controls(self):
        """Enable UI controls."""
        for btn in [self.transcribe_btn, self.batch_transcribe_btn]:
            btn.configure(state="normal")
    
    def _show_success_dialog(self, output_path: Path):
        """Show success dialog."""
        if messagebox.askyesno("Success!", "Open output folder?"):
            try:
                os.startfile(str(output_path.parent))
            except:
                pass
    
    def _center_window(self):
        """Center window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
    
    def _load_settings(self):
        """Load saved settings."""
        try:
            self.settings_panel.set_model(self.settings_manager.get("model", WHISPER_MODEL))
            self.settings_panel.set_language(self.settings_manager.get("language", DEFAULT_LANGUAGE))
            self.settings_panel.set_formatting(self.settings_manager.get("formatting", "auto"))
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def _save_settings(self):
        """Save current settings."""
        self.settings_manager.set("model", self.settings_panel.get_model())
        self.settings_manager.set("language", self.settings_panel.get_language())
        self.settings_manager.set("formatting", self.settings_panel.get_formatting())
